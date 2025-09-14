/**
 * Admin Dashboard Initialization Script
 * 관리자 대시보드 초기화 및 핵심 기능
 */

// 스크립트 동적 로드 헬퍼 함수
function loadScript(src) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

// 개선된 ModuleLoader 기반 초기화 (안전성 + 단순성)
async function initializePage() {
    console.log('🚀 [Admin Dashboard] 개선된 초기화 시작');

    try {
        // Phase 1: 필수 모듈 순차 로드
        console.log('📦 [Admin Dashboard] 필수 모듈 로드 중...');

        // config.js 먼저 로드
        if (!window.CONFIG) {
            console.log('🔧 config.js 로딩...');
            await loadScript('config.js');

            let attempts = 0;
            while (!window.CONFIG && attempts < 20) {
                await new Promise(resolve => setTimeout(resolve, 100));
                attempts++;
            }

            if (!window.CONFIG) {
                throw new Error('config.js 로드 실패');
            }
            console.log('✅ CONFIG 로드 완료');
        }

        // ModuleLoader는 선택사항 - 직접 모듈 로딩으로 대체
        console.log('🔄 간소화된 모드로 작동 - ModuleLoader 생략');
        window.moduleLoader = null;

        // Phase 2: 날짜 표시 등 기본 UI
        const currentDateElement = document.getElementById('current-date');
        if (currentDateElement) {
            currentDateElement.textContent = new Date().toLocaleDateString('ko-KR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                weekday: 'short'
            });
        }

        console.log('✅ [Admin Dashboard] 개선된 초기화 완료');

    } catch (error) {
        console.error('❌ [Admin Dashboard] 초기화 실패:', error);
        showInitializationError(error);
    }
}

/**
 * 초기화 실패 시 에러 표시
 */
