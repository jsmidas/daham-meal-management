// 페이지 네비게이션 관리
function showPage(pageName) {
    // 모든 페이지 숨기기
    document.querySelectorAll('.page-content').forEach(page => {
        page.classList.add('hidden');
    });
    
    // 선택된 페이지 보이기
    const targetPage = document.getElementById(`${pageName}-page`);
    if (targetPage) {
        targetPage.classList.remove('hidden');
    }
    
    // 네비게이션 활성 상태 변경
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const activeItem = document.querySelector(`[data-page="${pageName}"]`);
    if (activeItem) {
        activeItem.classList.add('active');
    }
    
    // 페이지 제목 변경
    const titles = {
        'dashboard': '관리자 대시보드',
        'users': '사용자 관리',
        'suppliers': '업체 관리',
        'business-locations': '사업장 관리',
        'supplier-mapping': '협력업체 매핑',
        'meal-pricing': '식단가 관리',
        'ingredients': '식자재 관리',
        'pricing': '단가 관리',
        'settings': '시스템 설정',
        'logs': '로그 관리'
    };
    
    document.getElementById('page-title').textContent = titles[pageName] || '관리자 시스템';
}

// 로그아웃 함수
async function logout() {
    if (confirm('로그아웃 하시겠습니까?')) {
        try {
            const response = await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include'  // 쿠키 포함
            });
            
            const result = await response.json();
            
            if (result.success) {
                window.location.href = result.redirect || '/login';
            } else {
                console.error('로그아웃 실패:', result.message);
                window.location.href = '/login';  // 실패해도 로그인 페이지로 이동
            }
        } catch (error) {
            console.error('로그아웃 중 오류:', error);
            window.location.href = '/login';  // 오류 시에도 로그인 페이지로 이동
        }
    }
}

// 네비게이션 초기화 - 즉시 실행하되 DOM이 준비될 때까지 대기
function initNavigation() {
    console.log('[Navigation] 네비게이션 초기화 시작');
    
    const items = document.querySelectorAll('.nav-item');
    console.log(`[Navigation] ${items.length}개의 네비게이션 아이템 발견`);
    
    // 네비게이션 클릭 이벤트
    items.forEach(item => {
        item.addEventListener('click', (e) => {
            console.log('[Navigation] 네비게이션 아이템 클릭:', e.currentTarget.getAttribute('data-page'));
            
            // target="_blank"가 있는 링크는 새 탭에서 열리도록 허용
            if (e.currentTarget.getAttribute('target') === '_blank') {
                return; // 기본 동작 허용
            }
            
            // href가 있는 외부 링크(협력업체 관리, 사업장 관리, 급식관리로 이동)는 기본 동작 허용
            const href = e.currentTarget.getAttribute('href');
            if (href && (href.startsWith('/admin/suppliers') || href.startsWith('/admin/business-locations') || href === '/')) {
                return; // 기본 동작 허용
            }
            
            e.preventDefault();
            const pageName = e.currentTarget.getAttribute('data-page');
            if (pageName) {
                showPage(pageName);
                
                // 페이지별 초기화
                if (pageName === 'dashboard') {
                    if (window.DashboardModule && window.DashboardModule.loadDashboardData) {
                        window.DashboardModule.loadDashboardData();
                        window.DashboardModule.loadRecentActivity();
                    }
                } else if (pageName === 'users') {
                    if (window.UsersModule && window.UsersModule.loadUsers) {
                        window.UsersModule.loadUsers();
                    }
                    if (window.loadManagedSites) window.loadManagedSites();
                } else if (pageName === 'suppliers') {
                    if (window.loadSuppliers) window.loadSuppliers();
                } else if (pageName === 'business-locations') {
                    if (window.loadSitesTree) window.loadSitesTree();
                } else if (pageName === 'ingredients') {
                    if (window.loadIngredientsList) window.loadIngredientsList();
                    if (window.loadSupplierFilter) window.loadSupplierFilter();
                }
            }
        });
    });
    
    console.log('[Navigation] 네비게이션 초기화 완료');
}

// DOM이 준비되면 즉시 초기화 실행
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNavigation);
} else {
    // DOM이 이미 로드된 경우 즉시 실행
    initNavigation();
}

// 전역 함수로 내보내기
window.showPage = showPage;
window.logout = logout;