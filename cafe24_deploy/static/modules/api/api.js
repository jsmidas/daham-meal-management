/**
 * 🔌 API 통신 모듈
 *
 * 중앙집중식 API 호출 관리 시스템
 * - CONFIG 기반 동적 URL 생성
 * - 표준화된 에러 처리
 * - 로딩 상태 관리
 * - 메시지 알림 시스템
 */

(function() {
'use strict';

// API 베이스 URL 가져오기
function getApiBaseUrl() {
    return window.CONFIG?.API?.BASE_URL || 'http://127.0.0.1:8009';
}

// API 전체 URL 생성
function buildApiUrl(endpoint) {
    const baseUrl = getApiBaseUrl();

    // endpoint가 전체 URL인 경우 그대로 반환
    if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
        return endpoint;
    }

    // endpoint가 /로 시작하면 baseUrl과 합치기
    if (endpoint.startsWith('/')) {
        return baseUrl + endpoint;
    }

    // 그 외의 경우 /를 추가하여 합치기
    return baseUrl + '/' + endpoint;
}

// API 호출 래퍼 함수
async function apiCall(endpoint, options = {}) {
    const url = buildApiUrl(endpoint);

    const defaultOptions = {
        credentials: 'include', // 쿠키 포함
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    };

    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };

    try {
        console.log(`📡 [API] ${options.method || 'GET'} ${url}`);
        const response = await fetch(url, finalOptions);

        if (!response.ok) {
            const errorData = await response.text();
            console.error(`❌ [API] Error ${response.status}: ${errorData}`);
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            console.log(`✅ [API] Success:`, data);
            return data;
        } else {
            const text = await response.text();
            console.log(`✅ [API] Success (text):`, text);
            return text;
        }
    } catch (error) {
        console.error('❌ [API] 호출 실패:', error);
        throw error;
    }
}

// GET 요청
async function apiGet(endpoint, params = {}) {
    const url = buildApiUrl(endpoint);
    const urlObj = new URL(url);

    Object.keys(params).forEach(key => {
        if (params[key] !== null && params[key] !== undefined) {
            urlObj.searchParams.append(key, params[key]);
        }
    });

    return apiCall(urlObj.toString(), { method: 'GET' });
}

// POST 요청
async function apiPost(endpoint, data = {}) {
    return apiCall(endpoint, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

// PUT 요청
async function apiPut(endpoint, data = {}) {
    return apiCall(endpoint, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

// DELETE 요청
async function apiDelete(endpoint) {
    return apiCall(endpoint, { method: 'DELETE' });
}

// 파일 업로드
async function apiUpload(endpoint, file, additionalData = {}) {
    const url = buildApiUrl(endpoint);
    const formData = new FormData();
    formData.append('file', file);

    Object.keys(additionalData).forEach(key => {
        formData.append(key, additionalData[key]);
    });

    // FormData를 사용할 때는 Content-Type을 설정하지 않음 (브라우저가 자동 설정)
    return fetch(url, {
        method: 'POST',
        body: formData,
        credentials: 'include'
    }).then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    });
}

// 공통 에러 처리
function handleApiError(error, defaultMessage = '처리 중 오류가 발생했습니다.') {
    console.error('API 오류:', error);

    if (error.message.includes('HTTP error!')) {
        const status = error.message.match(/status: (\d+)/)?.[1];
        switch (status) {
            case '400':
                return '잘못된 요청입니다.';
            case '401':
                return '인증이 필요합니다.';
            case '403':
                return '접근 권한이 없습니다.';
            case '404':
                return '요청한 리소스를 찾을 수 없습니다.';
            case '500':
                return '서버 내부 오류가 발생했습니다.';
            default:
                return defaultMessage;
        }
    }

    if (error.message.includes('Failed to fetch')) {
        return '네트워크 연결을 확인해주세요.';
    }

    return defaultMessage;
}

// 로딩 상태 관리
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div style="text-align: center; padding: 20px;">로딩 중...</div>';
    }
}

function hideLoading(elementId, content = '') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = content;
    }
}

// 성공/에러 메시지 표시
function showMessage(message, type = 'info') {
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#007bff'
    };

    const messageDiv = document.createElement('div');
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type] || colors.info};
        color: white;
        padding: 15px 20px;
        border-radius: 5px;
        z-index: 10000;
        font-weight: bold;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        animation: slideIn 0.3s ease-out;
    `;
    messageDiv.textContent = message;

    // 애니메이션 스타일 추가
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);

    document.body.appendChild(messageDiv);

    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.style.animation = 'slideIn 0.3s ease-out reverse';
            setTimeout(() => {
                messageDiv.parentNode.removeChild(messageDiv);
            }, 300);
        }
    }, 3000);
}

// 확인 대화상자
function confirmAction(message, onConfirm, onCancel = null) {
    if (confirm(message)) {
        if (typeof onConfirm === 'function') {
            onConfirm();
        }
    } else {
        if (typeof onCancel === 'function') {
            onCancel();
        }
    }
}

// API 모듈 객체로 정리
window.API = {
    // 기본 메서드
    call: apiCall,
    get: apiGet,
    post: apiPost,
    put: apiPut,
    delete: apiDelete,
    upload: apiUpload,

    // 유틸리티
    handleError: handleApiError,
    showLoading: showLoading,
    hideLoading: hideLoading,
    showMessage: showMessage,
    confirmAction: confirmAction,

    // URL 관련
    getBaseUrl: getApiBaseUrl,
    buildUrl: buildApiUrl
};

// 이전 버전과의 호환성을 위한 전역 함수 유지
window.apiCall = apiCall;
window.apiGet = apiGet;
window.apiPost = apiPost;
window.apiPut = apiPut;
window.apiDelete = apiDelete;
window.apiUpload = apiUpload;
window.handleApiError = handleApiError;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showMessage = showMessage;
window.confirmAction = confirmAction;

console.log('✅ [API Module] 초기화 완료');
console.log(`📡 [API Module] Base URL: ${getApiBaseUrl()}`);

})(); // IIFE 종료