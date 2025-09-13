/**
 * 🚀 Admin Dashboard 초기화 모듈
 * 페이지 초기화 및 ModuleLoader 연동을 담당합니다.
 */

class AdminInitializer {
    constructor() {
        this.moduleLoader = null;
        this.isInitialized = false;
    }

    /**
     * 페이지 초기화 메인 함수
     */
    async initialize() {
        console.log('🚀 [AdminInit] 초기화 시작');

        try {
            // Phase 1: ModuleLoader 초기화
            await this.initializeModuleLoader();

            // Phase 2: 핵심 모듈 로드
            await this.loadCoreModules();

            // Phase 3: 기본 UI 설정
            this.setupBasicUI();

            // Phase 4: 네비게이션 초기화
            await this.initializeNavigation();

            // Phase 5: 대시보드 초기화
            await this.initializeDashboard();

            this.isInitialized = true;
            console.log('✅ [AdminInit] 초기화 완료');

        } catch (error) {
            console.error('❌ [AdminInit] 초기화 실패:', error);
            this.showInitializationError(error);
        }
    }

    /**
     * ModuleLoader 초기화
     */
    async initializeModuleLoader() {
        console.log('📦 [AdminInit] ModuleLoader 초기화 중...');

        // ModuleLoader가 이미 로드되었는지 확인
        if (window.ModuleLoader) {
            this.moduleLoader = window.ModuleLoader;
            console.log('✅ [AdminInit] ModuleLoader 준비 완료');
            return;
        }

        // ModuleLoader 로드
        await this.loadScript('static/utils/module-loader.js');

        // ModuleLoader 대기
        let attempts = 0;
        while (!window.ModuleLoader && attempts < 20) {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }

        if (!window.ModuleLoader) {
            throw new Error('ModuleLoader 로드 실패');
        }

        this.moduleLoader = window.ModuleLoader;
        console.log('✅ [AdminInit] ModuleLoader 로드 완료');
    }

    /**
     * 핵심 모듈 로드
     */
    async loadCoreModules() {
        console.log('📦 [AdminInit] 핵심 모듈 로드 중...');

        // config와 admin-cache 로드
        await this.moduleLoader.loadCoreModules();

        console.log('✅ [AdminInit] 핵심 모듈 로드 완료');
    }

    /**
     * 기본 UI 설정
     */
    setupBasicUI() {
        console.log('🎨 [AdminInit] 기본 UI 설정 중...');

        // 현재 날짜 표시
        const currentDateElement = document.getElementById('current-date');
        if (currentDateElement) {
            currentDateElement.textContent = new Date().toLocaleDateString('ko-KR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                weekday: 'short'
            });
        }

        console.log('✅ [AdminInit] 기본 UI 설정 완료');
    }

    /**
     * 네비게이션 초기화
     */
    async initializeNavigation() {
        console.log('🧭 [AdminInit] 네비게이션 초기화 중...');

        // AdminNavigation 모듈 로드
        if (!window.AdminNavigation) {
            await this.loadScript('static/js/admin-navigation.js');

            let attempts = 0;
            while (!window.AdminNavigation && attempts < 20) {
                await new Promise(resolve => setTimeout(resolve, 100));
                attempts++;
            }
        }

        if (window.AdminNavigation) {
            window.navigation = new AdminNavigation(this.moduleLoader);
            window.navigation.initialize();
            console.log('✅ [AdminInit] 네비게이션 초기화 완료');
        } else {
            console.warn('⚠️ [AdminInit] 네비게이션 모듈 로드 실패');
        }
    }

    /**
     * 대시보드 초기화
     */
    async initializeDashboard() {
        console.log('📊 [AdminInit] 대시보드 초기화 중...');

        try {
            // dashboard-core 모듈 로드
            const DashboardCore = await this.moduleLoader.loadModule('dashboard-core');

            if (DashboardCore) {
                window.dashboard = new DashboardCore();
                await window.dashboard.init();
                console.log('✅ [AdminInit] 대시보드 초기화 완료');
            }
        } catch (error) {
            console.warn('⚠️ [AdminInit] 대시보드 모듈 로드 실패:', error);
            // 대시보드 로드 실패는 치명적이지 않으므로 계속 진행
        }
    }

    /**
     * 스크립트 동적 로드
     */
    loadScript(src) {
        return new Promise((resolve, reject) => {
            const existing = document.querySelector(`script[src="${src}"]`);
            if (existing) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    /**
     * 초기화 에러 표시
     */
    showInitializationError(error) {
        const contentArea = document.getElementById('content-area');
        if (contentArea) {
            contentArea.innerHTML = `
                <div style="padding: 40px; text-align: center; background: #fff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #ff6b6b;">⚠️ 시스템 초기화 실패</h2>
                    <p style="color: #666; margin: 20px 0;">관리자 시스템을 시작할 수 없습니다.</p>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; font-family: monospace; font-size: 12px; color: #333; text-align: left;">
                        ${error.message || error.toString()}
                    </div>
                    <button onclick="location.reload()" style="padding: 12px 24px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; margin-right: 10px;">
                        🔄 페이지 새로고침
                    </button>
                    <button onclick="debugInfo.modules()" style="padding: 12px 24px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer;">
                        🔍 모듈 상태 확인
                    </button>
                </div>
            `;
        }
    }

    /**
     * 로그아웃 처리
     */
    async logout() {
        if (confirm('로그아웃하시겠습니까?')) {
            try {
                // 캐시 정리
                if (window.AdminCache) {
                    AdminCache.clearAllCache();
                    console.log('🗑️ [Logout] 캐시 정리 완료');
                }

                // 대시보드 정리
                if (window.dashboard && typeof window.dashboard.destroy === 'function') {
                    window.dashboard.destroy();
                    console.log('🧹 [Logout] 대시보드 정리 완료');
                }

                // 모듈 정리
                if (this.moduleLoader) {
                    this.moduleLoader.reset();
                    console.log('🔄 [Logout] 모듈 초기화 완료');
                }

                // 메인 페이지로 이동
                console.log('🚪 [Logout] 메인 페이지로 이동');
                window.location.href = '/';

            } catch (error) {
                console.error('❌ [Logout] 로그아웃 중 오류:', error);
                // 오류가 있어도 로그아웃 진행
                window.location.href = '/';
            }
        }
    }
}

// 전역 초기화 인스턴스
window.adminInit = new AdminInitializer();

// 전역 로그아웃 함수
window.logout = () => window.adminInit.logout();

// 개발자 디버그 함수
window.debugInfo = {
    modules: () => window.ModuleLoader ? ModuleLoader.getModuleStatus() : 'ModuleLoader not loaded',
    cache: () => window.AdminCache ? AdminCache.getCacheStatus() : 'AdminCache not loaded',
    dashboard: () => window.dashboard || 'Dashboard not initialized',
    reload: () => location.reload(),
    clearCache: () => window.AdminCache ? AdminCache.clearAllCache() : 'AdminCache not available'
};

console.log('✅ [AdminInit] 초기화 모듈 준비 완료');