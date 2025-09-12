/**
 * AI-Resistant API Gateway
 * 모든 API 호출을 중앙에서 관리하고 보호하는 시스템
 */

class APIGateway {
    constructor() {
        this.endpoints = new Map();
        this.middleware = [];
        this.rateLimiter = new Map();
        this.cache = new Map();
        this.initialized = false;
    }

    /**
     * API 엔드포인트 등록
     */
    registerEndpoint(path, handler, options = {}) {
        const config = {
            handler,
            method: options.method || 'GET',
            middleware: options.middleware || [],
            rateLimit: options.rateLimit || null,
            cache: options.cache || false,
            cacheTTL: options.cacheTTL || 300000, // 5분
            protected: options.protected || false
        };

        this.endpoints.set(`${config.method}:${path}`, config);
        console.log(`🔌 API endpoint registered: ${config.method} ${path}`);
    }

    /**
     * 전역 미들웨어 등록
     */
    use(middleware) {
        if (typeof middleware !== 'function') {
            throw new Error('❌ Middleware must be a function');
        }
        this.middleware.push(middleware);
        console.log('🔧 Global middleware registered');
    }

    /**
     * API 요청 처리
     */
    async request(path, options = {}) {
        const method = (options.method || 'GET').toUpperCase();
        const key = `${method}:${path}`;
        const endpoint = this.endpoints.get(key);

        if (!endpoint) {
            throw new Error(`❌ API endpoint not found: ${method} ${path}`);
        }

        try {
            // Rate limiting 검사
            if (!this.checkRateLimit(key, endpoint.rateLimit)) {
                throw new Error('⚠️ Rate limit exceeded');
            }

            // 캐시 확인
            if (endpoint.cache && method === 'GET') {
                const cached = this.getFromCache(key);
                if (cached) {
                    console.log(`📋 Cache hit: ${key}`);
                    return cached;
                }
            }

            // 요청 컨텍스트 생성
            const context = {
                path,
                method,
                options,
                timestamp: Date.now(),
                user: options.user || null
            };

            // 전역 미들웨어 실행
            for (const middleware of this.middleware) {
                await middleware(context);
            }

            // 엔드포인트별 미들웨어 실행
            for (const middleware of endpoint.middleware) {
                await middleware(context);
            }

            // 핸들러 실행
            console.log(`🌐 Processing API request: ${method} ${path}`);
            const result = await endpoint.handler(context);

            // 캐시 저장
            if (endpoint.cache && method === 'GET') {
                this.setCache(key, result, endpoint.cacheTTL);
            }

            return result;

        } catch (error) {
            console.error(`💥 API request failed: ${method} ${path}`, error);
            throw error;
        }
    }

    /**
     * Rate limiting 검사
     */
    checkRateLimit(key, limit) {
        if (!limit) return true;

        const now = Date.now();
        const windowStart = now - (limit.window || 60000); // 기본 1분 윈도우
        
        if (!this.rateLimiter.has(key)) {
            this.rateLimiter.set(key, []);
        }

        const requests = this.rateLimiter.get(key);
        
        // 오래된 요청 제거
        const filtered = requests.filter(timestamp => timestamp > windowStart);
        
        if (filtered.length >= (limit.max || 100)) {
            return false;
        }

        filtered.push(now);
        this.rateLimiter.set(key, filtered);
        return true;
    }

    /**
     * 캐시 조회
     */
    getFromCache(key) {
        const cached = this.cache.get(key);
        if (!cached) return null;

        if (Date.now() > cached.expires) {
            this.cache.delete(key);
            return null;
        }

        return cached.data;
    }

    /**
     * 캐시 저장
     */
    setCache(key, data, ttl) {
        this.cache.set(key, {
            data,
            expires: Date.now() + ttl
        });
    }

    /**
     * 표준 HTTP 요청을 API Gateway를 통해 라우팅
     */
    async fetch(url, options = {}) {
        try {
            // URL에서 경로 추출
            const urlObj = new URL(url, window.location.origin);
            const path = urlObj.pathname;

            // API Gateway를 통한 요청
            return await this.request(path, {
                method: options.method || 'GET',
                headers: options.headers || {},
                body: options.body || null,
                user: options.user || null
            });

        } catch (error) {
            // Gateway에서 처리할 수 없는 경우 원본 fetch 사용
            console.log(`🌍 Falling back to native fetch for: ${url}`);
            return await window._originalFetch(url, options);
        }
    }

    /**
     * 초기화
     */
    initialize() {
        if (this.initialized) return;

        // 네이티브 fetch 백업
        window._originalFetch = window._originalFetch || window.fetch;
        
        // fetch 오버라이드 (선택적)
        if (window.FORTRESS_INTERCEPT_FETCH) {
            window.fetch = this.fetch.bind(this);
        }

        // 기본 미들웨어 등록
        this.use(async (context) => {
            console.log(`📊 API Request: ${context.method} ${context.path}`);
        });

        // 오류 처리 미들웨어
        this.use(async (context) => {
            if (!context.options.headers) {
                context.options.headers = {};
            }
            context.options.headers['X-Fortress-Request-ID'] = 
                Math.random().toString(36).substring(7);
        });

        this.initialized = true;
        console.log('🚪 API Gateway initialized');
    }

    /**
     * 통계 정보
     */
    getStats() {
        return {
            endpoints: Array.from(this.endpoints.keys()),
            cacheSize: this.cache.size,
            rateLimitEntries: this.rateLimiter.size,
            middleware: this.middleware.length
        };
    }

    /**
     * 캐시 클리어
     */
    clearCache() {
        this.cache.clear();
        console.log('🧹 API cache cleared');
    }
}

// 전역 인스턴스
window.APIGateway = window.APIGateway || new APIGateway();

// API 편의 함수들
window.api = {
    get: (path, options) => window.APIGateway.request(path, { ...options, method: 'GET' }),
    post: (path, data, options) => window.APIGateway.request(path, { 
        ...options, 
        method: 'POST', 
        body: JSON.stringify(data),
        headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) }
    }),
    put: (path, data, options) => window.APIGateway.request(path, { 
        ...options, 
        method: 'PUT', 
        body: JSON.stringify(data),
        headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) }
    }),
    delete: (path, options) => window.APIGateway.request(path, { ...options, method: 'DELETE' })
};

console.log('🚪 API Gateway loaded');