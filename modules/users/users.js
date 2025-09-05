/**
 * Users Module - 사용자 관리
 * 사용자 CRUD, 권한 관리, 사업장 할당 등을 담당하는 독립 모듈
 */
class UsersModule {
    constructor() {
        this.currentPage = 1;
        this.totalPages = 1;
        this.pageSize = 20;
        this.currentEditUserId = null;
        this.users = [];
        this.filteredUsers = [];
        this.sortField = null;
        this.sortDirection = 'asc';
        this.selectedUsers = new Set();
        this.init();
    }

    /**
     * 모듈 초기화
     */
    init() {
        if (document.getElementById('users-page')) {
            console.log('[Users] 모듈 초기화 시작');
            this.loadUsers();
            this.loadUserStats();
            this.setupEventListeners();
        }
    }

    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        // 검색 입력 필드에서 Enter 키 처리
        const searchInput = document.getElementById('user-search');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchUsers();
                }
            });
        }

        // 전체 선택 체크박스
        const selectAllCheckbox = document.getElementById('select-all-users');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', () => this.toggleSelectAll());
        }
    }

    /**
     * 사용자 목록 로드
     */
    async loadUsers() {
        try {
            console.log('[Users] 사용자 목록 로드 시작');
            
            const response = await fetch('/api/admin/users');
            const data = await response.json();
            
            if (data.success) {
                this.users = data.users || [];
                this.filteredUsers = [...this.users];
                this.displayUsers();
                this.updatePagination(data.currentPage || 1, data.totalPages || 1);
                console.log(`[Users] 사용자 ${this.users.length}명 로드 완료`);
            } else {
                throw new Error(data.message || '사용자 목록 로드 실패');
            }
        } catch (error) {
            console.error('[Users] 사용자 목록 로드 실패:', error);
            this.showErrorState();
        }
    }

    /**
     * 사용자 통계 로드
     */
    async loadUserStats() {
        try {
            const stats = this.calculateStats();
            this.updateStatsDisplay(stats);
        } catch (error) {
            console.error('[Users] 통계 로드 실패:', error);
        }
    }

    /**
     * 통계 계산
     */
    calculateStats() {
        const total = this.users.length;
        const active = this.users.filter(user => user.is_active).length;
        const admin = this.users.filter(user => user.role === 'admin').length;
        const inactive = total - active;

        return { total, active, admin, inactive };
    }

    /**
     * 통계 표시 업데이트
     */
    updateStatsDisplay(stats) {
        const elements = {
            'total-users-count': stats.total,
            'active-users-count': stats.active,
            'admin-users-count': stats.admin,
            'inactive-users-count': stats.inactive
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    /**
     * 사용자 목록 표시
     */
    displayUsers() {
        const tbody = document.getElementById('users-table-body');
        if (!tbody) return;
        
        if (!this.filteredUsers || this.filteredUsers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="11" class="loading-row">등록된 사용자가 없습니다.</td></tr>';
            return;
        }
        
        const startIndex = (this.currentPage - 1) * this.pageSize;
        const endIndex = startIndex + this.pageSize;
        const pageUsers = this.filteredUsers.slice(startIndex, endIndex);
        
        tbody.innerHTML = pageUsers.map(user => `
            <tr class="${this.selectedUsers.has(user.id) ? 'selected-row' : ''}">
                <td>
                    <input type="checkbox" class="user-checkbox" 
                           value="${user.id}" 
                           ${this.selectedUsers.has(user.id) ? 'checked' : ''}
                           onchange="UsersModule.toggleUserSelection(${user.id})">
                </td>
                <td>${user.id}</td>
                <td>
                    <div class="user-info">
                        <span class="username">${this.escapeHtml(user.username)}</span>
                        <div class="user-email">${this.escapeHtml(user.email || '-')}</div>
                    </div>
                </td>
                <td><span class="role-badge role-${user.role}">${this.getRoleDisplay(user.role)}</span></td>
                <td>${this.escapeHtml(user.department || '-')}</td>
                <td>${this.escapeHtml(user.phone_number || '-')}</td>
                <td>${this.escapeHtml(user.managed_site || '-')}</td>
                <td>${user.assigned_sites_count || 0}개 사업장</td>
                <td>
                    <span class="status-badge ${user.is_active ? 'status-active' : 'status-inactive'}">
                        ${user.is_active ? '활성' : '비활성'}
                    </span>
                </td>
                <td>${this.formatLastLogin(user.last_login)}</td>
                <td class="actions-cell">
                    <button class="btn-small btn-edit" onclick="UsersModule.editUser(${user.id})" title="편집">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-small btn-sites" onclick="UsersModule.manageSites(${user.id})" title="사업장 관리">
                        <i class="fas fa-building"></i>
                    </button>
                    <button class="btn-small btn-reset" onclick="UsersModule.resetPassword(${user.id})" title="비밀번호 초기화">
                        <i class="fas fa-key"></i>
                    </button>
                    <button class="btn-small ${user.is_active ? 'btn-danger' : 'btn-success'}" 
                            onclick="UsersModule.toggleUserStatus(${user.id}, ${!user.is_active})" 
                            title="${user.is_active ? '비활성화' : '활성화'}">
                        <i class="fas fa-${user.is_active ? 'times' : 'check'}"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
        this.updateBulkActionsBar();
    }

    /**
     * 에러 상태 표시
     */
    showErrorState() {
        const tbody = document.getElementById('users-table-body');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="11" class="loading-row" style="color: #dc3545;">
                        <i class="fas fa-exclamation-triangle"></i> 
                        사용자 목록을 불러올 수 없습니다. 다시 시도해주세요.
                        <br>
                        <button onclick="UsersModule.loadUsers()" class="btn-secondary" style="margin-top: 10px;">
                            다시 시도
                        </button>
                    </td>
                </tr>
            `;
        }
    }

    /**
     * 역할 표시명 반환
     */
    getRoleDisplay(role) {
        const roleMap = {
            'admin': '관리자',
            'manager': '담당자',
            'viewer': '열람자'
        };
        return roleMap[role] || role;
    }

    /**
     * 최근 로그인 시간 포맷
     */
    formatLastLogin(lastLogin) {
        if (!lastLogin) return '로그인 기록 없음';
        
        try {
            const date = new Date(lastLogin);
            const now = new Date();
            const diff = now - date;
            
            if (diff < 60000) { // 1분 미만
                return '방금 전';
            } else if (diff < 3600000) { // 1시간 미만
                return Math.floor(diff / 60000) + '분 전';
            } else if (diff < 86400000) { // 24시간 미만
                return Math.floor(diff / 3600000) + '시간 전';
            } else {
                return date.toLocaleDateString();
            }
        } catch (error) {
            return lastLogin;
        }
    }

    /**
     * 사용자 검색
     */
    searchUsers() {
        const keyword = document.getElementById('user-search')?.value?.toLowerCase() || '';
        
        if (!keyword) {
            this.filteredUsers = [...this.users];
        } else {
            this.filteredUsers = this.users.filter(user => 
                user.username?.toLowerCase().includes(keyword) ||
                user.email?.toLowerCase().includes(keyword) ||
                user.department?.toLowerCase().includes(keyword) ||
                user.phone_number?.includes(keyword)
            );
        }
        
        this.currentPage = 1;
        this.displayUsers();
        this.updatePaginationInfo();
        console.log(`[Users] 검색 결과: ${this.filteredUsers.length}명`);
    }

    /**
     * 사용자 필터링
     */
    filterUsers() {
        const roleFilter = document.getElementById('role-filter')?.value || '';
        const statusFilter = document.getElementById('status-filter')?.value || '';
        
        this.filteredUsers = this.users.filter(user => {
            const roleMatch = !roleFilter || user.role === roleFilter;
            const statusMatch = !statusFilter || 
                (statusFilter === 'active' && user.is_active) ||
                (statusFilter === 'inactive' && !user.is_active);
            
            return roleMatch && statusMatch;
        });
        
        // 검색어도 적용
        const keyword = document.getElementById('user-search')?.value?.toLowerCase() || '';
        if (keyword) {
            this.filteredUsers = this.filteredUsers.filter(user => 
                user.username?.toLowerCase().includes(keyword) ||
                user.email?.toLowerCase().includes(keyword) ||
                user.department?.toLowerCase().includes(keyword)
            );
        }
        
        this.currentPage = 1;
        this.displayUsers();
        this.updatePaginationInfo();
    }

    /**
     * 필터 초기화
     */
    clearFilters() {
        document.getElementById('user-search').value = '';
        document.getElementById('role-filter').value = '';
        document.getElementById('status-filter').value = '';
        
        this.filteredUsers = [...this.users];
        this.currentPage = 1;
        this.displayUsers();
        this.updatePaginationInfo();
    }

    /**
     * 정렬
     */
    sortBy(field) {
        if (this.sortField === field) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortField = field;
            this.sortDirection = 'asc';
        }
        
        this.filteredUsers.sort((a, b) => {
            const aVal = a[field];
            const bVal = b[field];
            
            if (aVal < bVal) return this.sortDirection === 'asc' ? -1 : 1;
            if (aVal > bVal) return this.sortDirection === 'asc' ? 1 : -1;
            return 0;
        });
        
        this.displayUsers();
        this.updateSortIndicators(field);
    }

    /**
     * 정렬 표시 업데이트
     */
    updateSortIndicators(field) {
        // 모든 정렬 표시 제거
        document.querySelectorAll('.sortable').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });
        
        // 현재 정렬 필드 표시
        const currentTh = document.querySelector(`[onclick="UsersModule.sortBy('${field}')"]`);
        if (currentTh) {
            currentTh.classList.add(this.sortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
        }
    }

    /**
     * 페이지 변경
     */
    changePage(direction) {
        const newPage = this.currentPage + direction;
        const maxPages = Math.ceil(this.filteredUsers.length / this.pageSize);
        
        if (newPage >= 1 && newPage <= maxPages) {
            this.currentPage = newPage;
            this.displayUsers();
            this.updatePaginationInfo();
        }
    }

    /**
     * 페이지 크기 변경
     */
    changePageSize() {
        const pageSize = parseInt(document.getElementById('page-size')?.value || 20);
        this.pageSize = pageSize;
        this.currentPage = 1;
        this.displayUsers();
        this.updatePaginationInfo();
    }

    /**
     * 페이지네이션 정보 업데이트
     */
    updatePaginationInfo() {
        const maxPages = Math.ceil(this.filteredUsers.length / this.pageSize);
        const pageInfo = document.getElementById('page-info');
        if (pageInfo) {
            pageInfo.textContent = `${this.currentPage} / ${maxPages}`;
        }
        
        // 버튼 상태 업데이트
        const prevBtn = document.getElementById('prev-page-btn');
        const nextBtn = document.getElementById('next-page-btn');
        
        if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
        if (nextBtn) nextBtn.disabled = this.currentPage >= maxPages;
    }

    /**
     * 전체 선택 토글
     */
    toggleSelectAll() {
        const selectAllCheckbox = document.getElementById('select-all-users');
        const isChecked = selectAllCheckbox?.checked || false;
        
        if (isChecked) {
            // 현재 페이지의 모든 사용자 선택
            const startIndex = (this.currentPage - 1) * this.pageSize;
            const endIndex = startIndex + this.pageSize;
            const pageUsers = this.filteredUsers.slice(startIndex, endIndex);
            
            pageUsers.forEach(user => this.selectedUsers.add(user.id));
        } else {
            this.selectedUsers.clear();
        }
        
        this.displayUsers();
    }

    /**
     * 개별 사용자 선택 토글
     */
    toggleUserSelection(userId) {
        if (this.selectedUsers.has(userId)) {
            this.selectedUsers.delete(userId);
        } else {
            this.selectedUsers.add(userId);
        }
        
        this.displayUsers();
    }

    /**
     * 일괄 작업 바 업데이트
     */
    updateBulkActionsBar() {
        const selectedCount = this.selectedUsers.size;
        let bulkBar = document.querySelector('.bulk-actions-bar');
        
        if (selectedCount > 0) {
            if (!bulkBar) {
                bulkBar = this.createBulkActionsBar();
                const tableContainer = document.querySelector('.table-container');
                tableContainer.parentNode.insertBefore(bulkBar, tableContainer);
            }
            
            bulkBar.querySelector('.selected-count').textContent = `${selectedCount}명 선택됨`;
            bulkBar.classList.add('show');
        } else if (bulkBar) {
            bulkBar.classList.remove('show');
        }
    }

    /**
     * 일괄 작업 바 생성
     */
    createBulkActionsBar() {
        const bulkBar = document.createElement('div');
        bulkBar.className = 'bulk-actions-bar';
        bulkBar.innerHTML = `
            <span class="selected-count"></span>
            <button class="bulk-action-btn" onclick="UsersModule.bulkActivate()">
                <i class="fas fa-check"></i> 일괄 활성화
            </button>
            <button class="bulk-action-btn" onclick="UsersModule.bulkDeactivate()">
                <i class="fas fa-times"></i> 일괄 비활성화
            </button>
            <button class="bulk-action-btn" onclick="UsersModule.bulkExport()">
                <i class="fas fa-download"></i> 선택 내보내기
            </button>
            <button class="bulk-action-btn" onclick="UsersModule.clearSelection()">
                <i class="fas fa-times-circle"></i> 선택 해제
            </button>
        `;
        return bulkBar;
    }

    /**
     * 선택 해제
     */
    clearSelection() {
        this.selectedUsers.clear();
        const selectAllCheckbox = document.getElementById('select-all-users');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = false;
        }
        this.displayUsers();
    }

    /**
     * HTML 이스케이프
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 새 사용자 추가 모달 표시
     */
    showAddUserModal() {
        console.log('[Users] 새 사용자 추가 모달 표시');
        // 실제 모달 구현 필요
        alert('새 사용자 추가 모달 (구현 예정)');
    }

    /**
     * 사용자 편집
     */
    editUser(userId) {
        console.log('[Users] 사용자 편집:', userId);
        alert(`사용자 ${userId} 편집 (구현 예정)`);
    }

    /**
     * 사업장 관리
     */
    manageSites(userId) {
        console.log('[Users] 사업장 관리:', userId);
        alert(`사용자 ${userId} 사업장 관리 (구현 예정)`);
    }

    /**
     * 비밀번호 초기화
     */
    async resetPassword(userId) {
        if (!confirm('이 사용자의 비밀번호를 초기화하시겠습니까?')) {
            return;
        }
        
        console.log('[Users] 비밀번호 초기화:', userId);
        alert(`사용자 ${userId} 비밀번호 초기화 (구현 예정)`);
    }

    /**
     * 사용자 상태 토글
     */
    async toggleUserStatus(userId, newStatus) {
        const action = newStatus ? '활성화' : '비활성화';
        
        if (!confirm(`이 사용자를 ${action}하시겠습니까?`)) {
            return;
        }
        
        console.log('[Users] 사용자 상태 변경:', userId, '→', newStatus);
        
        // API 호출 구현 예정
        // 임시로 로컬 상태 업데이트
        const user = this.users.find(u => u.id === userId);
        if (user) {
            user.is_active = newStatus;
            this.displayUsers();
            this.loadUserStats();
        }
    }

    /**
     * 사용자 내보내기
     */
    exportUsers() {
        console.log('[Users] 사용자 목록 내보내기');
        alert('사용자 목록 내보내기 (구현 예정)');
    }

    /**
     * 일괄 활성화
     */
    async bulkActivate() {
        if (this.selectedUsers.size === 0) return;
        
        if (!confirm(`선택된 ${this.selectedUsers.size}명의 사용자를 일괄 활성화하시겠습니까?`)) {
            return;
        }
        
        console.log('[Users] 일괄 활성화:', [...this.selectedUsers]);
        // API 호출 구현 예정
    }

    /**
     * 일괄 비활성화
     */
    async bulkDeactivate() {
        if (this.selectedUsers.size === 0) return;
        
        if (!confirm(`선택된 ${this.selectedUsers.size}명의 사용자를 일괄 비활성화하시겠습니까?`)) {
            return;
        }
        
        console.log('[Users] 일괄 비활성화:', [...this.selectedUsers]);
        // API 호출 구현 예정
    }

    /**
     * 선택된 사용자 내보내기
     */
    bulkExport() {
        if (this.selectedUsers.size === 0) return;
        
        console.log('[Users] 선택된 사용자 내보내기:', [...this.selectedUsers]);
        alert(`선택된 ${this.selectedUsers.size}명 내보내기 (구현 예정)`);
    }

    /**
     * 일괄 작업 표시
     */
    showBulkActions() {
        console.log('[Users] 일괄 작업 표시');
        alert('일괄 작업 옵션 (구현 예정)');
    }

    /**
     * 페이지네이션 업데이트
     */
    updatePagination(currentPage, totalPages) {
        this.currentPage = currentPage;
        this.totalPages = totalPages;
        this.updatePaginationInfo();
    }

    /**
     * 페이지 표시 시 호출
     */
    onPageShow() {
        this.loadUsers();
        this.loadUserStats();
    }

    /**
     * 페이지 숨김 시 호출
     */
    onPageHide() {
        this.selectedUsers.clear();
    }
}

// 전역 인스턴스 생성
window.UsersModule = new UsersModule();

console.log('[Users] 사용자 모듈 로드 완료');