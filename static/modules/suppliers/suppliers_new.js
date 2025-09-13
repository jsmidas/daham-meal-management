/**
 * 협력업체 관리 모듈
 * admin 대시보드용 완전한 협력업체 관리 기능
 */

class SupplierManagement {
    constructor() {
        this.API_BASE_URL = window.CONFIG?.API?.BASE_URL || 'http://127.0.0.1:8015';
        this.currentSupplierId = null;
        this.isEditMode = false;
        this.isLoaded = false;
    }

    async load() {
        if (this.isLoaded) return;
        console.log('🚀 [SupplierManagement] 협력업체 관리 모듈 초기화');

        this.setupEventListeners();
        await this.loadSupplierStats();
        await this.loadSuppliers();

        this.isLoaded = true;
    }

    setupEventListeners() {
        // 검색 입력 시 실시간 검색
        const searchInput = document.getElementById('searchSupplierInput');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => this.loadSuppliers(), 500));
        }

        // 활성 상태 필터 변경 시
        const statusFilter = document.getElementById('supplierStatusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.loadSuppliers());
        }

        // 협력업체 폼 제출
        const supplierForm = document.getElementById('supplierForm');
        if (supplierForm) {
            supplierForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }

        // 모달 외부 클릭 시 닫기
        window.addEventListener('click', (event) => {
            const modal = document.getElementById('supplierModal');
            if (event.target === modal) {
                this.closeModal();
            }
        });
    }

    // 디바운스 함수
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 협력업체 통계 로드
    async loadSupplierStats() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/api/admin/suppliers/stats`);
            if (!response.ok) throw new Error('통계 로드 실패');

            const stats = await response.json();

            const totalSuppliersElement = document.getElementById('totalSuppliers');
            const activeSuppliersElement = document.getElementById('activeSuppliers');

            if (totalSuppliersElement) totalSuppliersElement.textContent = stats.total || '0';
            if (activeSuppliersElement) activeSuppliersElement.textContent = stats.active || '0';
        } catch (error) {
            console.error('협력업체 통계 로드 오류:', error);
            const totalSuppliersElement = document.getElementById('totalSuppliers');
            const activeSuppliersElement = document.getElementById('activeSuppliers');

            if (totalSuppliersElement) totalSuppliersElement.textContent = '오류';
            if (activeSuppliersElement) activeSuppliersElement.textContent = '오류';
        }
    }

    // 협력업체 목록 로드
    async loadSuppliers(page = 1) {
        try {
            this.showLoading(true);

            const search = document.getElementById('searchSupplierInput')?.value || '';
            const status = document.getElementById('supplierStatusFilter')?.value || '';

            const params = new URLSearchParams({
                page: page.toString(),
                per_page: '10'
            });

            if (search) params.append('search', search);
            if (status) params.append('status', status);

            const response = await fetch(`${this.API_BASE_URL}/api/suppliers?${params}`);
            if (!response.ok) throw new Error('협력업체 목록 로드 실패');

            const data = await response.json();

            this.renderSuppliersTable(data.suppliers || []);
            this.renderPagination(data.pagination);

        } catch (error) {
            console.error('협력업체 목록 로드 오류:', error);
            this.showError('협력업체 목록을 불러오는데 실패했습니다.');
        } finally {
            this.showLoading(false);
        }
    }

    // 협력업체 테이블 렌더링
    renderSuppliersTable(suppliers) {
        const tbody = document.getElementById('suppliersTableBody');
        const table = document.getElementById('suppliersTable');
        const emptyState = document.getElementById('supplierEmptyState');

        if (!tbody) return;

        if (!suppliers || suppliers.length === 0) {
            if (table) table.style.display = 'none';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        if (table) table.style.display = 'table';
        if (emptyState) emptyState.style.display = 'none';

        tbody.innerHTML = suppliers.map(supplier => `
            <tr>
                <td>${this.escapeHtml(supplier.name || '')}</td>
                <td>${this.escapeHtml(supplier.parent_code || '')}</td>
                <td>${this.escapeHtml(supplier.business_number || '-')}</td>
                <td>${this.escapeHtml(supplier.representative || '-')}</td>
                <td>${this.escapeHtml(supplier.headquarters_phone || '-')}</td>
                <td>${this.escapeHtml(supplier.email || '-')}</td>
                <td><span class="status-badge status-${supplier.is_active ? 'active' : 'inactive'}">${supplier.is_active ? '활성' : '비활성'}</span></td>
                <td>${this.formatDate(supplier.created_at)}</td>
                <td>
                    <div class="actions">
                        <button class="btn btn-sm btn-primary" onclick="window.supplierManagement.editSupplier(${supplier.id})">수정</button>
                        ${supplier.is_active ?
                            `<button class="btn btn-sm btn-danger" onclick="window.supplierManagement.deactivateSupplier(${supplier.id})">비활성화</button>` :
                            `<button class="btn btn-sm btn-success" onclick="window.supplierManagement.activateSupplier(${supplier.id})">활성화</button>`
                        }
                    </div>
                </td>
            </tr>
        `).join('');
    }

    // 페이지네이션 렌더링
    renderPagination(pagination) {
        const container = document.getElementById('supplierPagination');
        if (!container || !pagination) return;

        let html = '';

        // 이전 페이지 버튼
        html += `<button ${!pagination.has_prev ? 'disabled' : ''} onclick="window.supplierManagement.loadSuppliers(${pagination.current_page - 1})">이전</button>`;

        // 페이지 번호들
        const startPage = Math.max(1, pagination.current_page - 2);
        const endPage = Math.min(pagination.total_pages, pagination.current_page + 2);

        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="${i === pagination.current_page ? 'active' : ''}" onclick="window.supplierManagement.loadSuppliers(${i})">${i}</button>`;
        }

        // 다음 페이지 버튼
        html += `<button ${!pagination.has_next ? 'disabled' : ''} onclick="window.supplierManagement.loadSuppliers(${pagination.current_page + 1})">다음</button>`;

        container.innerHTML = html;
    }

    // 날짜 포맷팅
    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR');
    }

    // HTML 이스케이프
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    // 협력업체 추가 모달 열기
    openCreateModal() {
        this.currentSupplierId = null;
        this.isEditMode = false;

        const modalTitle = document.getElementById('supplierModalTitle');
        const submitBtn = document.getElementById('supplierSubmitBtn');
        const supplierForm = document.getElementById('supplierForm');
        const supplierModal = document.getElementById('supplierModal');

        if (modalTitle) modalTitle.textContent = '협력업체 추가';
        if (submitBtn) submitBtn.textContent = '추가';
        if (supplierForm) supplierForm.reset();
        if (supplierModal) supplierModal.style.display = 'block';
    }

    // 협력업체 수정 모달 열기
    async editSupplier(supplierId) {
        try {
            const response = await fetch(`${this.API_BASE_URL}/api/suppliers/${supplierId}`);
            if (!response.ok) throw new Error('협력업체 정보 로드 실패');

            const supplier = await response.json();

            this.currentSupplierId = supplierId;
            this.isEditMode = true;

            const modalTitle = document.getElementById('supplierModalTitle');
            const submitBtn = document.getElementById('supplierSubmitBtn');
            const supplierModal = document.getElementById('supplierModal');

            if (modalTitle) modalTitle.textContent = '협력업체 수정';
            if (submitBtn) submitBtn.textContent = '수정';

            // 폼에 데이터 채우기
            const nameField = document.getElementById('supplierName');
            const codeField = document.getElementById('supplierCode');
            const businessNumberField = document.getElementById('supplierBusinessNumber');
            const representativeField = document.getElementById('supplierRepresentative');
            const addressField = document.getElementById('supplierAddress');
            const phoneField = document.getElementById('supplierPhone');
            const emailField = document.getElementById('supplierEmail');
            const notesField = document.getElementById('supplierNotes');

            if (nameField) nameField.value = supplier.name || '';
            if (codeField) codeField.value = supplier.parent_code || '';
            if (businessNumberField) businessNumberField.value = supplier.business_number || '';
            if (representativeField) representativeField.value = supplier.representative || '';
            if (addressField) addressField.value = supplier.headquarters_address || '';
            if (phoneField) phoneField.value = supplier.headquarters_phone || '';
            if (emailField) emailField.value = supplier.email || '';
            if (notesField) notesField.value = supplier.notes || '';

            if (supplierModal) supplierModal.style.display = 'block';

        } catch (error) {
            console.error('협력업체 정보 로드 오류:', error);
            this.showError('협력업체 정보를 불러오는데 실패했습니다.');
        }
    }

    // 모달 닫기
    closeModal() {
        const supplierModal = document.getElementById('supplierModal');
        const supplierForm = document.getElementById('supplierForm');

        if (supplierModal) supplierModal.style.display = 'none';
        if (supplierForm) supplierForm.reset();
    }

    // 협력업체 폼 제출
    async handleFormSubmit(e) {
        e.preventDefault();

        const formData = new FormData(e.target);
        const supplierData = {
            name: formData.get('name'),
            parent_code: formData.get('parent_code'),
            business_number: formData.get('business_number'),
            representative: formData.get('representative'),
            headquarters_address: formData.get('headquarters_address'),
            headquarters_phone: formData.get('headquarters_phone'),
            email: formData.get('email'),
            notes: formData.get('notes')
        };

        try {
            const url = this.isEditMode
                ? `${this.API_BASE_URL}/api/suppliers/${this.currentSupplierId}`
                : `${this.API_BASE_URL}/api/suppliers`;

            const method = this.isEditMode ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(supplierData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '요청 처리 실패');
            }

            this.showSuccess(this.isEditMode ? '협력업체가 수정되었습니다.' : '협력업체가 추가되었습니다.');
            this.closeModal();
            await this.loadSuppliers();
            await this.loadSupplierStats();

        } catch (error) {
            console.error('협력업체 저장 오류:', error);
            this.showError(`협력업체 ${this.isEditMode ? '수정' : '추가'}에 실패했습니다: ${error.message}`);
        }
    }

    // 협력업체 비활성화
    async deactivateSupplier(supplierId) {
        if (!confirm('정말로 이 협력업체를 비활성화하시겠습니까?')) {
            return;
        }

        try {
            const response = await fetch(`${this.API_BASE_URL}/api/suppliers/${supplierId}/deactivate`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('비활성화 실패');

            this.showSuccess('협력업체가 비활성화되었습니다.');
            await this.loadSuppliers();
            await this.loadSupplierStats();

        } catch (error) {
            console.error('협력업체 비활성화 오류:', error);
            this.showError('협력업체 비활성화에 실패했습니다.');
        }
    }

    // 협력업체 활성화
    async activateSupplier(supplierId) {
        try {
            const response = await fetch(`${this.API_BASE_URL}/api/suppliers/${supplierId}/activate`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('활성화 실패');

            this.showSuccess('협력업체가 활성화되었습니다.');
            await this.loadSuppliers();
            await this.loadSupplierStats();

        } catch (error) {
            console.error('협력업체 활성화 오류:', error);
            this.showError('협력업체 활성화에 실패했습니다.');
        }
    }

    // 로딩 표시
    showLoading(show) {
        const loadingIndicator = document.getElementById('supplierLoadingIndicator');
        const table = document.getElementById('suppliersTable');

        if (loadingIndicator) {
            loadingIndicator.style.display = show ? 'block' : 'none';
        }
        if (table) {
            table.style.display = show ? 'none' : 'table';
        }
    }

    // 성공 메시지 표시
    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    // 오류 메시지 표시
    showError(message) {
        this.showAlert(message, 'error');
    }

    // 알림 메시지 표시
    showAlert(message, type = 'success') {
        const container = document.getElementById('supplierAlertContainer');
        if (!container) return;

        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;

        container.appendChild(alert);

        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }
}

// 전역 함수들 (onclick 핸들러용)
function openCreateSupplierModal() {
    if (window.supplierManagement) {
        window.supplierManagement.openCreateModal();
    }
}

function closeSupplierModal() {
    if (window.supplierManagement) {
        window.supplierManagement.closeModal();
    }
}

function loadSuppliers() {
    if (window.supplierManagement) {
        window.supplierManagement.loadSuppliers();
    }
}

// 모듈 익스포트
window.SupplierManagement = SupplierManagement;