function showInitializationError(error) {
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
                <button onclick="checkModuleStatus()" style="padding: 12px 24px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    🔍 모듈 상태 확인
                </button>
            </div>
        `;
    }
}

/**
 * 안전한 로그아웃 (의존성 확인 후 실행)
 */
async function logout() {
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

/**
 * 페이지 네비게이션 설정
 */
function setupNavigation() {
    console.log('🧭 네비게이션 설정 중...');

    document.querySelectorAll('.nav-item').forEach(navItem => {
        navItem.addEventListener('click', function(e) {
            e.preventDefault();

            // 활성 메뉴 변경
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            this.classList.add('active');

            // 페이지 내용 변경
            const page = this.dataset.page;
            showPage(page);
        });
    });
}

/**
 * 페이지 전환 함수
 */
function showPage(pageName) {
    console.log(`📄 페이지 전환: ${pageName}`);

    // 모든 페이지 숨기기
    document.querySelectorAll('.page-content').forEach(content => {
        content.style.display = 'none';
        content.classList.remove('active');
    });

    // 선택된 페이지 표시
    const pageContent = document.getElementById(`${pageName}-content`);
    if (pageContent) {
        pageContent.style.display = 'block';
        pageContent.classList.add('active');

        // 페이지별 초기화 함수 호출
        loadPageModule(pageName);
    }

    // URL 해시 업데이트 (브라우저 히스토리)
    window.location.hash = pageName;
}

/**
 * 페이지별 모듈 로드
 */
async function loadPageModule(pageName) {
    console.log(`🔄 모듈 로드 중: ${pageName}`);

    switch(pageName) {
        case 'users':
            if (window.userManagement && typeof window.userManagement.load === 'function') {
                await window.userManagement.load();
            } else {
                console.log('⏳ 사용자 관리 모듈 로딩 중...');
                setTimeout(() => loadPageModule(pageName), 500);
            }
            break;

        case 'suppliers':
            if (window.SuppliersManagementFull && typeof window.SuppliersManagementFull.init === 'function') {
                window.SuppliersManagementFull.init();
            }
            break;

        case 'business-locations':
            if (window.SitesManagement && typeof window.SitesManagement.init === 'function') {
                window.SitesManagement.init();
            }
            break;

        case 'supplier-mappings':
            loadSupplierMappings();
            break;

        case 'meal-pricing':
            loadMealPricing();
            break;

        case 'ingredients':
            loadIngredients();
            break;

        case 'dashboard':
        default:
            loadDashboardStats();
            break;
    }
}

/**
 * 대시보드 통계 로드
 */
async function loadDashboardStats() {
    console.log('📊 대시보드 통계 로딩...');

    try {
        const API_BASE_URL = window.CONFIG?.API?.BASE_URL || 'http://127.0.0.1:8010';
        const response = await fetch(`${API_BASE_URL}/api/admin/dashboard-stats`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // 통계 업데이트
        updateDashboardCard('total-users', data.totalUsers || 0);
        updateDashboardCard('total-suppliers', data.totalSuppliers || 0);
        updateDashboardCard('total-ingredients', data.totalIngredients || 0);
        updateDashboardCard('active-sites', data.activeSites || 0);

        console.log('✅ 대시보드 통계 로드 완료');
    } catch (error) {
        console.error('❌ 대시보드 통계 로드 실패:', error);
    }
}

/**
 * 대시보드 카드 업데이트
 */
function updateDashboardCard(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value.toLocaleString('ko-KR');
    }
}

/**
 * 협력업체 매핑 로드
 */
function loadSupplierMappings() {
    console.log('🔗 협력업체 매핑 로딩...');
    const content = document.getElementById('supplier-mappings-content');
    if (content) {
        content.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> 로딩 중...</div>';
        // 실제 모듈 로드 로직
    }
}

/**
 * 식단가 관리 로드
 */
function loadMealPricing() {
    console.log('💰 식단가 관리 로딩...');
    const content = document.getElementById('meal-pricing-content');
    if (content) {
        content.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> 로딩 중...</div>';
        // 실제 모듈 로드 로직
    }
}

/**
 * 식자재 관리 로드
 */
function loadIngredients() {
    console.log('🥕 식자재 관리 로딩...');
    const content = document.getElementById('ingredients-content');
    if (content) {
        content.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> 로딩 중...</div>';
        // 실제 모듈 로드 로직
    }
}

/**
 * 모듈 상태 확인
 */
function checkModuleStatus() {
    const modules = {
        'CONFIG': window.CONFIG,
        'userManagement': window.userManagement,
        'SuppliersManagementFull': window.SuppliersManagementFull,
        'SitesManagement': window.SitesManagement
    };

    console.table(modules);
    return modules;
}

/**
 * 개발자용 디버그 함수들 (콘솔에서 사용)
 */
window.debugInfo = {
    modules: checkModuleStatus,
    cache: () => window.AdminCache ? AdminCache.getCacheStatus() : 'AdminCache not loaded',
    dashboard: () => window.dashboard || 'Dashboard not initialized',
    reload: () => location.reload(),
    clearCache: () => window.AdminCache ? AdminCache.clearAllCache() : 'AdminCache not available'
};

console.log('🔧 [Admin Dashboard] 디버그 함수 사용법:');
console.log('  debugInfo.modules()  - 모듈 상태 확인');
console.log('  debugInfo.cache()    - 캐시 상태 확인');
console.log('  debugInfo.dashboard() - 대시보드 상태 확인');
console.log('  debugInfo.clearCache() - 캐시 초기화');
console.log('  debugInfo.reload()   - 페이지 새로고침');

/**
 * DOM Ready 시 초기화
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', async () => {
        await initializePage();
        setupNavigation();

        // URL 해시에 따라 초기 페이지 설정
        const hash = window.location.hash.slice(1);
        if (hash) {
            showPage(hash);
        } else {
            showPage('dashboard');
        }
    });
} else {
    // 이미 로드된 경우 바로 실행
    initializePage().then(() => {
        setupNavigation();
        const hash = window.location.hash.slice(1);
        showPage(hash || 'dashboard');
    });
}