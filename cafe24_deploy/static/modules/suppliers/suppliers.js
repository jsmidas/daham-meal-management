/**
 * 협력업체 관리 모듈
 * admin 대시보드용 완전한 협력업체 관리 기능
 */

(function() {
'use strict';

// 관리자 대시보드와 호환성을 위해 두 이름 모두 지원
window.SupplierManagement = window.SuppliersModule = {
    API_BASE_URL: 'http://127.0.0.1:8010',
    currentSupplierId: null,
    isEditMode: false,
    isLoaded: false,

    // 모듈 초기화
    async init() {
        console.log('🚀 [SupplierManagement] 협력업체 관리 모듈 초기화');
        await this.load();
        return this;
    },

    async load() {
        if (this.isLoaded) return;
        console.log('🚀 [SupplierManagement] 협력업체 관리 모듈 로드');

        // CONFIG 설정 확인
        if (window.CONFIG?.API?.BASE_URL) {
            this.API_BASE_URL = window.CONFIG.API.BASE_URL;
        }

        // 페이지 컨텐츠 영역에 협력업체 관리 HTML 구조 생성
        await this.renderSupplierManagementHTML();

        this.setupEventListeners();
        await this.loadSupplierStats();
        await this.loadSuppliers();

        this.isLoaded = true;
    },

    setupEventListeners() {
        // 검색 입력 시 실시간 검색
        const searchInput = document.getElementById('searchSupplierInput');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => this.loadSuppliers(), 500));
        }

        // 모달 외부 클릭 시 닫기
        const modal = document.getElementById('supplierModal');
        if (modal) {
            modal.addEventListener('click', function(event) {
                if (event.target === modal) {
                    closeSupplierModal();
                }
            });
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
    },

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
    },

    // 협력업체 통계 로드
    async loadSupplierStats() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/api/admin/suppliers/stats`);
            if (!response.ok) throw new Error('통계 로드 실패');

            const data = await response.json();

            const totalSuppliersElement = document.getElementById('totalSuppliers');
            const activeSuppliersElement = document.getElementById('activeSuppliers');

            if (totalSuppliersElement) totalSuppliersElement.textContent = data.total || data.stats?.total_suppliers || '0';
            if (activeSuppliersElement) activeSuppliersElement.textContent = data.active || data.stats?.active_suppliers || '0';
        } catch (error) {
            console.error('협력업체 통계 로드 오류:', error);
            const totalSuppliersElement = document.getElementById('totalSuppliers');
            const activeSuppliersElement = document.getElementById('activeSuppliers');

            if (totalSuppliersElement) totalSuppliersElement.textContent = '오류';
            if (activeSuppliersElement) activeSuppliersElement.textContent = '오류';
        }
    },

    // 협력업체 목록 로드
    async loadSuppliers(page = 1) {
        try {
            this.showLoading(true);

            const search = document.getElementById('searchSupplierInput')?.value || '';
            const status = document.getElementById('supplierStatusFilter')?.value || '';

            const params = new URLSearchParams({
                page: page.toString(),
                limit: '10'
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
    },

    // 협력업체 테이블 렌더링
    renderSuppliersTable(suppliers) {
        const tbody = document.getElementById('suppliersTableBody');
        const table = document.getElementById('suppliersTable');
        const emptyState = document.getElementById('supplierEmptyState');

        if (!tbody) return;

        // API에서 받은 실제 데이터 사용
        const displaySuppliers = suppliers;

        if (!displaySuppliers || displaySuppliers.length === 0) {
            if (table) table.style.display = 'none';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        if (table) table.style.display = 'table';
        if (emptyState) emptyState.style.display = 'none';

        tbody.innerHTML = displaySuppliers.map(supplier => `
            <tr>
                <td>${this.escapeHtml(supplier.name || '')}</td>
                <td>${this.escapeHtml(supplier.parent_code || supplier.code || '')}</td>
                <td>${this.escapeHtml(supplier.business_number || supplier.businessNumber || '-')}</td>
                <td>${this.escapeHtml(supplier.representative || '-')}</td>
                <td>${this.escapeHtml(supplier.headquarters_phone || supplier.phone || '-')}</td>
                <td>${this.escapeHtml(supplier.email || '-')}</td>
                <td><span class="status-badge status-${supplier.is_active !== false ? 'active' : 'inactive'}">${supplier.is_active !== false ? '활성' : '비활성'}</span></td>
                <td>${this.formatDate(supplier.created_at || supplier.createdAt)}</td>
                <td>
                    <div class="actions">
                        <button class="btn btn-sm btn-primary" onclick="editSupplier(${supplier.id})">수정</button>
                        ${supplier.is_active !== false ?
                            `<button class="btn btn-sm btn-danger" onclick="window.supplierManagement.deactivateSupplier(${supplier.id})">비활성화</button>` :
                            `<button class="btn btn-sm btn-success" onclick="window.supplierManagement.activateSupplier(${supplier.id})">활성화</button>`
                        }
                    </div>
                </td>
            </tr>
        `).join('');
    },

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
    },

    // 날짜 포맷팅
    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR');
    },

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
    },

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
    },

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
    },

    // 모달 닫기
    closeModal() {
        const supplierModal = document.getElementById('supplierModal');
        const supplierForm = document.getElementById('supplierForm');

        if (supplierModal) supplierModal.style.display = 'none';
        if (supplierForm) supplierForm.reset();
    },

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

            // 사용자 친화적인 오류 메시지 처리
            let errorMessage = error.message;

            if (errorMessage.includes('사업자번호')) {
                errorMessage = '사업자번호가 중복됩니다. 다른 번호를 입력하거나 비워두세요.';
            } else if (errorMessage.includes('협력업체 이름')) {
                errorMessage = '협력업체명이 중복됩니다. 다른 이름을 사용해 주세요.';
            }

            this.showError(`협력업체 ${this.isEditMode ? '수정' : '추가'} 실패: ${errorMessage}`);
        }
    },

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
    },

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
    },

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
    },

    // 성공 메시지 표시
    showSuccess(message) {
        this.showAlert(message, 'success');
    },

    // 오류 메시지 표시
    showError(message) {
        this.showAlert(message, 'error');
    },

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
    },

    // 협력업체 관리 HTML 구조 생성
    async renderSupplierManagementHTML() {
        // suppliers-content가 이미 HTML에 있는지 확인
        let suppliersContent = document.getElementById('suppliers-content');
        if (!suppliersContent) {
            console.error('suppliers-content element not found');
            return;
        }

        const supplierHTML = `
            <div class="supplier-management-container">

                    <!-- 알림 컨테이너 -->
                    <div id="supplierAlertContainer"></div>

                    <!-- 통계 카드들 -->
                    <div class="dashboard-grid" style="margin-bottom: 2rem;">
                        <div class="dashboard-card">
                            <div class="card-header">
                                <span class="icon">🚛</span>
                                <h3 class="card-title">전체 협력업체</h3>
                            </div>
                            <div class="card-content">
                                <div class="stat-number" id="totalSuppliers">-</div>
                                <div class="stat-label">등록된 협력업체 수</div>
                            </div>
                        </div>

                        <div class="dashboard-card">
                            <div class="card-header">
                                <span class="icon">✅</span>
                                <h3 class="card-title">활성 협력업체</h3>
                            </div>
                            <div class="card-content">
                                <div class="stat-number" id="activeSuppliers">-</div>
                                <div class="stat-label">현재 활성 상태</div>
                            </div>
                        </div>
                    </div>

                    <!-- 컨트롤 패널 -->
                    <div class="controls">
                        <div class="search-container">
                            <input type="text" id="searchSupplierInput" placeholder="협력업체명, 코드, 사업자번호로 검색...">
                        </div>

                        <div class="filter-container">
                            <select id="supplierStatusFilter">
                                <option value="">전체 상태</option>
                                <option value="active">활성</option>
                                <option value="inactive">비활성</option>
                            </select>

                            <button class="btn btn-primary" onclick="openCreateSupplierModal()">
                                + 협력업체 추가
                            </button>
                        </div>
                    </div>

                    <!-- 로딩 인디케이터 -->
                    <div id="supplierLoadingIndicator" class="loading-indicator" style="display: none;">
                        <div class="spinner"></div>
                        <p>데이터를 불러오는 중...</p>
                    </div>

                    <!-- 협력업체 테이블 -->
                    <div class="data-table">
                        <table id="suppliersTable">
                            <thead>
                                <tr>
                                    <th>업체명</th>
                                    <th>업체코드</th>
                                    <th>사업자번호</th>
                                    <th>대표자</th>
                                    <th>전화번호</th>
                                    <th>이메일</th>
                                    <th>상태</th>
                                    <th>등록일</th>
                                    <th>작업</th>
                                </tr>
                            </thead>
                            <tbody id="suppliersTableBody">
                                <!-- 동적으로 생성됨 -->
                            </tbody>
                        </table>
                    </div>

                    <!-- 빈 상태 -->
                    <div id="supplierEmptyState" class="empty-state" style="display: none;">
                        <div class="icon">🚛</div>
                        <h3>등록된 협력업체가 없습니다</h3>
                        <p>새로운 협력업체를 추가해보세요.</p>
                        <button class="btn btn-primary" onclick="openCreateSupplierModal()">
                            첫 번째 협력업체 추가
                        </button>
                    </div>

                    <!-- 페이지네이션 -->
                    <div id="supplierPagination" class="pagination"></div>
                </div>
            </div>

            <!-- 협력업체 추가/수정 모달 -->
            <style>
                #supplierModal .modal-content {
                    max-height: 70vh !important;
                    margin: 3% auto !important;
                    width: 450px !important;
                }
                #supplierModal .modal-header {
                    padding: 6px 10px !important;
                }
                #supplierModal .modal-header h3 {
                    font-size: 15px !important;
                    margin: 0;
                }
                #supplierModal .modal-body {
                    padding: 8px 10px !important;
                    max-height: calc(70vh - 80px) !important;
                    overflow-y: auto !important;
                }
                #supplierModal .modal-footer {
                    padding: 6px 10px !important;
                    text-align: right;
                }
                #supplierModal .form-group {
                    margin-bottom: 4px !important;
                }
                #supplierModal .form-group label {
                    margin-bottom: 1px !important;
                    font-size: 11px !important;
                    display: block;
                }
                #supplierModal input,
                #supplierModal textarea {
                    padding: 3px 6px !important;
                    font-size: 11px !important;
                    height: 24px !important;
                    width: 100%;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                }
                #supplierModal textarea {
                    height: 40px !important;
                    resize: vertical;
                }
                #supplierModal .btn {
                    padding: 4px 10px !important;
                    font-size: 12px !important;
                }
                #supplierModal .close {
                    font-size: 18px !important;
                    line-height: 14px !important;
                }
            </style>
            <div id="supplierModal" class="modal" onclick="if(event.target === this) return false;">
                <div class="modal-content" onmousedown="event.stopPropagation();">
                    <div class="modal-header">
                        <h3 id="supplierModalTitle">협력업체 추가</h3>
                        <span class="close" onclick="closeSupplierModal()">&times;</span>
                    </div>

                    <div class="modal-body">
                        <form id="supplierForm">
                            <div class="form-group">
                                <label for="supplierName">업체명 *</label>
                                <input type="text" id="supplierName" name="name" required>
                            </div>

                            <div class="form-group">
                                <label for="supplierCode">업체코드</label>
                                <input type="text" id="supplierCode" name="parent_code">
                            </div>

                            <div class="form-group">
                                <label for="supplierBusinessNumber">사업자번호</label>
                                <input type="text" id="supplierBusinessNumber" name="business_number">
                            </div>

                            <div class="form-group">
                                <label for="supplierRepresentative">대표자</label>
                                <input type="text" id="supplierRepresentative" name="representative">
                            </div>

                            <div class="form-group">
                                <label for="supplierAddress">주소</label>
                                <input type="text" id="supplierAddress" name="headquarters_address">
                            </div>

                            <div class="form-group">
                                <label for="supplierPhone">전화번호</label>
                                <input type="tel" id="supplierPhone" name="headquarters_phone">
                            </div>

                            <div class="form-group">
                                <label for="supplierEmail">이메일</label>
                                <input type="email" id="supplierEmail" name="email">
                            </div>

                            <div class="form-group">
                                <label for="supplierNotes">비고</label>
                                <textarea id="supplierNotes" name="notes"></textarea>
                            </div>
                        </form>
                    </div>

                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="closeSupplierModal()">취소</button>
                        <button type="button" class="btn btn-primary" onclick="saveSupplierWithoutAlert()">저장</button>
                    </div>
                </div>
            </div>
        `;

        // suppliers-content 영역에만 내용을 추가
        suppliersContent.innerHTML = supplierHTML;
    },
};

console.log('🚀 Complete Supplier Management Module 정의 완료');

// 전역 함수들 (onclick 핸들러용)
window.openCreateSupplierModal = function() {
    if (window.SupplierManagement) {
        window.SupplierManagement.openCreateModal();
    }
};

window.closeSupplierModal = function() {
    const modal = document.getElementById('supplierModal');
    if (modal) {
        modal.style.display = 'none';
        // 폼 초기화
        const form = document.getElementById('supplierForm');
        if (form) form.reset();
        // 상태 초기화
        if (window.SupplierManagement) {
            window.SupplierManagement.isEditMode = false;
            window.SupplierManagement.currentSupplierId = null;
        }
    }
};

window.loadSuppliers = function() {
    if (window.SupplierManagement) {
        window.SupplierManagement.loadSuppliers();
    }
};

window.saveSupplierWithoutAlert = function() {
    console.log('Save supplier without alert');
    if (window.SupplierManagement) {
        const form = document.getElementById('supplierForm');
        if (!form) return;

        // 필드명 매핑 수정
        const supplierData = {
            name: document.getElementById('supplierName').value,
            parent_code: document.getElementById('supplierCode').value,
            business_number: document.getElementById('supplierBusinessNumber').value,
            representative: document.getElementById('supplierRepresentative').value,
            headquarters_address: document.getElementById('supplierAddress').value,
            headquarters_phone: document.getElementById('supplierPhone').value,
            email: document.getElementById('supplierEmail').value,
            notes: document.getElementById('supplierNotes').value
        };

        console.log('Supplier data to save:', supplierData);
        console.log('Edit mode:', window.SupplierManagement.isEditMode);
        console.log('Current supplier ID:', window.SupplierManagement.currentSupplierId);

        const url = window.SupplierManagement.isEditMode
            ? `${window.SupplierManagement.API_BASE_URL}/api/suppliers/${window.SupplierManagement.currentSupplierId}`
            : `${window.SupplierManagement.API_BASE_URL}/api/suppliers`;

        const method = window.SupplierManagement.isEditMode ? 'PUT' : 'POST';

        console.log('Request URL:', url);
        console.log('Request method:', method);

        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(supplierData)
        })
        .then(res => {
            console.log('Response status:', res.status);
            if (!res.ok) {
                return res.json().then(data => {
                    throw new Error(data.detail || data.error || '알 수 없는 오류');
                });
            }
            return res.json();
        })
        .then(data => {
            console.log('Response data:', data);
            // API 응답 성공 시 모달 닫고 목록 새로고침
            closeSupplierModal();
            window.SupplierManagement.loadSuppliers();
            window.SupplierManagement.loadSupplierStats();
        })
        .catch(err => {
            console.error('Save error:', err);

            // 사용자 친화적인 오류 메시지
            let errorMessage = err.message || '저장 중 오류가 발생했습니다.';

            // 사업자번호 중복 오류 처리
            if (errorMessage.includes('사업자번호')) {
                errorMessage = '📝 사업자번호 중복 오류\n\n' +
                    '동일한 사업자번호가 이미 등록되어 있습니다.\n' +
                    '해결 방법:\n' +
                    '1. 다른 사업자번호를 입력하거나\n' +
                    '2. 사업자번호를 비워두세요';
            }
            // 협력업체명 중복 오류 처리
            else if (errorMessage.includes('협력업체 이름')) {
                errorMessage = '🏪 협력업체명 중복 오류\n\n' +
                    '동일한 협력업체명이 이미 등록되어 있습니다.\n' +
                    '다른 이름을 사용해 주세요.';
            }
            // UNIQUE constraint 오류 처리
            else if (errorMessage.includes('UNIQUE constraint')) {
                errorMessage = '⚠️ 중복 데이터 오류\n\n' +
                    '입력하신 정보 중 중복된 값이 있습니다.\n' +
                    '사업자번호나 협력업체명을 확인해 주세요.';
            }

            alert(errorMessage);
        });
    }
};

window.editSupplier = function(supplierId) {
    console.log('Edit supplier called:', supplierId);
    if (window.SupplierManagement) {
        // API를 통해 협력업체 정보 가져오기
        window.SupplierManagement.editSupplier(supplierId);
    }
};

})(); // IIFE 종료