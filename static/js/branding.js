/**
 * 🏢 브랜딩 관리 시스템
 * 화이트라벨링을 위한 로고 및 회사명 동적 적용
 */

const BrandingManager = {
    /**
     * 브랜딩 정보 가져오기
     */
    getBranding() {
        if (typeof CONFIG !== 'undefined' && CONFIG.BRANDING) {
            return CONFIG.BRANDING;
        }

        // 기본값 (CONFIG 로드 실패시)
        return {
            COMPANY_NAME: '다함푸드',
            SYSTEM_NAME: '급식관리',
            LOGO_PATH: 'static/images/logo.svg',
            SIDEBAR_TITLE: '급식관리',
            COLORS: {
                PRIMARY: '#2a5298',
                SECONDARY: '#667eea'
            }
        };
    },

    /**
     * 사이드바 헤더 HTML 생성
     */
    generateSidebarHeader(isCompact = false) {
        const branding = this.getBranding();

        if (isCompact) {
            // 컴팩트 버전 (어드민용) - 은색 배경에 검정 글씨
            return `
                <div class="sidebar-header branded-header" style="background: linear-gradient(135deg, #e8e8e8, #f5f5f5); border-bottom: 1px solid #d0d0d0;">
                    <div style="display: flex; align-items: center; gap: 8px; padding: 15px 12px;">
                        <img src="${branding.LOGO_PATH}"
                             alt="${branding.COMPANY_NAME} 로고"
                             style="height: 24px; width: auto; flex-shrink: 0;"
                             onerror="this.style.display='none'">
                        <div style="overflow: hidden; flex: 1;">
                            <h2 style="margin: 0; font-size: 13px; font-weight: 700; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                ${branding.COMPANY_NAME}
                            </h2>
                            <p style="margin: 0; font-size: 10px; color: #666; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                ${branding.SYSTEM_NAME}
                            </p>
                        </div>
                    </div>
                </div>
            `;
        } else {
            // 일반 버전 (기존과 동일)
            return `
                <div class="sidebar-header branded-header">
                    <div style="display: flex; align-items: center; gap: 12px; padding: 20px;">
                        <img src="${branding.LOGO_PATH}"
                             alt="${branding.COMPANY_NAME} 로고"
                             style="height: 32px; width: auto;"
                             onerror="this.style.display='none'">
                        <div>
                            <h2 style="margin: 0; font-size: 16px; font-weight: 700; color: white;">
                                ${branding.COMPANY_NAME}
                            </h2>
                            <p style="margin: 0; font-size: 12px; color: rgba(255,255,255,0.8);">
                                ${branding.SYSTEM_NAME}
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }
    },

    /**
     * 기존 사이드바 헤더를 브랜딩 헤더로 교체
     */
    applySidebarBranding() {
        // 사이드바 자체 찾기
        const sidebar = document.querySelector('.sidebar, nav.sidebar, .left-panel');

        if (!sidebar) {
            console.warn('⚠️ 사이드바를 찾을 수 없습니다.');
            return;
        }

        // 기존 브랜딩 헤더가 있는지 확인 (중복 적용 방지)
        if (sidebar.querySelector('.branded-header')) {
            console.log('✅ 브랜딩 헤더가 이미 존재합니다.');
            return;
        }

        // 어드민 대시보드인지 확인 (컴팩트 레이아웃 적용)
        const isAdminPage = document.title.includes('관리자') ||
                           window.location.pathname.includes('admin') ||
                           document.querySelector('.admin-dashboard');

        // 다양한 사이드바 헤더 선택자들 (더 포괄적)
        const headerSelectors = [
            '.sidebar-header',
            '.sidebar .logo',
            '.sidebar h1:first-child',
            '.sidebar h2:first-child',
            'nav.sidebar > div:first-child',
            'nav.sidebar > h1:first-child',
            'nav.sidebar > h2:first-child',
            '.left-panel h2:first-child',
            '.logo h1',
            'h1:first-child'
        ];

        let headerElement = null;

        // 기존 헤더 찾기 (사이드바 내부에서만 검색)
        for (const selector of headerSelectors) {
            headerElement = sidebar.querySelector(selector.replace('.sidebar ', '').replace('nav.sidebar > ', ''));
            if (headerElement) {
                console.log(`🔍 기존 헤더 발견: ${selector}`);
                break;
            }
        }

        if (headerElement) {
            // 기존 헤더를 브랜딩 헤더로 교체 (어드민인 경우 컴팩트 버전)
            headerElement.outerHTML = this.generateSidebarHeader(isAdminPage);
            console.log(`🔄 기존 헤더를 브랜딩 헤더로 교체했습니다. ${isAdminPage ? '(컴팩트 버전)' : ''}`);
        } else {
            // 헤더가 없으면 사이드바 맨 앞에 추가 (어드민인 경우 컴팩트 버전)
            sidebar.insertAdjacentHTML('afterbegin', this.generateSidebarHeader(isAdminPage));
            console.log(`➕ 사이드바에 브랜딩 헤더를 추가했습니다. ${isAdminPage ? '(컴팩트 버전)' : ''}`);
        }
    },

    /**
     * 브라우저 타이틀 업데이트
     */
    updatePageTitle(pageTitle = '') {
        const branding = this.getBranding();
        const fullTitle = pageTitle
            ? `${pageTitle} - ${branding.COMPANY_NAME} ${branding.SYSTEM_NAME}`
            : `${branding.COMPANY_NAME} ${branding.SYSTEM_NAME}`;

        document.title = fullTitle;
    },

    /**
     * CSS 커스텀 속성으로 브랜딩 색상 적용
     */
    applyBrandingColors() {
        const branding = this.getBranding();
        const root = document.documentElement;

        root.style.setProperty('--brand-primary', branding.COLORS.PRIMARY);
        root.style.setProperty('--brand-secondary', branding.COLORS.SECONDARY);
    },

    /**
     * 전체 브랜딩 적용
     */
    applyBranding(pageTitle = '') {
        // DOM 로드 완료 후 실행
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.applySidebarBranding();
                this.updatePageTitle(pageTitle);
                this.applyBrandingColors();
            });
        } else {
            this.applySidebarBranding();
            this.updatePageTitle(pageTitle);
            this.applyBrandingColors();
        }
    },

    /**
     * 개발자 도구용 브랜딩 정보 출력
     */
    debugBranding() {
        console.log('🏢 브랜딩 정보:', this.getBranding());
        console.log('📄 페이지 제목:', document.title);
        console.log('🎨 브랜딩 색상:', {
            primary: getComputedStyle(document.documentElement).getPropertyValue('--brand-primary'),
            secondary: getComputedStyle(document.documentElement).getPropertyValue('--brand-secondary')
        });
    }
};

// 전역에서 사용 가능하도록 설정
if (typeof window !== 'undefined') {
    window.BrandingManager = BrandingManager;

    // 개발자 도구에서 사용할 수 있도록 전역 함수 추가
    window.debugBranding = () => BrandingManager.debugBranding();
}

// 자동 브랜딩 적용 (페이지 로드시)
// 페이지별로 호출하거나, 자동으로 적용하려면 주석 해제
// BrandingManager.applyBranding();