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
    fetch(`${window.location.origin}/api/admin/dashboard-stats`)
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
        fetch(`${window.location.origin}/api/admin/dashboard-stats`)
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

        // 최근 활동 로그 로드
        loadActivityLogs();
        startActivityRefresh();
        return;
    }

    const fallbackInitialization = {
        'users': async () => {
            // Enhanced User Management 모듈 사용
            if (window.enhancedUserMgmt) {
                console.log('✅ Enhanced User Management 모듈 사용');
                return window.enhancedUserMgmt.init();
            }

            // Enhanced 모듈이 없으면 로드
            if (!window.enhancedUserMgmt) {
                await loadScript('/static/modules/users/users-enhanced.js');
                await new Promise(resolve => setTimeout(resolve, 100));
                if (window.enhancedUserMgmt) {
                    return window.enhancedUserMgmt.init();
                }
            }

            // 폴백: 기존 모듈 사용
            console.log('⚠️ Enhanced 모듈 로드 실패, 기존 모듈 사용');
            if (!window.UsersManagementFull) {
                await loadScript('/static/modules/users/users-management-full.js');
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            return window.UsersManagementFull?.init?.();
        },
        'suppliers': async () => {
            // 템플릿 로드 (추후 구현)

            // 모듈 초기화
            if (!window.SupplierManagement) {
                await loadScript('/static/modules/suppliers/suppliers.js');
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
                await loadScript('/static/modules/sites/sites.js');
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
            console.log('🥬 식자재 관리 모듈 초기화 시작');

            // 템플릿 로드
            const ingredientsContent = document.getElementById('ingredients-content');
            if (ingredientsContent && ingredientsContent.innerHTML.trim().length < 100) {
                try {
                    if (window.location.protocol.startsWith('http')) {
                        const response = await fetch('static/templates/ingredients-section.html');
                        if (response.ok) {
                            const html = await response.text();
                            ingredientsContent.innerHTML = html;
                            console.log('✅ 식자재 템플릿 로드 완료');
                        }
                    }
                } catch (err) {
                    console.error('❌ 식자재 템플릿 로드 실패:', err);
                }
            }

            // 모듈 로드
            if (!window.IngredientsModule) {
                await loadScript('/static/modules/ingredients/ingredients.js');
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            // 모듈 초기화
            if (window.IngredientsModule) {
                console.log('🚀 IngredientsModule.init 호출');
                return window.IngredientsModule.init();
            } else {
                console.error('❌ IngredientsModule을 찾을 수 없음');
            }
        },
        'supplier-mapping': async () => {
            // 개선된 매핑 모듈 사용
            if (!window.initEnhancedMapping) {
                await loadScript('/static/modules/mappings/enhanced-mapping.js');
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            // 개선된 매핑 초기화
            if (window.initEnhancedMapping) {
                await window.initEnhancedMapping();
            }
        },
        'menu-recipes': async () => {
            console.log('🍽️ 메뉴/레시피 관리 모듈 초기화 시작');

            // 템플릿 로드
            const menuRecipesContent = document.getElementById('menu-recipes-content');
            if (menuRecipesContent && menuRecipesContent.innerHTML.trim().length < 100) {
                try {
                    if (window.location.protocol.startsWith('http')) {
                        const response = await fetch('static/templates/menu-recipes-section.html');
                        if (response.ok) {
                            const html = await response.text();
                            menuRecipesContent.innerHTML = html;
                            console.log('✅ 메뉴/레시피 템플릿 로드 완료');
                        } else {
                            console.error('❌ 템플릿 파일 로드 실패:', response.status);
                            // 폴백 HTML
                            menuRecipesContent.innerHTML = `
                                <div class="page-header">
                                    <h2>메뉴/레시피 관리</h2>
                                    <p class="page-description">메뉴와 레시피를 관리하고 재료비를 계산합니다.</p>
                                    <div style="color: #ff9800; margin: 20px 0;">
                                        ⚠️ 템플릿 로드 실패 - 서버가 실행 중인지 확인해주세요.
                                    </div>
                                </div>
                            `;
                        }
                    } else {
                        // file:// 프로토콜에서는 폴백 HTML
                        menuRecipesContent.innerHTML = `
                            <div class="page-header">
                                <h2>메뉴/레시피 관리</h2>
                                <p class="page-description">file:// 프로토콜에서는 제한적 기능만 지원됩니다.</p>
                                <div style="color: #666; margin: 20px 0;">
                                    HTTP 서버를 통해 접속하면 전체 기능을 사용할 수 있습니다.
                                </div>
                            </div>
                        `;
                        console.log('✅ 메뉴/레시피 템플릿 폴백 삽입');
                    }
                } catch (err) {
                    console.error('❌ 메뉴/레시피 템플릿 로드 실패:', err);
                    menuRecipesContent.innerHTML = `
                        <div class="page-header">
                            <h2>메뉴/레시피 관리</h2>
                            <div style="color: #dc3545; margin: 20px 0;">
                                ❌ 시스템 오류가 발생했습니다: ${err.message}
                            </div>
                        </div>
                    `;
                }
            }

            // 메뉴/레시피 모듈 로드
            if (!window.MenuRecipeManagement) {
                try {
                    await loadScript('/static/modules/menu-recipes/menu-recipes.js');
                    await new Promise(resolve => setTimeout(resolve, 200));
                    console.log('📦 메뉴/레시피 스크립트 로드 완료');
                } catch (err) {
                    console.error('❌ 메뉴/레시피 스크립트 로드 실패:', err);
                    return;
                }
            }

            // 모듈 초기화
            if (window.MenuRecipeManagement) {
                try {
                    console.log('🚀 MenuRecipeManagement.init 호출');
                    await window.MenuRecipeManagement.init();
                    console.log('✅ 메뉴/레시피 모듈 초기화 완료');
                } catch (err) {
                    console.error('❌ 메뉴/레시피 모듈 초기화 실패:', err);
                    const errorDiv = document.createElement('div');
                    errorDiv.innerHTML = `
                        <div style="background: #fff3cd; border: 1px solid #ffeeba; color: #856404; padding: 15px; border-radius: 5px; margin: 20px;">
                            <h4>⚠️ 모듈 초기화 실패</h4>
                            <p>메뉴/레시피 관리 기능을 로드할 수 없습니다.</p>
                            <details>
                                <summary>오류 세부사항</summary>
                                <pre style="margin-top: 10px; background: #f8f9fa; padding: 10px; border-radius: 3px;">${err.toString()}</pre>
                            </details>
                        </div>
                    `;
                    menuRecipesContent.appendChild(errorDiv);
                }
            } else {
                console.error('❌ MenuRecipeManagement 클래스를 찾을 수 없음');
                const errorDiv = document.createElement('div');
                errorDiv.innerHTML = `
                    <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 5px; margin: 20px;">
                        <h4>❌ 모듈 로드 실패</h4>
                        <p>MenuRecipeManagement 클래스를 찾을 수 없습니다.</p>
                        <p>스크립트 파일이 올바르게 로드되었는지 확인해주세요.</p>
                    </div>
                `;
                menuRecipesContent.appendChild(errorDiv);
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

/**
 * 최근 활동 로그 로드
 */
async function loadActivityLogs() {
    console.log('📝 최근 활동 로그 로딩...');

    try {
        const API_BASE_URL = window.CONFIG?.API_BASE_URL || 'http://127.0.0.1:8010';
        const response = await fetch(`${API_BASE_URL}/api/admin/activity-logs?limit=15`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const activityList = document.getElementById('activity-list');

        if (!activityList) return;

        if (data.logs && data.logs.length > 0) {
            activityList.innerHTML = data.logs.map(log => {
                const time = new Date(log.timestamp).toLocaleString('ko-KR', {
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                });

                // 아이콘 선택
                let icon = '📝';
                if (log.action_type.includes('추가')) icon = '➕';
                else if (log.action_type.includes('수정')) icon = '✏️';
                else if (log.action_type.includes('삭제')) icon = '🗑️';
                else if (log.action_type.includes('로그인')) icon = '🔐';

                return `
                    <div class="log-item">
                        <div class="log-time">${time}</div>
                        <div class="log-message">
                            <span style="margin-right: 5px;">${icon}</span>
                            <strong>${log.user}</strong> - ${log.action_detail}
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            activityList.innerHTML = `
                <div class="log-item">
                    <div class="log-message" style="color: #999; text-align: center;">
                        아직 기록된 활동이 없습니다.
                    </div>
                </div>
            `;
        }

        console.log('✅ 최근 활동 로그 로드 완료');
    } catch (error) {
        console.warn('⚠️ 최근 활동 로그 로드 실패 (서버 재시작 필요):', error.message);
        const activityList = document.getElementById('activity-list');
        if (activityList) {
            activityList.innerHTML = `
                <div class="log-item">
                    <div class="log-message" style="color: #ff9800; text-align: center;">
                        <div style="margin-bottom: 10px;">⚠️ 활동 로그 서비스가 준비 중입니다.</div>
                        <div style="font-size: 12px; color: #666;">
                            서버를 재시작하면 활동 로그가 표시됩니다.<br>
                            (터미널에서 Ctrl+C 후 python test_samsung_api.py 실행)
                        </div>
                    </div>
                </div>
            `;
        }
    }
}

/**
 * 정기적으로 활동 로그 새로고침 (30초마다)
 */
let activityRefreshInterval = null;

function startActivityRefresh() {
    if (activityRefreshInterval) {
        clearInterval(activityRefreshInterval);
    }

    activityRefreshInterval = setInterval(() => {
        const dashboardContent = document.getElementById('dashboard-content');
        if (dashboardContent && dashboardContent.style.display !== 'none') {
            loadActivityLogs();
        }
    }, 30000); // 30초마다 새로고침
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