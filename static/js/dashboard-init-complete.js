/**
 * Admin Dashboard 초기화 스크립트
 * admin_dashboard.html의 인라인 JavaScript에서 분리
 */

// CONFIG 설정
window.CONFIG = window.CONFIG || {
    API_BASE_URL: 'http://127.0.0.1:8010',
    API_TIMEOUT: 30000
};

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

// 페이지 네비게이션 설정
function setupNavigation() {
    console.log('🧭 네비게이션 설정 중...');

    document.querySelectorAll('.nav-item').forEach(navItem => {
        navItem.addEventListener('click', function(e) {
            e.preventDefault();
            const targetPage = this.getAttribute('data-page');
            switchToPage(targetPage);
        });
    });

    // 기본으로 대시보드 활성화
    switchToPage('dashboard');

    // 초기 대시보드 통계 로드
    fetch(`${window.CONFIG.API_BASE_URL}/api/admin/dashboard-stats`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const els = {
                    'total-users': data.totalUsers,
                    'total-sites': data.totalSites,
                    'total-ingredients': (data.totalIngredients || 0).toLocaleString(),
                    'total-suppliers': data.totalSuppliers
                };
                for (const [id, value] of Object.entries(els)) {
                    const el = document.getElementById(id);
                    if (el) el.textContent = value;
                }
            }
        })
        .catch(err => console.error('초기 대시보드 통계 로드 실패:', err));
}

async function switchToPage(pageName) {
    console.log(`🔄 페이지 전환: ${pageName}`);

    // 네비게이션 상태 업데이트
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });

    const activeNavItem = document.querySelector(`[data-page="${pageName}"]`);
    if (activeNavItem) {
        activeNavItem.classList.add('active');
    }

    // 모든 페이지 콘텐츠 숨기기 - display 직접 제어
    document.querySelectorAll('.page-content').forEach(content => {
        content.classList.remove('active');
        content.style.display = 'none';
    });

    // 선택된 페이지만 표시 - display 직접 제어
    const targetContent = document.getElementById(`${pageName}-content`);
    if (targetContent) {
        targetContent.classList.add('active');
        targetContent.style.display = 'block';
        console.log(`✅ ${pageName} 콘텐츠 표시 완료`);

        // 모듈 초기화
        await initializePageModule(pageName);
    } else {
        console.error(`❌ ${pageName}-content 요소를 찾을 수 없음`);
    }
}

