// 🗄️ 관리자 데이터 캐싱 시스템
// 사용자, 사업장, 협력업체 등 자주 사용되는 데이터를 로컬에 캐시

class AdminCacheManager {
    constructor() {
        this.cachePrefix = 'daham_admin_';
        this.cacheTimeout = 5 * 60 * 1000; // 5분

        if (typeof CONFIG === 'undefined' || !CONFIG.API || !CONFIG.API.BASE_URL) {
            throw new Error('[AdminCache] CONFIG 객체가 올바르게 로드되지 않았거나 API BASE_URL이 없습니다.');
        }
        this.apiBase = CONFIG.API.BASE_URL;
        
        // 캐시할 데이터 타입들
        this.cacheTypes = {
            USERS: 'users',
            SUPPLIERS: 'suppliers', 
            BUSINESS_LOCATIONS: 'business_locations',
            INGREDIENTS_SUMMARY: 'ingredients_summary'
        };
        
        console.log('[AdminCache] 캐시 매니저 초기화 완료');
    }

    /**
     * 캐시 키 생성
     */
    getCacheKey(type) {
        return `${this.cachePrefix}${type}`;
    }

    /**
     * 캐시 만료 키 생성  
     */
    getExpiryKey(type) {
        return `${this.cachePrefix}${type}_expiry`;
    }

    /**
     * 캐시된 데이터가 유효한지 확인
     */
    isCacheValid(type) {
        const expiryTime = localStorage.getItem(this.getExpiryKey(type));
        if (!expiryTime) return false;
        
        return Date.now() < parseInt(expiryTime);
    }

    /**
     * 데이터를 캐시에 저장
     */
    setCache(type, data) {
        try {
            const cacheKey = this.getCacheKey(type);
            const expiryKey = this.getExpiryKey(type);
            
            localStorage.setItem(cacheKey, JSON.stringify({
                data: data,
                timestamp: Date.now(),
                type: type
            }));
            
            localStorage.setItem(expiryKey, (Date.now() + this.cacheTimeout).toString());
            
            console.log(`[AdminCache] ${type} 데이터 캐시 저장 완료:`, data.length || 'N/A', '개');
        } catch (error) {
            console.error(`[AdminCache] ${type} 캐시 저장 실패:`, error);
        }
    }

    /**
     * 캐시에서 데이터 조회
     */
    getCache(type) {
        try {
            if (!this.isCacheValid(type)) {
                console.log(`[AdminCache] ${type} 캐시 만료 또는 없음`);
                return null;
            }
            
            const cacheKey = this.getCacheKey(type);
            const cached = localStorage.getItem(cacheKey);
            
            if (!cached) return null;
            
            const parsed = JSON.parse(cached);
            console.log(`[AdminCache] ${type} 캐시에서 조회:`, parsed.data.length || 'N/A', '개');
            return parsed.data;
        } catch (error) {
            console.error(`[AdminCache] ${type} 캐시 조회 실패:`, error);
            return null;
        }
    }

    /**
     * 특정 타입 캐시 삭제
     */
    clearCache(type) {
        localStorage.removeItem(this.getCacheKey(type));
        localStorage.removeItem(this.getExpiryKey(type));
        console.log(`[AdminCache] ${type} 캐시 삭제 완료`);
    }

    /**
     * 모든 캐시 삭제
     */
    clearAllCache() {
        Object.values(this.cacheTypes).forEach(type => {
            this.clearCache(type);
        });
        console.log('[AdminCache] 모든 캐시 삭제 완료');
    }

