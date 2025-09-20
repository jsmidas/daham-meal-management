/**
 * 자동 로그인 모달 유틸리티
 * 401 오류 시 자동으로 로그인 모달을 띄우고, 성공 후 원래 작업을 재시도합니다.
 */

window.AuthModal = {
    modalElement: null,
    pendingAction: null, // 로그인 후 재시도할 함수
    
    // 모달 초기화
    init() {
        this.createModal();
        return this;
    },
    
    // 모달 HTML 생성
    createModal() {
        const modalHTML = `
            <div id="authModal" style="
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 10000;
                justify-content: center;
                align-items: center;
            ">
                <div style="
                    background: white;
                    border-radius: 8px;
                    padding: 24px;
                    min-width: 400px;
                    max-width: 500px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                ">
                    <div style="
                        display: flex;
                        align-items: center;
                        margin-bottom: 20px;
                    ">
                        <span style="font-size: 24px; margin-right: 12px;">🔐</span>
                        <h3 style="margin: 0; color: #333;">관리자 인증이 필요합니다</h3>
                    </div>
                    
                    <p style="color: #666; margin-bottom: 20px;">
                        이 작업을 수행하려면 관리자 권한이 필요합니다. 로그인을 해주세요.
                    </p>
                    
                    <div id="authModalError" style="
                        display: none;
                        background: #fff5f5;
                        border: 1px solid #fed7d7;
                        color: #c53030;
                        padding: 12px;
                        border-radius: 4px;
                        margin-bottom: 16px;
                        font-size: 14px;
                    "></div>
                    
                    <form id="authModalForm">
                        <div style="margin-bottom: 16px;">
                            <label style="
                                display: block;
                                margin-bottom: 6px;
                                font-weight: 500;
                                color: #374151;
                            ">사용자명</label>
                            <input 
                                type="text" 
                                id="authModalUsername" 
                                value="admin"
                                style="
                                    width: 100%;
                                    padding: 10px 12px;
                                    border: 1px solid #d1d5db;
                                    border-radius: 4px;
                                    font-size: 14px;
                                    box-sizing: border-box;
                                "
                                required>
                        </div>
                        
                        <div style="margin-bottom: 20px;">
                            <label style="
                                display: block;
                                margin-bottom: 6px;
                                font-weight: 500;
                                color: #374151;
                            ">비밀번호</label>
                            <input 
                                type="password" 
                                id="authModalPassword" 
                                placeholder="비밀번호를 입력하세요"
                                style="
                                    width: 100%;
                                    padding: 10px 12px;
                                    border: 1px solid #d1d5db;
                                    border-radius: 4px;
                                    font-size: 14px;
                                    box-sizing: border-box;
                                "
                                required>
                        </div>
                        
                        <div style="
                            display: flex;
                            gap: 12px;
                            justify-content: flex-end;
                        ">
                            <button 
                                type="button" 
                                id="authModalCancel"
                                style="
                                    padding: 10px 20px;
                                    background: #f3f4f6;
                                    color: #374151;
                                    border: none;
                                    border-radius: 4px;
                                    cursor: pointer;
                                    font-size: 14px;
                                "
                            >취소</button>
                            
                            <button 
                                type="submit" 
                                id="authModalLogin"
                                style="
                                    padding: 10px 20px;
                                    background: #3b82f6;
                                    color: white;
                                    border: none;
                                    border-radius: 4px;
                                    cursor: pointer;
                                    font-size: 14px;
                                "
                            >로그인</button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        
        // 기존 모달이 있으면 제거
        const existingModal = document.getElementById('authModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // 새 모달을 body에 추가
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modalElement = document.getElementById('authModal');
        
        // 이벤트 리스너 설정
        this.setupEventListeners();
    },
    
    // 이벤트 리스너 설정
    setupEventListeners() {
        const form = document.getElementById('authModalForm');
        const cancelBtn = document.getElementById('authModalCancel');
        const passwordInput = document.getElementById('authModalPassword');
        
        // 폼 제출
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.attemptLogin();
        });
        
        // 취소 버튼
        cancelBtn.addEventListener('click', () => {
            this.hide();
        });
        
        // 모달 배경 클릭 시 닫기
        this.modalElement.addEventListener('click', (e) => {
            if (e.target === this.modalElement) {
                this.hide();
            }
        });
        
        // ESC 키로 닫기
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modalElement.style.display !== 'none') {
                this.hide();
            }
        });
        
        // 패스워드 입력 시 포커스
        this.modalElement.addEventListener('show', () => {
            setTimeout(() => passwordInput.focus(), 100);
        });
    },
    
    // 모달 표시
    show(pendingAction = null) {
        this.pendingAction = pendingAction;
        this.modalElement.style.display = 'flex';
        this.clearError();
        
        // 패스워드 필드 초기화 및 포커스
        const passwordInput = document.getElementById('authModalPassword');
        passwordInput.value = '';
        setTimeout(() => passwordInput.focus(), 100);
        
        console.log('[AuthModal] 로그인 모달 표시됨');
    },
    
    // 모달 숨기기
    hide() {
        this.modalElement.style.display = 'none';
        this.pendingAction = null;
        this.clearError();
        console.log('[AuthModal] 로그인 모달 숨김');
    },
    
    // 로그인 시도
    async attemptLogin() {
        const username = document.getElementById('authModalUsername').value;
        const password = document.getElementById('authModalPassword').value;
        const loginBtn = document.getElementById('authModalLogin');
        
        if (!username || !password) {
            this.showError('사용자명과 비밀번호를 모두 입력해주세요.');
            return;
        }
        
        // 로딩 상태
        const originalText = loginBtn.textContent;
        loginBtn.textContent = '로그인 중...';
        loginBtn.disabled = true;
        
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('[AuthModal] 로그인 성공');
                this.hide();
                
                // 대기 중인 작업이 있으면 실행
                if (this.pendingAction) {
                    console.log('[AuthModal] 대기 중인 작업 재시도');
                    try {
                        await this.pendingAction();
                    } catch (error) {
                        console.error('[AuthModal] 재시도 작업 실패:', error);
                    }
                }
            } else {
                this.showError(result.message || '로그인에 실패했습니다.');
            }
        } catch (error) {
            console.error('[AuthModal] 로그인 오류:', error);
            this.showError('로그인 중 오류가 발생했습니다. 다시 시도해주세요.');
        } finally {
            // 로딩 상태 해제
            loginBtn.textContent = originalText;
            loginBtn.disabled = false;
        }
    },
    
    // 오류 메시지 표시
    showError(message) {
        const errorDiv = document.getElementById('authModalError');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    },
    
    // 오류 메시지 지우기
    clearError() {
        const errorDiv = document.getElementById('authModalError');
        errorDiv.style.display = 'none';
        errorDiv.textContent = '';
    }
};

// 전역 함수로 401 오류 처리
window.handleUnauthorized = function(pendingAction) {
    console.log('[AuthModal] 401 Unauthorized 감지, 로그인 모달 표시');
    
    // AuthModal이 초기화되지 않았으면 초기화
    if (!AuthModal.modalElement) {
        AuthModal.init();
    }
    
    AuthModal.show(pendingAction);
};

// 페이지 로드 시 자동 초기화
document.addEventListener('DOMContentLoaded', () => {
    AuthModal.init();
    console.log('[AuthModal] 자동 로그인 모달 초기화 완료');
});