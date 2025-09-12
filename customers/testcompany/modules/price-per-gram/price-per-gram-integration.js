/**
 * g당 단가 모듈 통합 스크립트
 * 페이지 로드 시 자동으로 적절한 컨텍스트에서 모듈을 초기화
 */

// 모듈이 이미 로드되었다면 중복 실행 방지
if (window.pricePerGramIntegrated) {
    console.log('g당 단가 모듈이 이미 통합되었습니다.');
} else {
    window.pricePerGramIntegrated = true;
    
    // DOM이 준비되면 통합 시작
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPricePerGramIntegration);
    } else {
        initPricePerGramIntegration();
    }
}

function initPricePerGramIntegration() {
    console.log('g당 단가 모듈 통합을 시작합니다...');
    
    // PricePerGramModule이 로드될 때까지 대기
    const checkAndIntegrate = () => {
        if (window.PricePerGramModule && window.priceModule) {
            console.log('✅ g당 단가 모듈이 성공적으로 통합되었습니다.');
            
            // 페이지 변경 감지하여 동적으로 재초기화
            observePageChanges();
            
            // 현재 페이지에 맞는 모듈 즉시 활성화
            setTimeout(() => {
                if (window.priceModule) {
                    // 대시보드 통계 카드 활성화
                    window.priceModule.initDashboardStats();
                    
                    // 식자재 관리 워크스페이스 활성화
                    window.priceModule.initIngredientsWorkspace();
                }
            }, 500);
            
        } else {
            // 최대 5초까지 대기
            setTimeout(checkAndIntegrate, 100);
        }
    };
    
    checkAndIntegrate();
}

// 페이지 변경 감지
function observePageChanges() {
    // DOM 변경 관찰
    const observer = new MutationObserver((mutations) => {
        let shouldReinit = false;
        
        mutations.forEach((mutation) => {
            // 새로운 노드가 추가된 경우
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1) {
                    // KPI 그리드가 추가되면 대시보드 통계 재초기화
                    if (node.querySelector && node.querySelector('.kpi-grid')) {
                        shouldReinit = true;
                    }
                    
                    // 식자재 컨텐츠가 추가되면 워크스페이스 재초기화
                    if (node.id === 'ingredients-page' || 
                        node.id === 'ingredients-content' || 
                        (node.classList && node.classList.contains('ingredients-section'))) {
                        shouldReinit = true;
                    }
                }
            });
        });
        
        // 필요한 경우 모듈 재초기화
        if (shouldReinit && window.priceModule) {
            setTimeout(() => {
                window.priceModule.initDashboardStats();
                window.priceModule.initIngredientsWorkspace();
            }, 100);
        }
    });
    
    // body 전체를 관찰
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // 네비게이션 클릭 이벤트 감지
    document.addEventListener('click', (e) => {
        // 페이지 네비게이션 클릭 감지
        if (e.target.matches('[data-section]') || 
            e.target.matches('a[href*="#"]') ||
            e.target.closest('[data-section]')) {
            
            // 약간의 지연 후 모듈 재초기화
            setTimeout(() => {
                if (window.priceModule) {
                    window.priceModule.initDashboardStats();
                    window.priceModule.initIngredientsWorkspace();
                }
            }, 200);
        }
    });
}

// 전역 유틸리티 함수들
window.pricePerGramUtils = {
    // 강제 재초기화
    forceReinit: () => {
        if (window.priceModule) {
            console.log('g당 단가 모듈 강제 재초기화...');
            window.priceModule.initDashboardStats();
            window.priceModule.initIngredientsWorkspace();
        }
    },
    
    // 통계만 새로고침
    refreshStats: () => {
        if (window.priceModule) {
            window.priceModule.loadDashboardStats();
            window.priceModule.loadWorkspaceStats();
        }
    },
    
    // 디버그 정보
    debug: () => {
        console.log('=== g당 단가 모듈 디버그 정보 ===');
        console.log('모듈 로드됨:', !!window.PricePerGramModule);
        console.log('모듈 인스턴스:', !!window.priceModule);
        console.log('통합 완료:', !!window.pricePerGramIntegrated);
        console.log('KPI 그리드 존재:', !!document.querySelector('.kpi-grid'));
        console.log('admin 식자재 페이지 존재:', !!document.getElementById('ingredients-page'));
        console.log('독립 식자재 컨텐츠 존재:', !!document.getElementById('ingredients-content'));
        console.log('g당 단가 카드 존재:', !!document.querySelector('.kpi-card.price-analysis'));
        console.log('워크스페이스 존재:', !!document.getElementById('price-per-gram-workspace'));
    }
};

console.log('g당 단가 모듈 통합 스크립트가 로드되었습니다.');