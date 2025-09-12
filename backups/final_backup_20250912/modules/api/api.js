// 공통 API 호출 유틸리티
(function() {
'use strict';

// API 호출 래퍼 함수
async function apiCall(url, options = {}) {
    const defaultOptions = {
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
        const response = await fetch(url, finalOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        } else {
            return await response.text();
        }
    } catch (error) {
        console.error('API 호출 실패:', error);
        throw error;
    }
}

// GET 요청
async function apiGet(url, params = {}) {
    const urlObj = new URL(url, window.location.origin);
    Object.keys(params).forEach(key => {
        if (params[key] !== null && params[key] !== undefined) {
            urlObj.searchParams.append(key, params[key]);
        }
    });
    
    return apiCall(urlObj.toString(), { method: 'GET' });
}

// POST 요청
async function apiPost(url, data = {}) {
    return apiCall(url, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

// PUT 요청
async function apiPut(url, data = {}) {
    return apiCall(url, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

// DELETE 요청
async function apiDelete(url) {
    return apiCall(url, { method: 'DELETE' });
}

// 파일 업로드
async function apiUpload(url, file, additionalData = {}) {
    const formData = new FormData();
    formData.append('file', file);
    
    Object.keys(additionalData).forEach(key => {
        formData.append(key, additionalData[key]);
    });
    
    return apiCall(url, {
        method: 'POST',
        body: formData,
        headers: {} // Content-Type을 자동으로 설정하도록 빈 객체
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
    `;
    messageDiv.textContent = message;
    
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
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

// 전역 함수로 내보내기
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

})(); // IIFE 종료