/**
 * 사용자 관리 모듈
 * admin 대시보드용 완전한 사용자 관리 기능
 */

class UserManagement {
    constructor() {
        this.API_BASE_URL = window.CONFIG?.API?.BASE_URL || 'http://127.0.0.1:8010';
        this.currentUserId = null;
        this.isEditMode = false;
        this.isLoaded = false;
        this.modalLoaded = false;
    }

    async load() {
        if (this.isLoaded) return;
        console.log('🚀 [UserManagement] 사용자 관리 모듈 초기화');

        // 페이지 컨텐츠 영역에 사용자 관리 HTML 구조 생성
        await this.renderUserManagementHTML();

        // 모달 HTML 동적 로드
        await this.loadModalHTML();

        // 권한 관리 모듈 로드
        await this.loadPermissionsModule();

        this.setupEventListeners();
        await this.loadUserStats();
        await this.loadUsers();

        this.isLoaded = true;
    }

    // 사용자 관리 HTML 동적 생성
    async renderUserManagementHTML() {
        const contentArea = document.getElementById('content-area');
        if (!contentArea) {
            console.error('Content area not found');
            return;
        }

        const userHTML = `
            <div id="users-content" class="page-content">
                <div class="user-management-container">
                    <!-- 헤더 섹션 -->
                    <div class="page-header">
                        <h1>사용자 관리</h1>
                        <button class="btn btn-primary" onclick="window.userManagement.openCreateModal()">
                            <i class="fas fa-plus"></i> 사용자 추가
                        </button>
                    </div>

                    <!-- 통계 카드 섹션 -->
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-icon">
                                <i class="fas fa-users"></i>
                            </div>
                            <div class="stat-content">
                                <h3 id="totalUsers">로딩중...</h3>
                                <p>전체 사용자</p>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">
                                <i class="fas fa-user-check"></i>
                            </div>
                            <div class="stat-content">
                                <h3 id="activeUsers">로딩중...</h3>
                                <p>활성 사용자</p>
                            </div>
                        </div>
                    </div>

                    <!-- 검색 및 필터 섹션 -->
                    <div class="filters-section">
                        <div class="search-box">
                            <i class="fas fa-search"></i>
                            <input type="text" id="searchInput" placeholder="사용자명 또는 연락처로 검색...">
                        </div>
                        <div class="filter-group">
                            <select id="roleFilter">
                                <option value="">모든 권한</option>
                                <option value="admin">관리자</option>
                                <option value="nutritionist">영양사</option>
                                <option value="operator">운영자</option>
                                <option value="viewer">조회자</option>
                            </select>
                        </div>
                    </div>

                    <!-- 테이블 섹션 -->
                    <div class="table-container">
                        <!-- 로딩 인디케이터 -->
                        <div id="loadingIndicator" class="loading-indicator" style="display: none;">
                            <i class="fas fa-spinner fa-spin"></i>
                            <span>데이터를 불러오고 있습니다...</span>
                        </div>

                        <!-- 사용자 테이블 -->
                        <table id="usersTable" class="data-table">
                            <thead>
                                <tr>
                                    <th>사용자명</th>
                                    <th>연락처</th>
                                    <th>부서</th>
                                    <th>권한</th>
                                    <th>상태</th>
                                    <th>등록일</th>
                                    <th>작업</th>
                                </tr>
                            </thead>
                            <tbody id="usersTableBody">
                                <!-- 동적으로 생성될 사용자 목록 -->
                            </tbody>
                        </table>

                        <!-- 빈 상태 -->
                        <div id="emptyState" class="empty-state" style="display: none;">
                            <i class="fas fa-users"></i>
                            <h3>사용자가 없습니다</h3>
                            <p>검색 조건을 변경하거나 새 사용자를 추가해보세요.</p>
                        </div>
                    </div>

                    <!-- 페이지네이션 -->
                    <div id="pagination" class="pagination-container">
                        <!-- 동적으로 생성될 페이지네이션 -->
                    </div>
                </div>

                <!-- 사용자 추가/수정 모달 -->
                <div id="userModal" class="modal" style="display: none;">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h2 id="modalTitle">사용자 추가</h2>
                            <button type="button" class="close-btn" onclick="closeModal()">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>

                        <form id="userForm" class="modal-form">
                            <div class="form-group">
                                <label for="username">사용자명 *</label>
                                <input type="text" id="username" name="username" required>
                            </div>

                            <div class="form-group" id="passwordGroup">
                                <label for="password">비밀번호 *</label>
                                <input type="password" id="password" name="password" required>
                            </div>

                            <div class="form-group">
                                <label for="contact_info">연락처</label>
                                <input type="text" id="contact_info" name="contact_info" placeholder="전화번호 또는 이메일">
                            </div>

                            <div class="form-group">
                                <label for="department">부서</label>
                                <input type="text" id="department" name="department" placeholder="소속 부서">
                            </div>

                            <div class="form-group">
                                <label for="role">권한 *</label>
                                <select id="role" name="role" required>
                                    <option value="">권한 선택</option>
                                    <option value="admin">관리자</option>
                                    <option value="nutritionist">영양사</option>
                                    <option value="operator">운영자</option>
                                    <option value="viewer">조회자</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label for="notes">비고</label>
                                <textarea id="notes" name="notes" placeholder="추가 정보나 메모"></textarea>
                            </div>

                            <!-- 비밀번호 초기화 버튼 (수정 모드에서만 표시) -->
                            <div class="form-group" id="passwordResetGroup" style="display: none;">
                                <button type="button" class="btn btn-warning" onclick="window.userManagement.resetPassword()">
                                    <i class="fas fa-key"></i> 비밀번호 초기화
                                </button>
                            </div>

                            <!-- 사업장 권한 체크박스 섹션 -->
                            <div class="form-group">
                                <label>사업장 접근 권한</label>
                                <div id="sitePermissions" class="site-permissions-grid">
                                    <!-- 동적으로 생성될 체크박스들 -->
                                </div>
                            </div>

                            <div class="modal-actions">
                                <button type="button" class="btn btn-secondary" onclick="closeModal()">취소</button>
                                <button type="submit" id="submitBtn" class="btn btn-primary">추가</button>
                            </div>
                        </form>
                    </div>
                </div>

                <!-- 알림 컨테이너 -->
                <div id="alertContainer" class="alert-container"></div>
            </div>
        `;

        contentArea.innerHTML = userHTML;
    }

