/**
 * Excel 구조 그대로 식자재 관리 모듈
 * - Excel 컬럼명 그대로 한글 필드 사용
 * - 여유 컬럼 3개 포함
 */

class IngredientsExcelManager {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 50;
        this.searchTerm = '';
        this.selectedCategory = '';
        this.isLoading = false;
        this.init();
    }

    init() {
        console.log('Excel 식자재 관리 모듈 초기화');
        this.setupEventListeners();
        this.loadIngredients();
    }

    setupEventListeners() {
        // 검색 기능
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchTerm = e.target.value;
                this.debounceSearch();
            });
        }

        // 카테고리 필터
        const categorySelect = document.getElementById('category-select');
        if (categorySelect) {
            categorySelect.addEventListener('change', (e) => {
                this.selectedCategory = e.target.value;
                this.currentPage = 1;
                this.loadIngredients();
            });
        }

        // 업로드 관련
        const fileInput = document.getElementById('file-upload');
        const uploadBtn = document.getElementById('upload-btn');
        const startUploadBtn = document.getElementById('start-upload-btn');

        if (fileInput && uploadBtn) {
            uploadBtn.addEventListener('click', () => fileInput.click());
        }

        if (fileInput) {
            fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        }

        if (startUploadBtn) {
            startUploadBtn.addEventListener('click', this.uploadFile.bind(this));
        }

        // 페이지네이션
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('page-btn')) {
                const page = parseInt(e.target.dataset.page);
                if (page !== this.currentPage) {
                    this.currentPage = page;
                    this.loadIngredients();
                }
            }
        });
    }

    debounceSearch() {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.currentPage = 1;
            this.loadIngredients();
        }, 300);
    }

    async loadIngredients() {
        if (this.isLoading) return;
        
        try {
            this.isLoading = true;
            this.showLoadingState();

            const params = new URLSearchParams({
                page: this.currentPage,
                size: this.pageSize
            });

            if (this.searchTerm) {
                params.append('search', this.searchTerm);
            }

            if (this.selectedCategory) {
                params.append('category', this.selectedCategory);
            }

            const response = await fetch(`/api/admin/ingredients-excel?${params}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success) {
                this.displayIngredients(result.data.ingredients);
                this.displayPagination(result.data.pagination);
                this.updateSummary(result.data.pagination);
            } else {
                throw new Error(result.message || '데이터 로딩 실패');
            }

        } catch (error) {
            console.error('식자재 로딩 오류:', error);
            this.showError('식자재 데이터를 불러올 수 없습니다.');
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }

    displayIngredients(ingredients) {
        const tbody = document.querySelector('#ingredients-table tbody');
        if (!tbody) return;

        if (!ingredients || ingredients.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="12" class="text-center text-muted py-4">
                        검색 결과가 없습니다.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = ingredients.map(ingredient => `
            <tr>
                <td>${ingredient.id}</td>
                <td>${ingredient.분류_대분류 || '-'}</td>
                <td>${ingredient.기본식자재_세분류 || '-'}</td>
                <td class="font-monospace">${ingredient.고유코드 || '-'}</td>
                <td class="fw-medium">${ingredient.식자재명 || '-'}</td>
                <td>${ingredient.단위 || '-'}</td>
                <td>${ingredient.과세 || '-'}</td>
                <td class="text-end">${ingredient.입고가 ? ingredient.입고가.toLocaleString() : '-'}</td>
                <td class="text-end">${ingredient.판매가 ? ingredient.판매가.toLocaleString() : '-'}</td>
                <td>${ingredient.판매처명 || '-'}</td>
            </tr>
        `).join('');
    }

    displayPagination(pagination) {
        const paginationContainer = document.getElementById('pagination');
        if (!paginationContainer) return;

        const { current_page, total_pages, total_count } = pagination;
        
        let paginationHTML = '';
        
        if (total_pages > 1) {
            // 이전 페이지
            if (current_page > 1) {
                paginationHTML += `
                    <button class="btn btn-outline-primary btn-sm page-btn" data-page="${current_page - 1}">
                        이전
                    </button>
                `;
            }

            // 페이지 번호들
            const startPage = Math.max(1, current_page - 2);
            const endPage = Math.min(total_pages, current_page + 2);

            if (startPage > 1) {
                paginationHTML += `<button class="btn btn-outline-secondary btn-sm page-btn" data-page="1">1</button>`;
                if (startPage > 2) {
                    paginationHTML += `<span class="px-2">...</span>`;
                }
            }

            for (let i = startPage; i <= endPage; i++) {
                const isActive = i === current_page ? 'btn-primary' : 'btn-outline-secondary';
                paginationHTML += `
                    <button class="btn ${isActive} btn-sm page-btn" data-page="${i}">
                        ${i}
                    </button>
                `;
            }

            if (endPage < total_pages) {
                if (endPage < total_pages - 1) {
                    paginationHTML += `<span class="px-2">...</span>`;
                }
                paginationHTML += `<button class="btn btn-outline-secondary btn-sm page-btn" data-page="${total_pages}">${total_pages}</button>`;
            }

            // 다음 페이지
            if (current_page < total_pages) {
                paginationHTML += `
                    <button class="btn btn-outline-primary btn-sm page-btn" data-page="${current_page + 1}">
                        다음
                    </button>
                `;
            }
        }

        paginationContainer.innerHTML = paginationHTML;
    }

    updateSummary(pagination) {
        const summaryElement = document.getElementById('ingredients-summary');
        if (summaryElement) {
            const { total_count, current_page, page_size } = pagination;
            const startItem = (current_page - 1) * page_size + 1;
            const endItem = Math.min(current_page * page_size, total_count);
            
            summaryElement.textContent = `전체 ${total_count.toLocaleString()}건 중 ${startItem}-${endItem}건 표시`;
        }
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        const selectedFileDiv = document.getElementById('selected-file');
        const startUploadBtn = document.getElementById('start-upload-btn');

        if (file) {
            // 파일 형식 체크
            const allowedTypes = ['.xlsx', '.xls'];
            const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
            
            if (!allowedTypes.includes(fileExtension)) {
                this.showError('Excel 파일(.xlsx, .xls)만 업로드 가능합니다.');
                event.target.value = '';
                return;
            }

            if (selectedFileDiv) {
                selectedFileDiv.innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas fa-file-excel"></i>
                        <strong>${file.name}</strong>
                        <small class="text-muted">(${this.formatFileSize(file.size)})</small>
                        <button type="button" class="btn btn-sm btn-outline-danger ms-2" onclick="this.clearFileSelection()">
                            제거
                        </button>
                    </div>
                `;
            }

            if (startUploadBtn) {
                startUploadBtn.disabled = false;
            }
        }
    }

    clearFileSelection() {
        const fileInput = document.getElementById('file-upload');
        const selectedFileDiv = document.getElementById('selected-file');
        const startUploadBtn = document.getElementById('start-upload-btn');

        if (fileInput) fileInput.value = '';
        if (selectedFileDiv) selectedFileDiv.innerHTML = '';
        if (startUploadBtn) startUploadBtn.disabled = true;
    }

    async uploadFile() {
        const fileInput = document.getElementById('file-upload');
        const file = fileInput.files[0];

        if (!file) {
            this.showError('업로드할 파일을 선택해주세요.');
            return;
        }

        try {
            const formData = new FormData();
            formData.append('file', file);

            // 업로드 진행 상태 표시
            this.showUploadProgress();

            const response = await fetch('http://localhost:9000/api/admin/ingredients-excel-upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.showSuccess(`
                    업로드 완료!<br>
                    • 전체: ${result.data.total_rows}건<br>
                    • 신규: ${result.data.new_count}건<br>
                    • 업데이트: ${result.data.updated_count}건<br>
                    • 오류: ${result.data.error_count}건
                `);
                
                // 파일 선택 초기화
                this.clearFileSelection();
                
                // 데이터 새로고침
                this.loadIngredients();
                
                // 히스토리도 갱신 (있다면)
                if (typeof this.loadUploadHistory === 'function') {
                    this.loadUploadHistory();
                }

            } else {
                throw new Error(result.message || '업로드 실패');
            }

        } catch (error) {
            console.error('업로드 오류:', error);
            this.showError(`업로드 중 오류가 발생했습니다: ${error.message}`);
        } finally {
            this.hideUploadProgress();
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showLoadingState() {
        const tableBody = document.querySelector('#ingredients-table tbody');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="12" class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">로딩중...</span>
                        </div>
                        <div class="mt-2">데이터를 불러오는 중...</div>
                    </td>
                </tr>
            `;
        }
    }

    hideLoadingState() {
        // loadingState는 displayIngredients에서 자동으로 교체됨
    }

    showUploadProgress() {
        const startUploadBtn = document.getElementById('start-upload-btn');
        if (startUploadBtn) {
            startUploadBtn.disabled = true;
            startUploadBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status"></span>
                업로드 중...
            `;
        }
    }

    hideUploadProgress() {
        const startUploadBtn = document.getElementById('start-upload-btn');
        if (startUploadBtn) {
            startUploadBtn.disabled = false;
            startUploadBtn.innerHTML = '업로드 시작';
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // 기존 알림 제거
        const existing = document.querySelector('.notification-toast');
        if (existing) {
            existing.remove();
        }

        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} notification-toast position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div>${message}</div>
                <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;

        document.body.appendChild(notification);

        // 5초 후 자동 제거
        setTimeout(() => {
            if (notification && notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // Excel 식자재 관리자 초기화
    if (document.getElementById('ingredients-table')) {
        window.ingredientsExcelManager = new IngredientsExcelManager();
    }
});