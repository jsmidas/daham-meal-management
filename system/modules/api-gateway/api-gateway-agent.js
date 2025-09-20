/**
 * 🌐 API Gateway Agent
 * 모든 고객 API 통합 관리, 인증 및 권한 통합, 로드 밸런싱
 */

define('api-gateway-agent', ['navigation'], (deps) => {

    return {
        name: 'api-gateway-agent',
        version: '1.0.0',
        protected: true,

        // 내부 상태
        state: {
            isGatewayActive: false,
            registeredServices: new Map(),
            routingRules: new Map(),
            authTokens: new Map(),
            requestQueue: [],
            responseCache: new Map(),
            loadBalancer: {
                activeServers: [],
                roundRobinIndex: 0,
                healthChecks: new Map()
            },
            statistics: {
                totalRequests: 0,
                successfulRequests: 0,
                failedRequests: 0,
                averageResponseTime: 0,
                requestsPerMinute: 0
            },
            middleware: [],
            rateLimiter: new Map()
        },

        // 설정
        config: {
            gateway: {
                enabled: true,
                port: 8080,
                baseUrl: 'http://127.0.0.1:8080',
                timeout: 30000,
                retries: 3
            },
            loadBalancing: {
                strategy: 'round-robin', // round-robin, least-connections, weighted
                healthCheckInterval: 30000,
                failureThreshold: 3
            },
            caching: {
                enabled: true,
                defaultTTL: 5 * 60 * 1000, // 5분
                maxSize: 100
            },
            rateLimit: {
                enabled: true,
                windowMs: 60000, // 1분
                maxRequests: 100,
                skipSuccessfulRequests: false
            },
            auth: {
                tokenExpiry: 24 * 60 * 60 * 1000, // 24시간
                refreshThreshold: 2 * 60 * 60 * 1000 // 2시간
            },
            cors: {
                enabled: true,
                origins: ['*'],
                methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
                headers: ['Content-Type', 'Authorization', 'X-Requested-With']
            }
        },

        // 초기화
        async init() {
            console.log('🌐 API Gateway Agent initializing...');

            try {
                this.setupDefaultServices();
                this.setupRoutingRules();
                this.setupMiddleware();
                this.setupLoadBalancer();
                this.startGateway();

                console.log('✅ API Gateway Agent initialized successfully');

                // 관리 인터페이스 등록
                if (window.Fortress) {
                    window.Fortress.registerInterface('api-gateway', this.getPublicInterface());
                }

                return this;
            } catch (error) {
                console.error('❌ Failed to initialize API Gateway Agent:', error);
                throw error;
            }
        },

        // 공개 인터페이스
        getPublicInterface() {
            return {
                // 게이트웨이 제어
                startGateway: () => this.startGateway(),
                stopGateway: () => this.stopGateway(),
                isActive: () => this.state.isGatewayActive,

                // 서비스 등록
                registerService: (name, config) => this.registerService(name, config),
                unregisterService: (name) => this.unregisterService(name),
                getServices: () => this.getServicesInfo(),

                // 라우팅
                addRoute: (pattern, target) => this.addRoute(pattern, target),
                removeRoute: (pattern) => this.removeRoute(pattern),
                getRoutes: () => this.getRoutesInfo(),

                // 요청 처리
                proxyRequest: (request) => this.proxyRequest(request),

                // 인증 관리
                authenticate: (credentials) => this.authenticate(credentials),
                refreshToken: (token) => this.refreshToken(token),
                validateToken: (token) => this.validateToken(token),
                revokeToken: (token) => this.revokeToken(token),

                // 모니터링
                getStatistics: () => ({ ...this.state.statistics }),
                getLoadBalancerStatus: () => this.getLoadBalancerStatus(),
                getHealthStatus: () => this.getHealthStatus(),

                // 설정
                updateConfig: (newConfig) => this.updateConfig(newConfig),
                getConfig: () => ({ ...this.config })
            };
        },

        // 기본 서비스 설정
        setupDefaultServices() {
            // 메인 API 서버
            this.registerService('main-api', {
                name: 'Main API Server',
                servers: [
                    { url: 'http://127.0.0.1:8010', weight: 1, healthy: true }
                ],
                paths: ['/api/*'],
                auth: { required: true, roles: ['admin', 'user'] },
                rateLimit: { maxRequests: 100, windowMs: 60000 }
            });

            // 통합 컨트롤 타워
            this.registerService('control-tower', {
                name: 'Control Tower',
                servers: [
                    { url: 'http://127.0.0.1:8080', weight: 1, healthy: true }
                ],
                paths: ['/control/*', '/admin/*'],
                auth: { required: true, roles: ['admin'] },
                rateLimit: { maxRequests: 50, windowMs: 60000 }
            });

            // 정적 파일 서빙
            this.registerService('static-files', {
                name: 'Static Files',
                servers: [
                    { url: 'http://127.0.0.1:8080', weight: 1, healthy: true }
                ],
                paths: ['/static/*', '/css/*', '/js/*'],
                auth: { required: false },
                cache: { enabled: true, ttl: 10 * 60 * 1000 } // 10분
            });

            console.log('📋 Default services registered');
        },

        // 라우팅 규칙 설정
        setupRoutingRules() {
            // API 요청 라우팅
            this.addRoute('/api/**', {
                service: 'main-api',
                rewrite: (path) => path,
                middleware: ['auth', 'rateLimit', 'logging']
            });

            // 관리자 페이지 라우팅
            this.addRoute('/admin/**', {
                service: 'control-tower',
                rewrite: (path) => path,
                middleware: ['auth', 'adminOnly', 'logging']
            });

            // 정적 파일 라우팅
            this.addRoute('/static/**', {
                service: 'static-files',
                rewrite: (path) => path,
                middleware: ['cache', 'compress']
            });

            console.log('🛣️ Routing rules configured');
        },

        // 미들웨어 설정
        setupMiddleware() {
            // 인증 미들웨어
            this.addMiddleware('auth', async (request, response, next) => {
                const authHeader = request.headers['Authorization'] || request.headers['authorization'];

                if (!authHeader) {
                    return this.sendError(response, 401, 'Authentication required');
                }

                const token = authHeader.replace('Bearer ', '');
                const validation = await this.validateToken(token);

                if (!validation.valid) {
                    return this.sendError(response, 401, 'Invalid or expired token');
                }

                request.user = validation.user;
                next();
            });

            // 관리자 권한 미들웨어
            this.addMiddleware('adminOnly', async (request, response, next) => {
                if (!request.user || !request.user.roles.includes('admin')) {
                    return this.sendError(response, 403, 'Admin access required');
                }
                next();
            });

            // 속도 제한 미들웨어
            this.addMiddleware('rateLimit', async (request, response, next) => {
                const clientId = this.getClientId(request);
                const limit = this.checkRateLimit(clientId);

                if (!limit.allowed) {
                    return this.sendError(response, 429, 'Too many requests', {
                        'X-RateLimit-Limit': limit.max,
                        'X-RateLimit-Remaining': limit.remaining,
                        'X-RateLimit-Reset': limit.reset
                    });
                }

                next();
            });

            // 로깅 미들웨어
            this.addMiddleware('logging', async (request, response, next) => {
                const startTime = Date.now();

                const originalSend = response.send;
                response.send = function(data) {
                    const endTime = Date.now();
                    const duration = endTime - startTime;

                    // 요청 로그 기록
                    console.log(`[Gateway] ${request.method} ${request.url} - ${response.statusCode} (${duration}ms)`);

                    return originalSend.call(this, data);
                };

                next();
            });

            // 캐시 미들웨어
            this.addMiddleware('cache', async (request, response, next) => {
                if (request.method !== 'GET') {
                    return next();
                }

                const cacheKey = this.generateCacheKey(request);
                const cached = this.state.responseCache.get(cacheKey);

                if (cached && Date.now() < cached.expiry) {
                    response.setHeader('X-Cache', 'HIT');
                    return response.send(cached.data);
                }

                const originalSend = response.send;
                response.send = function(data) {
                    // 성공적인 응답만 캐시
                    if (response.statusCode === 200) {
                        this.cacheResponse(cacheKey, data);
                    }
                    return originalSend.call(this, data);
                }.bind(this);

                next();
            });

            console.log('🔧 Middleware configured');
        },

        // 로드 밸런서 설정
        setupLoadBalancer() {
            // 서버 헬스체크 시작
            setInterval(() => {
                this.performHealthChecks();
            }, this.config.loadBalancing.healthCheckInterval);

            // 초기 헬스체크
            this.performHealthChecks();

            console.log('⚖️ Load balancer configured');
        },

        // 게이트웨이 시작
        startGateway() {
            if (this.state.isGatewayActive) return;

            this.state.isGatewayActive = true;

            // 원본 fetch 함수 인터셉트
            this.interceptFetch();

            this.log('🟢 API Gateway started');
        },

        // 게이트웨이 정지
        stopGateway() {
            if (!this.state.isGatewayActive) return;

            this.state.isGatewayActive = false;
            this.log('🔴 API Gateway stopped');
        },

        // Fetch 인터셉트
        interceptFetch() {
            const originalFetch = window.fetch;
            const self = this;

            window.fetch = async function(url, options = {}) {
                // 게이트웨이가 비활성 상태면 원본 fetch 사용
                if (!self.state.isGatewayActive) {
                    return originalFetch.call(this, url, options);
                }

                // URL이 문자열이 아니면 원본 fetch 사용
                if (typeof url !== 'string') {
                    return originalFetch.call(this, url, options);
                }

                // 외부 URL이면 원본 fetch 사용
                if (url.startsWith('http') && !url.includes('127.0.0.1') && !url.includes('localhost')) {
                    return originalFetch.call(this, url, options);
                }

                try {
                    // 게이트웨이를 통해 요청 처리
                    return await self.proxyRequest({
                        url,
                        method: options.method || 'GET',
                        headers: options.headers || {},
                        body: options.body,
                        credentials: options.credentials
                    });
                } catch (error) {
                    console.warn('🔄 Gateway failed, falling back to direct fetch:', error);
                    return originalFetch.call(this, url, options);
                }
            };
        },

        // 요청 프록시
        async proxyRequest(request) {
            try {
                this.state.statistics.totalRequests++;
                const startTime = Date.now();

                // 라우팅 규칙 찾기
                const route = this.findRoute(request.url);
                if (!route) {
                    throw new Error(`No route found for ${request.url}`);
                }

                // 서비스 정보 가져오기
                const service = this.state.registeredServices.get(route.service);
                if (!service) {
                    throw new Error(`Service ${route.service} not found`);
                }

                // 미들웨어 실행
                const response = await this.executeMiddleware(route.middleware, request, service);
                if (response) {
                    return response; // 미들웨어에서 응답을 반환한 경우
                }

                // 로드 밸런싱으로 서버 선택
                const targetServer = this.selectServer(service);
                if (!targetServer) {
                    throw new Error(`No healthy servers available for ${route.service}`);
                }

                // URL 재작성
                const targetUrl = this.rewriteUrl(request.url, route.rewrite, targetServer.url);

                // 실제 요청 수행
                const proxyResponse = await fetch(targetUrl, {
                    method: request.method,
                    headers: this.processHeaders(request.headers, service),
                    body: request.body,
                    credentials: request.credentials
                });

                const endTime = Date.now();
                const duration = endTime - startTime;

                // 통계 업데이트
                this.updateStatistics(proxyResponse.ok, duration);

                // 응답 처리
                return this.processResponse(proxyResponse, service);

            } catch (error) {
                this.state.statistics.failedRequests++;
                this.log(`❌ Proxy request failed: ${error.message}`, 'error');
                throw error;
            }
        },

        // 라우트 찾기
        findRoute(url) {
            for (const [pattern, route] of this.state.routingRules) {
                if (this.matchPattern(url, pattern)) {
                    return route;
                }
            }
            return null;
        },

        // 패턴 매칭
        matchPattern(url, pattern) {
            // 와일드카드 패턴 지원
            const regex = new RegExp(
                pattern.replace(/\*\*/g, '.*').replace(/\*/g, '[^/]*')
            );
            return regex.test(url);
        },

        // 서버 선택 (로드 밸런싱)
        selectServer(service) {
            const healthyServers = service.servers.filter(server => server.healthy);

            if (healthyServers.length === 0) {
                return null;
            }

            switch (this.config.loadBalancing.strategy) {
                case 'round-robin':
                    return this.roundRobinSelect(healthyServers);
                case 'least-connections':
                    return this.leastConnectionsSelect(healthyServers);
                case 'weighted':
                    return this.weightedSelect(healthyServers);
                default:
                    return healthyServers[0];
            }
        },

        // 라운드 로빈 선택
        roundRobinSelect(servers) {
            const server = servers[this.state.loadBalancer.roundRobinIndex % servers.length];
            this.state.loadBalancer.roundRobinIndex++;
            return server;
        },

        // 인증 처리
        async authenticate(credentials) {
            try {
                // 실제 인증 로직 (API 서버에 요청)
                const response = await fetch('http://127.0.0.1:8010/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(credentials)
                });

                if (!response.ok) {
                    throw new Error('Authentication failed');
                }

                const authData = await response.json();

                // 토큰 생성 및 저장
                const token = this.generateToken(authData.user);
                this.state.authTokens.set(token, {
                    user: authData.user,
                    created: Date.now(),
                    expires: Date.now() + this.config.auth.tokenExpiry
                });

                return { token, user: authData.user };

            } catch (error) {
                this.log(`❌ Authentication failed: ${error.message}`, 'error');
                throw error;
            }
        },

        // 토큰 검증
        async validateToken(token) {
            const tokenData = this.state.authTokens.get(token);

            if (!tokenData) {
                return { valid: false, error: 'Token not found' };
            }

            if (Date.now() > tokenData.expires) {
                this.state.authTokens.delete(token);
                return { valid: false, error: 'Token expired' };
            }

            return { valid: true, user: tokenData.user };
        },

        // 속도 제한 확인
        checkRateLimit(clientId) {
            const now = Date.now();
            const windowMs = this.config.rateLimit.windowMs;
            const maxRequests = this.config.rateLimit.maxRequests;

            if (!this.state.rateLimiter.has(clientId)) {
                this.state.rateLimiter.set(clientId, {
                    requests: [],
                    lastReset: now
                });
            }

            const client = this.state.rateLimiter.get(clientId);

            // 윈도우 초과 요청 정리
            client.requests = client.requests.filter(timestamp => now - timestamp < windowMs);

            if (client.requests.length >= maxRequests) {
                return {
                    allowed: false,
                    max: maxRequests,
                    remaining: 0,
                    reset: client.requests[0] + windowMs
                };
            }

            client.requests.push(now);

            return {
                allowed: true,
                max: maxRequests,
                remaining: maxRequests - client.requests.length,
                reset: now + windowMs
            };
        },

        // 헬스체크 수행
        async performHealthChecks() {
            for (const [serviceName, service] of this.state.registeredServices) {
                for (const server of service.servers) {
                    try {
                        const response = await fetch(`${server.url}/health`, {
                            method: 'HEAD',
                            timeout: 5000
                        });

                        const wasHealthy = server.healthy;
                        server.healthy = response.ok;

                        if (!wasHealthy && server.healthy) {
                            this.log(`✅ Server ${server.url} is now healthy`);
                        } else if (wasHealthy && !server.healthy) {
                            this.log(`❌ Server ${server.url} is now unhealthy`);
                        }

                    } catch (error) {
                        const wasHealthy = server.healthy;
                        server.healthy = false;

                        if (wasHealthy) {
                            this.log(`❌ Server ${server.url} health check failed: ${error.message}`);
                        }
                    }
                }
            }
        },

        // 서비스 등록
        registerService(name, config) {
            this.state.registeredServices.set(name, {
                name: config.name || name,
                servers: config.servers || [],
                paths: config.paths || [],
                auth: config.auth || { required: false },
                rateLimit: config.rateLimit,
                cache: config.cache,
                ...config
            });

            this.log(`📝 Service registered: ${name}`);
        },

        // 라우트 추가
        addRoute(pattern, target) {
            this.state.routingRules.set(pattern, target);
            this.log(`🛣️ Route added: ${pattern} -> ${target.service}`);
        },

        // 미들웨어 추가
        addMiddleware(name, handler) {
            this.state.middleware.push({ name, handler });
        },

        // 통계 업데이트
        updateStatistics(success, duration) {
            if (success) {
                this.state.statistics.successfulRequests++;
            } else {
                this.state.statistics.failedRequests++;
            }

            // 평균 응답 시간 계산
            const total = this.state.statistics.totalRequests;
            const current = this.state.statistics.averageResponseTime;
            this.state.statistics.averageResponseTime =
                (current * (total - 1) + duration) / total;
        },

        // 토큰 생성
        generateToken(user) {
            const payload = {
                userId: user.id,
                username: user.username,
                roles: user.roles || [],
                timestamp: Date.now()
            };

            // 간단한 토큰 생성 (실제로는 JWT 사용 권장)
            return btoa(JSON.stringify(payload)) + '.' + Date.now();
        },

        // 클라이언트 ID 추출
        getClientId(request) {
            return request.headers['x-forwarded-for'] ||
                   request.headers['x-real-ip'] ||
                   'unknown';
        },

        // 로깅
        log(message, level = 'info') {
            const logEntry = {
                timestamp: new Date().toISOString(),
                level,
                message,
                agent: 'api-gateway'
            };

            console.log(`[API Gateway] ${message}`);

            // 모니터링 에이전트에 로그 전송
            const monitoring = window.require?.('monitoring-agent');
            if (monitoring && level === 'error') {
                monitoring.logError({
                    type: 'api-gateway',
                    message,
                    timestamp: logEntry.timestamp
                });
            }
        },

        // 정리
        destroy() {
            this.stopGateway();
            this.log('🗑️ API Gateway Agent destroyed');
        },

        // 헬스 상태 반환
        getHealthStatus() {
            const totalServers = Array.from(this.state.registeredServices.values())
                .reduce((sum, service) => sum + service.servers.length, 0);

            const healthyServers = Array.from(this.state.registeredServices.values())
                .reduce((sum, service) =>
                    sum + service.servers.filter(s => s.healthy).length, 0);

            return {
                status: healthyServers === totalServers ? 'healthy' : 'degraded',
                totalServers,
                healthyServers,
                statistics: this.state.statistics
            };
        }
    };
});

console.log('🌐 API Gateway Agent module loaded');