    async loadModalHTML() {
        try {
            const container = document.getElementById('userModalContainer');
            if (!container) {
                console.error('Modal container not found');
                return;
            }

            const response = await fetch('/static/modules/users/user-modal.html');
            if (!response.ok) throw new Error('Failed to load modal HTML');

            const html = await response.text();
            container.innerHTML = html;
            this.modalLoaded = true;

            console.log('✅ [UserManagement] 모달 HTML 로드 완료');
        } catch (error) {
            console.error('Modal HTML 로드 실패:', error);
        }
    }

    async loadPermissionsModule() {
        try {
            // 권한 관리 스크립트 동적 로드
            if (!window.userPermissionsManager) {
                const script = document.createElement('script');
                script.src = '/static/modules/users/user-permissions.js';
                document.head.appendChild(script);

                // 스크립트 로드 대기
                await new Promise((resolve) => {
                    script.onload = resolve;
                });
            }

            // 권한 관리자 초기화
            if (window.userPermissionsManager) {
                await window.userPermissionsManager.init();
                console.log('✅ [UserManagement] 권한 관리 모듈 초기화 완료');
            }
        } catch (error) {
            console.error('권한 모듈 로드 실패:', error);
        }
    }

    setupEventListeners() {
        // 검색 입력 시 실시간 검색
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => this.loadUsers(), 500));
        }

        // 권한 필터 변경 시
        const roleFilter = document.getElementById('roleFilter');
        if (roleFilter) {
            roleFilter.addEventListener('change', () => this.loadUsers());
        }

        // 사용자 폼 제출 (모달 로드 후)
        setTimeout(() => {
            const userForm = document.getElementById('userForm');
            if (userForm) {
                userForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
            }

            // 모달 외부 클릭 시 닫기
            window.addEventListener('click', (event) => {
                const modal = document.getElementById('userModal');
                if (event.target === modal) {
                    this.closeModal();
                }
            });
        }, 1000);
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

    // 사용자 통계 로드
    async loadUserStats() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/api/admin/users/stats`);
            if (!response.ok) throw new Error('통계 로드 실패');

            const stats = await response.json();

            const totalUsersElement = document.getElementById('totalUsers');
            const activeUsersElement = document.getElementById('activeUsers');

            if (totalUsersElement) totalUsersElement.textContent = stats.total || '0';
            if (activeUsersElement) activeUsersElement.textContent = stats.active || '0';
        } catch (error) {
            console.error('사용자 통계 로드 오류:', error);
            const totalUsersElement = document.getElementById('totalUsers');
            const activeUsersElement = document.getElementById('activeUsers');

            if (totalUsersElement) totalUsersElement.textContent = '오류';
            if (activeUsersElement) activeUsersElement.textContent = '오류';
        }
    }

    // 사용자 목록 로드
    async loadUsers(page = 1) {
        try {
            this.showLoading(true);

            const search = document.getElementById('searchInput')?.value || '';
            const role = document.getElementById('roleFilter')?.value || '';

            const params = new URLSearchParams({
                page: page.toString(),
                per_page: '10'
            });

            if (search) params.append('search', search);
            if (role) params.append('role', role);

            const response = await fetch(`${this.API_BASE_URL}/api/users?${params}`);
            if (!response.ok) throw new Error('사용자 목록 로드 실패');

            const data = await response.json();

            this.renderUsersTable(data.users || []);
            this.renderPagination(data.pagination);

        } catch (error) {
            console.error('사용자 목록 로드 오류:', error);
            this.showError('사용자 목록을 불러오는데 실패했습니다.');
        } finally {
            this.showLoading(false);
        }
    }

    // 사용자 테이블 렌더링
    renderUsersTable(users) {
        const tbody = document.getElementById('usersTableBody');
        const table = document.getElementById('usersTable');
        const emptyState = document.getElementById('emptyState');

        if (!tbody) return;

        if (!users || users.length === 0) {
            if (table) table.style.display = 'none';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        if (table) table.style.display = 'table';
        if (emptyState) emptyState.style.display = 'none';

        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${this.escapeHtml(user.username || '')}</td>
                <td>${this.escapeHtml(user.contact_info || '')}</td>
                <td>${this.escapeHtml(user.department || '-')}</td>
                <td><span class="role-badge role-${user.role}">${this.getRoleText(user.role)}</span></td>
                <td><span class="status-badge status-${user.is_active ? 'active' : 'inactive'}">${user.is_active ? '활성' : '비활성'}</span></td>
                <td>${this.formatDate(user.created_at)}</td>
                <td>
                    <div class="actions">
                        <button class="btn btn-sm btn-primary" onclick="window.userManagement.editUser(${user.id})">수정</button>
                        ${user.is_active ?
                            `<button class="btn btn-sm btn-danger" onclick="window.userManagement.deactivateUser(${user.id})">비활성화</button>` :
                            `<button class="btn btn-sm btn-success" onclick="window.userManagement.activateUser(${user.id})">활성화</button>`
                        }
                    </div>
                </td>
            </tr>
        `).join('');
    }

    // 페이지네이션 렌더링
    renderPagination(pagination) {
        const container = document.getElementById('pagination');
        if (!container || !pagination) return;

        let html = '';

        // 이전 페이지 버튼
        html += `<button ${!pagination.has_prev ? 'disabled' : ''} onclick="window.userManagement.loadUsers(${pagination.current_page - 1})">이전</button>`;

        // 페이지 번호들
        const startPage = Math.max(1, pagination.current_page - 2);
        const endPage = Math.min(pagination.total_pages, pagination.current_page + 2);

        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="${i === pagination.current_page ? 'active' : ''}" onclick="window.userManagement.loadUsers(${i})">${i}</button>`;
        }

        // 다음 페이지 버튼
        html += `<button ${!pagination.has_next ? 'disabled' : ''} onclick="window.userManagement.loadUsers(${pagination.current_page + 1})">다음</button>`;

        container.innerHTML = html;
    }

    // 권한 텍스트 변환
    getRoleText(role) {
        const roleMap = {
            'admin': '관리자',
            'nutritionist': '영양사',
            'operator': '운영자',
            'viewer': '조회자'
        };
        return roleMap[role] || role;
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

    // 사용자 추가 모달 열기
    async openCreateModal() {
        this.currentUserId = null;
        this.isEditMode = false;

        const modalTitle = document.getElementById('modalTitle');
        const submitBtn = document.getElementById('submitBtn');
        const passwordGroup = document.getElementById('passwordGroup');
        const passwordField = document.getElementById('password');
        const passwordResetGroup = document.getElementById('passwordResetGroup');
        const userForm = document.getElementById('userForm');
        const userModal = document.getElementById('userModal');

        if (modalTitle) modalTitle.textContent = '사용자 추가';
        if (submitBtn) submitBtn.textContent = '추가';
        if (passwordGroup) passwordGroup.style.display = 'block';
        if (passwordField) passwordField.required = true;
        if (passwordResetGroup) passwordResetGroup.style.display = 'none';
        if (userForm) userForm.reset();
        if (userModal) userModal.style.display = 'block';

        // 사업장 체크박스 로드
        await this.loadSitePermissions();
    }

    // 사용자 수정 모달 열기
    async editUser(userId) {
        try {
            const response = await fetch(`${this.API_BASE_URL}/api/users/${userId}`);
            if (!response.ok) throw new Error('사용자 정보 로드 실패');

            const data = await response.json();
            const user = data.user || data;  // API 응답 형식 호환성

            this.currentUserId = userId;
            this.isEditMode = true;

            const modalTitle = document.getElementById('modalTitle');
            const submitBtn = document.getElementById('submitBtn');
            const passwordGroup = document.getElementById('passwordGroup');
            const passwordField = document.getElementById('password');
            const passwordResetGroup = document.getElementById('passwordResetGroup');
            const userModal = document.getElementById('userModal');

            if (modalTitle) modalTitle.textContent = '사용자 수정';
            if (submitBtn) submitBtn.textContent = '수정';
            if (passwordGroup) passwordGroup.style.display = 'none';
            if (passwordField) passwordField.required = false;
            if (passwordResetGroup) passwordResetGroup.style.display = 'block';

            // 폼에 데이터 채우기
            const usernameField = document.getElementById('username');
            const contactField = document.getElementById('contact_info');
            const departmentField = document.getElementById('department');
            const roleField = document.getElementById('role');
            const notesField = document.getElementById('notes');

            if (usernameField) usernameField.value = user.username || '';
            if (contactField) contactField.value = user.contact_info || '';
            if (departmentField) departmentField.value = user.department || '';
            if (roleField) roleField.value = user.role || '';
            if (notesField) notesField.value = user.notes || user.position || '';  // notes가 없으면 position 사용

            if (userModal) userModal.style.display = 'flex';

            // 사업장 권한 로드
            await this.loadUserSitePermissions(userId);

        } catch (error) {
            console.error('사용자 정보 로드 오류:', error);
            this.showError('사용자 정보를 불러오는데 실패했습니다.');
        }
    }

    // 모달 닫기
    closeModal() {
        const userModal = document.getElementById('userModal');
        const userForm = document.getElementById('userForm');

        if (userModal) userModal.style.display = 'none';
        if (userForm) userForm.reset();
        this.currentUserId = null;
        this.isEditMode = false;

        // 권한 관리자 리셋
        if (window.userPermissionsManager) {
            window.userPermissionsManager.reset();
        }
    }

    // 듀얼 리스트 선택기 관련 함수들 추가
    moveSelectedSites() {
        if (window.userPermissionsManager) {
            window.userPermissionsManager.moveSelectedSites();
        }
    }

    removeSelectedSites() {
        if (window.userPermissionsManager) {
            window.userPermissionsManager.removeSelectedSites();
        }
    }

    moveAllSites() {
        if (window.userPermissionsManager) {
            window.userPermissionsManager.moveAllSites();
        }
    }

    removeAllSites() {
        if (window.userPermissionsManager) {
            window.userPermissionsManager.removeAllSites();
        }
    }

    selectByType(type) {
        if (window.userPermissionsManager) {
            window.userPermissionsManager.selectByType(type);
        }
    }

    selectByRegion(region) {
        if (window.userPermissionsManager) {
            window.userPermissionsManager.selectByRegion(region);
        }
    }

    // 사용자 폼 제출
    async handleFormSubmit(e) {
        e.preventDefault();

        const formData = new FormData(e.target);
        const userData = {
            username: formData.get('username'),
            contact_info: formData.get('contact_info'),
            department: formData.get('department'),
            role: formData.get('role'),
            notes: formData.get('notes')
        };

        if (!this.isEditMode) {
            userData.password = formData.get('password');
        }

        // 선택된 사업장 권한 수집
        const selectedSites = [];
        const checkboxes = document.querySelectorAll('#sitePermissions input[type="checkbox"]:checked');
        checkboxes.forEach(checkbox => {
            selectedSites.push(parseInt(checkbox.value));
        });
        userData.site_permissions = selectedSites;

        try {
            const url = this.isEditMode
                ? `${this.API_BASE_URL}/api/users/${this.currentUserId}`
                : `${this.API_BASE_URL}/api/users`;

            const method = this.isEditMode ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '요청 처리 실패');
            }

            this.showSuccess(this.isEditMode ? '사용자가 수정되었습니다.' : '사용자가 추가되었습니다.');
            this.closeModal();
            await this.loadUsers();
            await this.loadUserStats();

        } catch (error) {
            console.error('사용자 저장 오류:', error);
            this.showError(`사용자 ${this.isEditMode ? '수정' : '추가'}에 실패했습니다: ${error.message}`);
        }
    }

    // 사용자 비활성화
    async deactivateUser(userId) {
        if (!confirm('정말로 이 사용자를 비활성화하시겠습니까?')) {
            return;
        }

        try {
            const response = await fetch(`${this.API_BASE_URL}/api/users/${userId}/deactivate`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('비활성화 실패');

            this.showSuccess('사용자가 비활성화되었습니다.');
            await this.loadUsers();
            await this.loadUserStats();

        } catch (error) {
            console.error('사용자 비활성화 오류:', error);
            this.showError('사용자 비활성화에 실패했습니다.');
        }
    }

    // 사용자 활성화
    async activateUser(userId) {
        try {
            const response = await fetch(`${this.API_BASE_URL}/api/users/${userId}/activate`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('활성화 실패');

            this.showSuccess('사용자가 활성화되었습니다.');
            await this.loadUsers();
            await this.loadUserStats();

        } catch (error) {
            console.error('사용자 활성화 오류:', error);
            this.showError('사용자 활성화에 실패했습니다.');
        }
    }

    // 로딩 표시
    showLoading(show) {
        const loadingIndicator = document.getElementById('loadingIndicator');
        const table = document.getElementById('usersTable');

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
        const container = document.getElementById('alertContainer');
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

    // 사업장 권한 체크박스 로드
    async loadSitePermissions(userId = null) {
        try {
            // 사업장 목록 가져오기
            const sitesResponse = await fetch(`${this.API_BASE_URL}/api/admin/business-locations`);
            if (!sitesResponse.ok) throw new Error('사업장 목록 로드 실패');
            const sites = await sitesResponse.json();

            // 사용자 권한 가져오기 (수정 모드인 경우)
            let userPermissions = [];
            if (userId) {
                const permResponse = await fetch(`${this.API_BASE_URL}/api/users/${userId}/permissions`);
                if (permResponse.ok) {
                    userPermissions = await permResponse.json();
                }
            }

            // 체크박스 HTML 생성
            const container = document.getElementById('sitePermissions');
            if (!container) return;

            const html = sites.map(site => {
                const hasPermission = userPermissions.some(p => p.site_id === site.id);
                return `
                    <div class="site-checkbox">
                        <input type="checkbox"
                            id="site_${site.id}"
                            name="sites"
                            value="${site.id}"
                            ${hasPermission ? 'checked' : ''}>
                        <label for="site_${site.id}">${site.name}</label>
                    </div>
                `;
            }).join('');

            container.innerHTML = html;

        } catch (error) {
            console.error('사업장 권한 로드 오류:', error);
        }
    }

    // 비밀번호 초기화
    async resetPassword() {
        if (!this.currentUserId) return;

        if (!confirm('정말로 비밀번호를 초기화하시겠습니까? 초기 비밀번호는 "1234"로 설정됩니다.')) {
            return;
        }

        try {
            const response = await fetch(`${this.API_BASE_URL}/api/users/${this.currentUserId}/reset-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ new_password: '1234' })
            });

            if (!response.ok) throw new Error('비밀번호 초기화 실패');

            this.showSuccess('비밀번호가 "1234"로 초기화되었습니다.');

        } catch (error) {
            console.error('비밀번호 초기화 오류:', error);
            this.showError('비밀번호 초기화에 실패했습니다.');
        }
    }
}

// 전역 함수들 (onclick 핸들러용)
function openCreateModal() {
    if (window.userManagement) {
        window.userManagement.openCreateModal();
    }
}

function closeModal() {
    if (window.userManagement) {
        window.userManagement.closeModal();
    }
}

function loadUsers() {
    if (window.userManagement) {
        window.userManagement.loadUsers();
    }
}

// 모듈 익스포트
window.UserManagement = UserManagement;