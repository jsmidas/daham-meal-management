/**
 * 완전한 사용자 관리 모듈 (user_management.html에서 검증된 버전)
 * admin_dashboard.html에 통합하기 위한 버전
 */

(function() {
    'use strict';

    const API_BASE_URL = window.CONFIG?.API?.BASE_URL || 'http://127.0.0.1:8010';
    let currentPage = 1;
    let currentSort = { field: 'created_at', order: 'desc' };
    let selectedUsers = new Set();

    window.UsersManagementFull = {
        // 모듈 초기화
        async init() {
            console.log('👥 Full Users Management Module 초기화');
            await this.loadUserStats();
            await this.loadUsers();
            this.setupEventListeners();
            return this;
        },

        // 이벤트 리스너 설정
        setupEventListeners() {
            // 검색 입력
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                searchInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.loadUsers(1);
                    }
                });
            }

            // 역할 필터
            const roleFilter = document.getElementById('roleFilter');
            if (roleFilter) {
                roleFilter.addEventListener('change', () => {
                    this.loadUsers(1);
                });
            }

            // 전체 선택 체크박스
            const selectAll = document.getElementById('selectAll');
            if (selectAll) {
                selectAll.addEventListener('change', (e) => {
                    const checkboxes = document.querySelectorAll('.user-checkbox');
                    checkboxes.forEach(cb => {
                        cb.checked = e.target.checked;
                        const userId = parseInt(cb.dataset.userId);
                        if (e.target.checked) {
                            selectedUsers.add(userId);
                        } else {
                            selectedUsers.delete(userId);
                        }
                    });
                    this.updateBulkActions();
                });
            }
        },

        // 사용자 통계 로드
        async loadUserStats() {
            try {
                const response = await fetch(`${API_BASE_URL}/api/admin/users/stats`);
                const data = await response.json();

                if (data.success || data.total !== undefined) {
                    // ID 수정: totalUsersCount, activeUsersCount
                    const totalEl = document.getElementById('totalUsersCount');
                    const activeEl = document.getElementById('activeUsersCount');
                    const inactiveEl = document.getElementById('inactiveUsers');
                    const adminEl = document.getElementById('adminUsers');

                    if (totalEl) totalEl.textContent = data.total || data.stats?.total_users || '0';
                    if (activeEl) activeEl.textContent = data.active || data.stats?.active_users || '0';
                    if (inactiveEl) inactiveEl.textContent = data.inactive || data.stats?.inactive_users || '0';
                    if (adminEl) adminEl.textContent = data.admins || data.stats?.admin_users || '0';
                }
            } catch (error) {
                console.error('통계 로드 실패:', error);
            }
        },

        // 사용자 목록 로드
        async loadUsers(page = 1) {
            try {
                const search = document.getElementById('searchInput')?.value || '';
                const role = document.getElementById('roleFilter')?.value || '';

                const url = new URL(`${API_BASE_URL}/api/users`);
                url.searchParams.append('page', page);
                url.searchParams.append('limit', 10);
                if (search) url.searchParams.append('search', search);
                if (role) url.searchParams.append('role', role);

                const response = await fetch(url);
                const data = await response.json();

                if (data.success) {
                    this.renderUsersTable(data.users);
                    this.renderPagination(data.pagination);
                    currentPage = page;
                } else {
                    this.showAlert('사용자 목록을 불러오는데 실패했습니다: ' + data.error, 'error');
                }
            } catch (error) {
                console.error('사용자 목록 로드 실패:', error);
                this.showAlert('사용자 목록을 불러오는데 실패했습니다', 'error');
            }
        },

        // 사용자 테이블 렌더링
        renderUsersTable(users) {
            const tbody = document.getElementById('usersTableBody');
            if (!tbody) return;

            if (users.length === 0) {
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

            tbody.innerHTML = users.map(user => `
                <tr>
                    <td><input type="checkbox" class="user-checkbox" data-user-id="${user.id}"></td>
                    <td>
                        <div class="user-info">
                            <strong>${user.name}</strong>
                            <br>
                            <small>${user.username}</small>
                        </div>
                    </td>
                    <td>${user.contact || '-'}</td>
                    <td>${user.department || '-'}</td>
                    <td><span class="role-badge ${this.getRoleBadgeClass(user.role)}">${this.getRoleText(user.role)}</span></td>
                    <td>${this.formatDate(user.createdAt)}</td>
                    <td>
                        <span class="status-badge ${user.isActive ? 'active' : 'inactive'}">
                            ${user.isActive ? '활성' : '비활성'}
                        </span>
                    </td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn-icon" onclick="UsersManagementFull.editUser(${user.id})" title="수정">
                                ✏️
                            </button>
                            <button class="btn-icon" onclick="UsersManagementFull.toggleUserStatus(${user.id}, ${!user.isActive})" title="상태 변경">
                                ${user.isActive ? '⏸️' : '▶️'}
                            </button>
                            <button class="btn-icon btn-danger" onclick="UsersManagementFull.deleteUser(${user.id})" title="삭제">
                                🗑️
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');

            // 체크박스 이벤트 리스너 추가
            document.querySelectorAll('.user-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', (e) => {
                    const userId = parseInt(e.target.dataset.userId);
                    if (e.target.checked) {
                        selectedUsers.add(userId);
                    } else {
                        selectedUsers.delete(userId);
                    }
                    this.updateBulkActions();
                });
            });
        },

        // 페이지네이션 렌더링
        renderPagination(pagination) {
            const container = document.getElementById('pagination');
            if (!container) return;

            let html = '';

            // 이전 페이지 버튼
            html += `<button ${!pagination.has_prev ? 'disabled' : ''} onclick="UsersManagementFull.loadUsers(${pagination.current_page - 1})">이전</button>`;

            // 페이지 번호들
            const startPage = Math.max(1, pagination.current_page - 2);
            const endPage = Math.min(pagination.total_pages, pagination.current_page + 2);

            for (let i = startPage; i <= endPage; i++) {
                html += `<button class="${i === pagination.current_page ? 'active' : ''}" onclick="UsersManagementFull.loadUsers(${i})">${i}</button>`;
            }

            // 다음 페이지 버튼
            html += `<button ${!pagination.has_next ? 'disabled' : ''} onclick="UsersManagementFull.loadUsers(${pagination.current_page + 1})">다음</button>`;

            container.innerHTML = html;
        },

        // 권한 텍스트 변환
        getRoleText(role) {
            const roleMap = {
                'admin': '관리자',
                'nutritionist': '영양사',
                'operator': '운영자',
                'viewer': '조회자'
            };
            return roleMap[role] || role;
        },

        // 권한 배지 클래스
        getRoleBadgeClass(role) {
            const classMap = {
                'admin': 'admin',
                'nutritionist': 'nutritionist',
                'operator': 'operator',
                'viewer': 'viewer'
            };
            return classMap[role] || 'default';
        },

        // 날짜 포맷
        formatDate(dateString) {
            if (!dateString) return '-';
            const date = new Date(dateString);
            return date.toLocaleDateString('ko-KR');
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
            const bulkActions = document.getElementById('bulkActions');
            if (bulkActions) {
                bulkActions.style.display = selectedUsers.size > 0 ? 'flex' : 'none';
                const selectedCount = document.getElementById('selectedCount');
                if (selectedCount) {
                    selectedCount.textContent = selectedUsers.size;
                }
            }
        },

        // 사용자 편집
        async editUser(userId) {
            console.log('사용자 편집:', userId);
            // TODO: 편집 모달 구현
            this.showAlert(`사용자 ${userId} 편집 기능 준비 중`, 'info');
        },

        // 사용자 상태 토글
        async toggleUserStatus(userId, newStatus) {
            const statusText = newStatus ? '활성화' : '비활성화';
            if (!confirm(`사용자를 ${statusText}하시겠습니까?`)) return;

            try {
                const response = await fetch(`${API_BASE_URL}/api/users/${userId}/status`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ isActive: newStatus })
                });

                const result = await response.json();
                if (result.success) {
                    this.showAlert(`사용자가 ${statusText}되었습니다.`, 'success');
                    this.loadUsers(currentPage);
                } else {
                    this.showAlert(`상태 변경 실패: ${result.error}`, 'error');
                }
            } catch (error) {
                console.error('상태 변경 오류:', error);
                this.showAlert('상태 변경 중 오류가 발생했습니다.', 'error');
            }
        },

        // 사용자 삭제
        async deleteUser(userId) {
            if (!confirm('정말로 이 사용자를 삭제하시겠습니까?')) return;

            try {
                const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
                    method: 'DELETE'
                });

                const result = await response.json();
                if (result.success !== false) {
                    this.showAlert('사용자가 삭제되었습니다.', 'success');
                    this.loadUsers(currentPage);
                } else {
                    this.showAlert(`삭제 실패: ${result.error}`, 'error');
                }
            } catch (error) {
                console.error('삭제 오류:', error);
                this.showAlert('삭제 중 오류가 발생했습니다.', 'error');
            }
        },

        // 선택된 사용자 벌크 삭제
        async bulkDelete() {
            if (!confirm(`선택한 ${selectedUsers.size}명의 사용자를 삭제하시겠습니까?`)) return;

            try {
                const response = await fetch(`${API_BASE_URL}/api/users/bulk-delete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ userIds: Array.from(selectedUsers) })
                });

                const result = await response.json();
                if (result.success) {
                    this.showAlert(`${result.deleted}명의 사용자가 삭제되었습니다.`, 'success');
                    selectedUsers.clear();
                    this.updateBulkActions();
                    this.loadUsers(1);
                } else {
                    this.showAlert(`벌크 삭제 실패: ${result.error}`, 'error');
                }
            } catch (error) {
                console.error('벌크 삭제 오류:', error);
                this.showAlert('벌크 삭제 중 오류가 발생했습니다.', 'error');
            }
        },

        // 새 사용자 추가 모달 표시
        showAddUserModal() {
            console.log('새 사용자 추가 모달');
            // TODO: 사용자 추가 모달 구현
            this.showAlert('사용자 추가 기능 준비 중', 'info');
        }
    };

    console.log('👥 Full Users Management Module 정의 완료');

})();