// 페이지별 모듈 초기화
async function initializePageModule(pageName) {
    // 대시보드는 모듈 초기화 불필요
    if (pageName === 'dashboard') {
        console.log('📊 대시보드 - 모듈 초기화 불필요');
        // 대시보드 통계 로드
        fetch(`${window.CONFIG.API_BASE_URL}/api/admin/dashboard-stats`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const els = {
                        'total-users': data.totalUsers,
                        'total-sites': data.totalSites,
                        'total-ingredients': (data.totalIngredients || 0).toLocaleString(),
                        'total-suppliers': data.totalSuppliers
                    };
                    for (const [id, value] of Object.entries(els)) {
                        const el = document.getElementById(id);
                        if (el) el.textContent = value;
                    }
                }
            })
            .catch(err => console.error('대시보드 통계 로드 실패:', err));
        return;
    }

    const fallbackInitialization = {
        'users': async () => {
            // 템플릿 로드 먼저 (HTTP 환경에서만 작동)
            const userContent = document.getElementById('users-content');
            if (userContent && userContent.innerHTML.trim().length < 100) {
                try {
                    // HTTP 환경에서는 파일 로드
                    if (window.location.protocol.startsWith('http')) {
                        const response = await fetch('static/templates/users-section.html');
                        if (response.ok) {
                            const html = await response.text();
                            userContent.innerHTML = html;
                            console.log('✅ 사용자 템플릿 로드 완료');
                        }
                    } else {
                        // file:// 프로토콜에서는 폴백 HTML
                        userContent.innerHTML = '<div class="page-header"><h2>사용자 관리</h2><p>file:// 프로토콜에서는 제한적 기능만 지원됩니다.</p></div>';
                        console.log('✅ 사용자 템플릿 폴백 삽입');
                    }
                } catch (err) {
                    console.error('❌ 사용자 템플릿 로드 실패:', err);
                }
            }

            // 모듈 초기화
            if (!window.UsersManagementFull) {
                await loadScript('static/modules/users/users-management-full.js');
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            return window.UsersManagementFull?.init?.();
        },
        'suppliers': async () => {
            // 템플릿 로드 (추후 구현)

            // 모듈 초기화
            if (!window.SupplierManagement) {
                await loadScript('static/modules/suppliers/suppliers.js');
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            return window.SupplierManagement?.init?.();
        },
        'business-locations': async () => {
            // 템플릿 로드
            const sitesContent = document.getElementById('business-locations-content');
            if (sitesContent && sitesContent.innerHTML.trim().length < 100) {
                try {
                    // HTTP 환경에서는 파일 로드
                    if (window.location.protocol.startsWith('http')) {
                        const response = await fetch('static/templates/sites-section.html');
                        if (response.ok) {
                            const html = await response.text();
                            sitesContent.innerHTML = html;
                            console.log('✅ 사업장 템플릿 로드 완료');
                        }
                    } else {
                        // file:// 프로토콜에서는 폴백 HTML
                        sitesContent.innerHTML = '<div class="page-header"><h2>사업장 관리</h2><p>file:// 프로토콜에서는 제한적 기능만 지원됩니다.</p></div>';
                        console.log('✅ 사업장 템플릿 폴백 삽입');
                    }
                } catch (err) {
                    console.error('❌ 사업장 템플릿 로드 실패:', err);
                }
            }

            // 모듈 초기화
            if (!window.BusinessLocationsModule) {
                await loadScript('static/modules/sites/sites.js');
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            return window.BusinessLocationsModule?.init?.();
        },
        'meal-pricing': async () => {
            console.log('🎯 meal-pricing 모듈 초기화 시작');

            // 템플릿 로드
            const pricingContent = document.getElementById('meal-pricing-content');
            if (pricingContent && pricingContent.innerHTML.trim().length < 100) {
                try {
                    // HTTP 환경에서는 파일 로드
                    if (window.location.protocol.startsWith('http')) {
                        const response = await fetch('static/templates/meal-pricing-section.html');
                        if (response.ok) {
                            const html = await response.text();
                            pricingContent.innerHTML = html;
                            console.log('✅ 식단가 템플릿 파일 로드 완료');
                        }
                    } else {
                        // file:// 프로토콜에서는 직접 HTML 삽입 (폴백)
                        pricingContent.innerHTML = `<div class="page-header">
                            <h2>식단가 관리</h2>
                            <p class="page-description">사업장별 세부식단표를 관리하고 끼니별 판매가, 목표식재료비를 설정합니다.</p>
                        </div>`;
                        console.log('✅ 식단가 템플릿 폴백 삽입');
                    }
                } catch (err) {
                    console.error('❌ 식단가 템플릿 로드 실패:', err);
                }
            }

            // Meal Pricing 모듈 로드 (운영타입/계획명 직접 수정 버전)
            const timestamp = new Date().getTime();
            await loadScript(`static/modules/meal-pricing/meal-pricing.js?v=${timestamp}`);
            await new Promise(resolve => setTimeout(resolve, 100));

            if (window.MealPricingModule) {
                console.log('🚀 MealPricingModule.init 호출');
                await window.MealPricingModule.init();
                // 사업장 선택 이벤트 추가
                const select = document.getElementById('businessLocationSelect');
                if (select) {
                    select.addEventListener('change', window.loadMealPlansForLocation);
                }
            } else {
                console.error('❌ MealPricingModule을 찾을 수 없음');
            }
        },
        'ingredients': async () => {
            if (!window.IngredientManagement) {
                await loadScript('static/modules/ingredients/ingredients.js');
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            return window.IngredientManagement?.init?.();
        },
        'supplier-mapping': async () => {
            // 개선된 매핑 모듈 사용
            if (!window.initEnhancedMapping) {
                await loadScript('static/modules/mappings/enhanced-mapping.js');
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            // 개선된 매핑 초기화
            if (window.initEnhancedMapping) {
                await window.initEnhancedMapping();
            }
        }
    };

    // ModuleLoader 먼저 시도
    if (window.moduleLoader) {
        try {
            console.log(`📦 [ModuleLoader] ${pageName} 모듈 로드 중...`);
            const moduleObject = await window.moduleLoader.loadModule(pageName);

            if (moduleObject && typeof moduleObject.init === 'function') {
                console.log(`🎯 [ModuleLoader] ${pageName} 모듈 초기화 중...`);
                await moduleObject.init();
                console.log(`✅ [ModuleLoader] ${pageName} 모듈 초기화 완료`);
                return;
            }
        } catch (error) {
            console.warn(`⚠️ [ModuleLoader] ${pageName} 모듈 로드 실패:`, error);
        }
    }

    // 폴백: 직접 모듈 로딩
    console.log(`🔄 [Fallback] 직접 ${pageName} 모듈 로드 중...`);
    if (fallbackInitialization[pageName]) {
        try {
            await fallbackInitialization[pageName]();
            console.log(`✅ [Fallback] ${pageName} 모듈 초기화 완료`);
        } catch (fallbackError) {
            console.error(`❌ [Fallback] ${pageName} 모듈 초기화 실패:`, fallbackError);
        }
    } else {
        console.warn(`⚠️ ${pageName} 페이지에 대한 모듈이 정의되지 않음`);
    }
}

// 간단한 초기화 함수
async function initializePage() {
    console.log('🚀 [Admin Dashboard] 초기화 시작');

    // 날짜 표시
    const currentDateElement = document.getElementById('current-date');
    if (currentDateElement) {
        currentDateElement.textContent = new Date().toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            weekday: 'short'
        });
    }

    console.log('✅ [Admin Dashboard] 초기화 완료');
}

// 초기화 에러 표시 함수
function showInitializationError(error) {
    const contentArea = document.getElementById('content-area');
    if (contentArea) {
        contentArea.innerHTML = `
            <div style="padding: 40px; text-align: center; background: #fff; border-radius: 10px;">
                <h2 style="color: #ff6b6b;">⚠️ 시스템 초기화 실패</h2>
                <p style="color: #666; margin: 20px 0;">관리자 시스템을 시작할 수 없습니다.</p>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    ${error.message || error.toString()}
                </div>
                <button onclick="location.reload()" style="padding: 12px 24px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    🔄 페이지 새로고침
                </button>
            </div>
        `;
    }
}

// 로그아웃 함수 (전역으로 필요)
window.logout = function() {
    if (confirm('로그아웃 하시겠습니까?')) {
        alert('로그아웃 되었습니다.');
        window.location.href = '/';
    }
};

// 페이지 로드 시 통합 초기화 (단일 DOMContentLoaded 이벤트)
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🎯 [Admin Dashboard] 통합 초기화 시작');

    try {
        // 기본 초기화 실행
        await initializePage();

        // 네비게이션 설정
        setupNavigation();

        console.log('✅ [Admin Dashboard] 통합 초기화 완료');

    } catch (error) {
        console.error('❌ [Admin Dashboard] 통합 초기화 실패:', error);
        showInitializationError(error);
    }
});

// 전역 함수 export (다른 모듈에서 사용 가능)
window.dashboardInit = {
    loadScript,
    switchToPage,
    initializePageModule,
    setupNavigation
};