/**
 * 완전한 협력업체 관리 모듈
 * admin_dashboard.html에 통합하기 위한 버전
 */

(function() {
    'use strict';

    const API_BASE_URL = window.CONFIG?.API?.BASE_URL || 'http://127.0.0.1:8013';
    let currentPage = 1;
    let currentSort = { field: 'created_at', order: 'desc' };
    let selectedSuppliers = new Set();

    window.SuppliersManagementFull = {
        // 모듈 초기화
        async init() {
            console.log('🏢 Full Suppliers Management Module 초기화');
            await this.loadSupplierStats();
            await this.loadSuppliers();
            this.setupEventListeners();
            return this;
        },

        // 이벤트 리스너 설정
        setupEventListeners() {
            // 검색 입력
            const searchInput = document.getElementById('supplierSearchInput');
            if (searchInput) {
                searchInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.loadSuppliers(1);
                    }
                });
            }

            // 전체 선택 체크박스
            const selectAll = document.getElementById('selectAllSuppliers');
            if (selectAll) {
                selectAll.addEventListener('change', (e) => {
                    const checkboxes = document.querySelectorAll('.supplier-checkbox');
                    checkboxes.forEach(cb => {
                        cb.checked = e.target.checked;
                        const supplierId = parseInt(cb.dataset.supplierId);
                        if (e.target.checked) {
                            selectedSuppliers.add(supplierId);
                        } else {
                            selectedSuppliers.delete(supplierId);
                        }
                    });
                    this.updateBulkActions();
                });
            }
        },

        // 협력업체 통계 로드
        async loadSupplierStats() {
            try {
                const response = await fetch(`${API_BASE_URL}/api/suppliers/stats`);
                const data = await response.json();

                if (data.success) {
                    document.getElementById('totalSuppliers').textContent = data.stats.total_suppliers;
                    document.getElementById('activeSuppliers').textContent = data.stats.active_suppliers;
                }
            } catch (error) {
                console.error('통계 로드 실패:', error);
            }
        },

        // 협력업체 목록 로드
        async loadSuppliers(page = 1) {
            try {
                const search = document.getElementById('supplierSearchInput')?.value || '';

                const url = new URL(`${API_BASE_URL}/api/suppliers`);
                url.searchParams.append('page', page);
                url.searchParams.append('limit', 10);
                if (search) url.searchParams.append('search', search);

                const response = await fetch(url);
                const data = await response.json();

                if (data.success) {
                    this.renderSuppliersTable(data.suppliers);
                    this.renderPagination(data.pagination);
                    currentPage = page;
                } else {
                    this.showAlert('협력업체 목록을 불러오는데 실패했습니다: ' + data.error, 'error');
                }
            } catch (error) {
                console.error('협력업체 목록 로드 실패:', error);
                this.showAlert('협력업체 목록을 불러오는데 실패했습니다', 'error');
            }
        },

        // 협력업체 테이블 렌더링
        renderSuppliersTable(suppliers) {
            const tbody = document.getElementById('suppliersTableBody');
            if (!tbody) return;

            if (suppliers.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="9" class="empty-state">
                            <h3>검색 결과가 없습니다</h3>
                            <p>다른 검색 조건을 시도해보세요.</p>
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = suppliers.map(supplier => `
                <tr>
                    <td><input type="checkbox" class="supplier-checkbox" data-supplier-id="${supplier.id}"></td>
                    <td>${supplier.id}</td>
                    <td>
                        <div class="supplier-info">
                            <strong>${supplier.name}</strong>
                            <br>
                            <small>${supplier.code || '-'}</small>
                        </div>
                    </td>
                    <td>${supplier.businessType || '-'}</td>
                    <td>${supplier.representative || '-'}</td>
                    <td>${supplier.phone || '-'}</td>
                    <td>${supplier.email || '-'}</td>
                    <td>
                        <span class="status-badge ${supplier.isActive ? 'active' : 'inactive'}">
                            ${supplier.isActive ? '활성' : '비활성'}
                        </span>
                    </td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn-icon" onclick="SuppliersManagementFull.viewSupplierDetails(${supplier.id})" title="상세보기">
                                📋
                            </button>
                            <button class="btn-icon" onclick="SuppliersManagementFull.editSupplier(${supplier.id})" title="수정">
                                ✏️
                            </button>
                            <button class="btn-icon" onclick="SuppliersManagementFull.toggleSupplierStatus(${supplier.id}, ${!supplier.isActive})" title="상태 변경">
                                ${supplier.isActive ? '⏸️' : '▶️'}
                            </button>
                            <button class="btn-icon btn-danger" onclick="SuppliersManagementFull.deleteSupplier(${supplier.id})" title="삭제">
                                🗑️
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');

            // 체크박스 이벤트 리스너 추가
            document.querySelectorAll('.supplier-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', (e) => {
                    const supplierId = parseInt(e.target.dataset.supplierId);
                    if (e.target.checked) {
                        selectedSuppliers.add(supplierId);
                    } else {
                        selectedSuppliers.delete(supplierId);
                    }
                    this.updateBulkActions();
                });
            });
        },

        // 페이지네이션 렌더링
        renderPagination(pagination) {
            const container = document.getElementById('suppliersPagination');
            if (!container) return;

            let html = '';

            // 이전 페이지 버튼
            html += `<button ${!pagination.has_prev ? 'disabled' : ''} onclick="SuppliersManagementFull.loadSuppliers(${pagination.current_page - 1})">이전</button>`;

            // 페이지 번호들
            const startPage = Math.max(1, pagination.current_page - 2);
            const endPage = Math.min(pagination.total_pages, pagination.current_page + 2);

            for (let i = startPage; i <= endPage; i++) {
                html += `<button class="${i === pagination.current_page ? 'active' : ''}" onclick="SuppliersManagementFull.loadSuppliers(${i})">${i}</button>`;
            }

            // 다음 페이지 버튼
            html += `<button ${!pagination.has_next ? 'disabled' : ''} onclick="SuppliersManagementFull.loadSuppliers(${pagination.current_page + 1})">다음</button>`;

            container.innerHTML = html;
        },

        // 알림 표시
        showAlert(message, type = 'info') {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type}`;
            alertDiv.textContent = message;

            const container = document.querySelector('.content-container') || document.body;
            container.insertBefore(alertDiv, container.firstChild);

            setTimeout(() => alertDiv.remove(), 5000);
        },

        // 벌크 액션 업데이트
        updateBulkActions() {
            const bulkActions = document.getElementById('supplierBulkActions');
            if (bulkActions) {
                bulkActions.style.display = selectedSuppliers.size > 0 ? 'flex' : 'none';
                const selectedCount = document.getElementById('supplierSelectedCount');
                if (selectedCount) {
                    selectedCount.textContent = selectedSuppliers.size;
                }
            }
        },

        // 협력업체 상세보기
        async viewSupplierDetails(supplierId) {
            console.log('협력업체 상세보기:', supplierId);
            // 상세보기 모달 표시
            this.showSupplierModal(supplierId, 'view');
        },

        // 협력업체 편집
        async editSupplier(supplierId) {
            console.log('협력업체 편집:', supplierId);
            this.showSupplierModal(supplierId, 'edit');
        },

        // 협력업체 모달 표시
        showSupplierModal(supplierId, mode) {
            const modalHtml = `
                <div id="supplierModal" class="modal">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h2>${mode === 'edit' ? '협력업체 수정' : mode === 'view' ? '협력업체 상세' : '새 협력업체 추가'}</h2>
                            <button class="close-btn" onclick="SuppliersManagementFull.closeModal()">×</button>
                        </div>
                        <div class="modal-body">
                            <form id="supplierForm">
                                <div class="form-group">
                                    <label>업체명</label>
                                    <input type="text" id="supplierName" ${mode === 'view' ? 'readonly' : ''} required>
                                </div>
                                <div class="form-group">
                                    <label>업체코드</label>
                                    <input type="text" id="supplierCode" ${mode === 'view' ? 'readonly' : ''}>
                                </div>
                                <div class="form-group">
                                    <label>사업자번호</label>
                                    <input type="text" id="businessNumber" ${mode === 'view' ? 'readonly' : ''}>
                                </div>
                                <div class="form-group">
                                    <label>업종</label>
                                    <input type="text" id="businessType" ${mode === 'view' ? 'readonly' : ''}>
                                </div>
                                <div class="form-group">
                                    <label>대표자</label>
                                    <input type="text" id="representative" ${mode === 'view' ? 'readonly' : ''}>
                                </div>
                                <div class="form-group">
                                    <label>연락처</label>
                                    <input type="tel" id="phone" ${mode === 'view' ? 'readonly' : ''}>
                                </div>
                                <div class="form-group">
                                    <label>이메일</label>
                                    <input type="email" id="email" ${mode === 'view' ? 'readonly' : ''}>
                                </div>
                                ${mode !== 'view' ? `
                                <div class="form-actions">
                                    <button type="submit" class="btn btn-primary">저장</button>
                                    <button type="button" class="btn btn-secondary" onclick="SuppliersManagementFull.closeModal()">취소</button>
                                </div>
                                ` : `
                                <div class="form-actions">
                                    <button type="button" class="btn btn-secondary" onclick="SuppliersManagementFull.closeModal()">닫기</button>
                                </div>
                                `}
                            </form>
                        </div>
                    </div>
                </div>
            `;

            // 기존 모달 제거
            const existingModal = document.getElementById('supplierModal');
            if (existingModal) existingModal.remove();

            // 새 모달 추가
            document.body.insertAdjacentHTML('beforeend', modalHtml);

            // 데이터 로드 (편집/상세보기의 경우)
            if (supplierId && (mode === 'edit' || mode === 'view')) {
                // TODO: API에서 협력업체 정보 로드
                this.showAlert(`협력업체 ${supplierId} 정보 로드 기능 준비 중`, 'info');
            }
        },

        // 모달 닫기
        closeModal() {
            const modal = document.getElementById('supplierModal');
            if (modal) modal.remove();
        },

        // 협력업체 상태 토글
        async toggleSupplierStatus(supplierId, newStatus) {
            const statusText = newStatus ? '활성화' : '비활성화';
            if (!confirm(`협력업체를 ${statusText}하시겠습니까?`)) return;

            try {
                const response = await fetch(`${API_BASE_URL}/api/suppliers/${supplierId}/status`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ isActive: newStatus })
                });

                const result = await response.json();
                if (result.success) {
                    this.showAlert(`협력업체가 ${statusText}되었습니다.`, 'success');
                    this.loadSuppliers(currentPage);
                } else {
                    this.showAlert(`상태 변경 실패: ${result.error}`, 'error');
                }
            } catch (error) {
                console.error('상태 변경 오류:', error);
                this.showAlert('상태 변경 중 오류가 발생했습니다.', 'error');
            }
        },

        // 협력업체 삭제
        async deleteSupplier(supplierId) {
            if (!confirm('정말로 이 협력업체를 삭제하시겠습니까?')) return;

            try {
                const response = await fetch(`${API_BASE_URL}/api/suppliers/${supplierId}`, {
                    method: 'DELETE'
                });

                const result = await response.json();
                if (result.success !== false) {
                    this.showAlert('협력업체가 삭제되었습니다.', 'success');
                    this.loadSuppliers(currentPage);
                } else {
                    this.showAlert(`삭제 실패: ${result.error}`, 'error');
                }
            } catch (error) {
                console.error('삭제 오류:', error);
                this.showAlert('삭제 중 오류가 발생했습니다.', 'error');
            }
        },

        // 선택된 협력업체 벌크 삭제
        async bulkDelete() {
            if (!confirm(`선택한 ${selectedSuppliers.size}개의 협력업체를 삭제하시겠습니까?`)) return;

            try {
                const response = await fetch(`${API_BASE_URL}/api/suppliers/bulk-delete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ supplierIds: Array.from(selectedSuppliers) })
                });

                const result = await response.json();
                if (result.success) {
                    this.showAlert(`${result.deleted}개의 협력업체가 삭제되었습니다.`, 'success');
                    selectedSuppliers.clear();
                    this.updateBulkActions();
                    this.loadSuppliers(1);
                } else {
                    this.showAlert(`벌크 삭제 실패: ${result.error}`, 'error');
                }
            } catch (error) {
                console.error('벌크 삭제 오류:', error);
                this.showAlert('벌크 삭제 중 오류가 발생했습니다.', 'error');
            }
        },

        // 새 협력업체 추가 모달 표시
        showAddSupplierModal() {
            console.log('새 협력업체 추가 모달');
            this.showSupplierModal(null, 'add');
        }
    };

    console.log('🏢 Full Suppliers Management Module 정의 완료');

})();