    /**
     * 사용자 목록 조회 (캐시 우선)
     */
    async getUsers(forceRefresh = false) {
        const cacheType = this.cacheTypes.USERS;
        
        // 강제 새로고침이 아니고 캐시가 유효하면 캐시 사용
        if (!forceRefresh) {
            const cached = this.getCache(cacheType);
            if (cached) return cached;
        }
        
        try {
            console.log('[AdminCache] 사용자 목록 API 호출 중...');
            const response = await fetch(`${this.apiBase}/api/admin/users`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            const users = result.users || result.data || [];
            
            // 캐시에 저장
            this.setCache(cacheType, users);
            
            return users;
        } catch (error) {
            console.error('[AdminCache] 사용자 목록 로드 실패:', error);
            
            // API 실패 시 만료된 캐시라도 사용
            const fallbackCache = localStorage.getItem(this.getCacheKey(cacheType));
            if (fallbackCache) {
                console.log('[AdminCache] 만료된 사용자 캐시를 fallback으로 사용');
                return JSON.parse(fallbackCache).data;
            }
            
            return [];
        }
    }

    /**
     * 사업장 목록 조회 (캐시 우선)
     */
    async getBusinessLocations(forceRefresh = false) {
        const cacheType = this.cacheTypes.BUSINESS_LOCATIONS;
        
        if (!forceRefresh) {
            const cached = this.getCache(cacheType);
            if (cached) return cached;
        }
        
        try {
            console.log('[AdminCache] 사업장 목록 API 호출 중...');
            const response = await fetch(`${this.apiBase}/api/admin/business-locations`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            const locations = result.locations || result.data || [];
            
            this.setCache(cacheType, locations);
            return locations;
        } catch (error) {
            console.error('[AdminCache] 사업장 목록 로드 실패:', error);
            
            const fallbackCache = localStorage.getItem(this.getCacheKey(cacheType));
            if (fallbackCache) {
                console.log('[AdminCache] 만료된 사업장 캐시를 fallback으로 사용');
                return JSON.parse(fallbackCache).data;
            }
            
            return [];
        }
    }

    /**
     * 협력업체 목록 조회 (캐시 우선)
     */
    async getSuppliers(forceRefresh = false) {
        const cacheType = this.cacheTypes.SUPPLIERS;
        
        if (!forceRefresh) {
            const cached = this.getCache(cacheType);
            if (cached) return cached;
        }
        
        try {
            console.log('[AdminCache] 협력업체 목록 API 호출 중...');
            const response = await fetch(`${this.apiBase}/api/admin/suppliers`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            const suppliers = result.suppliers || result.data || [];
            
            this.setCache(cacheType, suppliers);
            return suppliers;
        } catch (error) {
            console.error('[AdminCache] 협력업체 목록 로드 실패:', error);
            
            const fallbackCache = localStorage.getItem(this.getCacheKey(cacheType));
            if (fallbackCache) {
                console.log('[AdminCache] 만료된 협력업체 캐시를 fallback으로 사용');
                return JSON.parse(fallbackCache).data;
            }
            
            return [];
        }
    }

    /**
     * 식자재 요약 통계 조회 (캐시 우선)
     */
    async getIngredientsSummary(forceRefresh = false) {
        const cacheType = this.cacheTypes.INGREDIENTS_SUMMARY;
        
        if (!forceRefresh) {
            const cached = this.getCache(cacheType);
            if (cached) return cached;
        }
        
        try {
            console.log('[AdminCache] 식자재 요약 API 호출 중...');
            const response = await fetch(`${this.apiBase}/api/admin/ingredients-summary`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            const summary = result.summary || result.data || {};
            
            this.setCache(cacheType, summary);
            return summary;
        } catch (error) {
            console.error('[AdminCache] 식자재 요약 로드 실패:', error);
            
            const fallbackCache = localStorage.getItem(this.getCacheKey(cacheType));
            if (fallbackCache) {
                console.log('[AdminCache] 만료된 식자재 요약 캐시를 fallback으로 사용');
                return JSON.parse(fallbackCache).data;
            }
            
            return {};
        }
    }

    /**
     * 캐시 상태 조회
     */
    getCacheStatus() {
        const status = {};
        
        Object.values(this.cacheTypes).forEach(type => {
            const cached = this.getCache(type);
            const expiryTime = localStorage.getItem(this.getExpiryKey(type));
            
            status[type] = {
                exists: !!cached,
                valid: this.isCacheValid(type),
                dataCount: cached ? (Array.isArray(cached) ? cached.length : 'N/A') : 0,
                expiresAt: expiryTime ? new Date(parseInt(expiryTime)).toLocaleString() : 'N/A'
            };
        });
        
        return status;
    }

    /**
     * 데이터 생성/수정/삭제 시 관련 캐시 무효화
     */
    invalidateRelatedCache(dataType, action = 'unknown') {
        console.log(`[AdminCache] ${dataType} ${action} - 관련 캐시 무효화`);
        
        switch (dataType) {
            case 'user':
                this.clearCache(this.cacheTypes.USERS);
                break;
            case 'supplier': 
                this.clearCache(this.cacheTypes.SUPPLIERS);
                this.clearCache(this.cacheTypes.INGREDIENTS_SUMMARY);
                break;
            case 'business_location':
                this.clearCache(this.cacheTypes.BUSINESS_LOCATIONS);
                break;
            case 'ingredient':
                this.clearCache(this.cacheTypes.INGREDIENTS_SUMMARY);
                break;
        }
    }

    /**
     * 백그라운드에서 캐시 새로고침
     */
    async refreshAllCaches() {
        console.log('[AdminCache] 백그라운드 캐시 새로고침 시작');
        
        try {
            await Promise.all([
                this.getUsers(true),
                this.getBusinessLocations(true), 
                this.getSuppliers(true),
                this.getIngredientsSummary(true)
            ]);
            
            console.log('[AdminCache] 백그라운드 캐시 새로고침 완료');
        } catch (error) {
            console.error('[AdminCache] 백그라운드 캐시 새로고침 실패:', error);
        }
    }
}

// 전역에서 사용 가능하도록 설정
if (typeof window !== 'undefined') {
    window.AdminCache = new AdminCacheManager();
    
    // 페이지 로드 시 백그라운드 캐시 새로고침 (5초 후)
    setTimeout(() => {
        window.AdminCache.refreshAllCaches();
    }, 5000);
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdminCacheManager;
}