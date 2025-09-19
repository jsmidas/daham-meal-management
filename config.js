// 🔧 다함 식자재 관리 시스템 - 중앙 설정 파일
// ⚠️  이 파일을 수정하면 모든 API 연결이 자동으로 업데이트됩니다

const CONFIG = {
    // API 서버 설정
    API: {
        BASE_URL: 'http://dahamfood.kr',
        ENDPOINTS: {
            // 대시보드 관련
            DASHBOARD_STATS: '/api/admin/dashboard-stats',
            RECENT_ACTIVITY: '/api/admin/recent-activity',
            
            // 관리자 데이터 (캐싱 지원)
            ADMIN_USERS: '/api/admin/users',
            ADMIN_SUPPLIERS: '/api/admin/suppliers', 
            ADMIN_BUSINESS_LOCATIONS: '/api/admin/business-locations',
            ADMIN_INGREDIENTS_SUMMARY: '/api/admin/ingredients-summary',
            ADMIN_INGREDIENTS_NEW: '/api/admin/ingredients-new',

            // 메뉴/레시피 관련
            ADMIN_MENU_RECIPES: '/api/admin/menu-recipes',
            ADMIN_MENU_CATEGORIES: '/api/admin/menu-recipes/categories',

            // 기존 엔드포인트 (호환성)
            TEST_SAMSUNG: '/test-samsung-welstory',
            ALL_INGREDIENTS: '/all-ingredients-for-suppliers',
            SUPPLIERS: '/suppliers',
            USERS: '/users',
            SITES: '/business-locations'
        }
    },
    
    // 데이터베이스 설정
    DATABASE: {
        PATH: './backups/working_state_20250912/daham_meal.db',
        BACKUP_PATH: './backups/'
    },
    
    // 개발 환경 설정
    DEV: {
        AUTO_RELOAD: true,
        DEBUG_MODE: false,
        MOCK_DATA: false
    },
    
    // 브랜딩 설정 (화이트라벨링)
    BRANDING: {
        COMPANY_NAME: '다함푸드',
        SYSTEM_NAME: '급식관리',
        LOGO_PATH: 'static/images/daham_logo.png',
        SIDEBAR_TITLE: '급식관리',
        FAVICON: 'static/images/favicon.ico',
        COLORS: {
            PRIMARY: '#2a5298',
            SECONDARY: '#667eea'
        }
    },

    // UI 설정
    UI: {
        ITEMS_PER_PAGE: 50,
        REFRESH_INTERVAL: 30000, // 30초
        THEME: 'light'
    }
};

// 🌍 전역에서 사용 가능하도록 설정
if (typeof window !== 'undefined') {
    window.CONFIG = CONFIG;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}

// 🔧 API URL 생성 헬퍼 함수
const API = {
    url: (endpoint) => `${CONFIG.API.BASE_URL}${CONFIG.API.ENDPOINTS[endpoint] || endpoint}`,
    get: (endpoint) => fetch(API.url(endpoint)),
    post: (endpoint, data) => fetch(API.url(endpoint), {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
};

if (typeof window !== 'undefined') {
    window.API = API;
}