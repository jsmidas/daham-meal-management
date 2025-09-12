/**
 * 사용자 관리 모듈
 * 독립적인 사용자 관리 기능 제공
 */

window.UsersModule = {
    isLoaded: false,
    currentPage: 1,
    pageSize: 20,
    totalUsers: 0,

    async load() {
        if (this.isLoaded) return;

        const container = document.getElementById('users-module');
        if (!container) return;

        this.render(container);
        this.setupEventListeners(container);
        await this.loadUsers();
        
        this.isLoaded = true;
        console.log('👥 Users Module 로드됨');
    },

    render(container) {
        container.innerHTML = `
            <div class="users-module">
                <div class="module-header">
                    <h2>👥 사용자 관리</h2>
                    <div class="header-actions">
                        <input type="text" id="users-search" placeholder="사용자 검색..." class="search-input">
                        <button id="add-user-btn" class="btn btn-primary">+ 사용자 추가</button>
                    </div>
                </div>

                <div class="users-stats" id="users-stats">
                    <div class="loading">통계 로딩 중...</div>
                </div>

                <div class="users-table-container">
                    <table class="users-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>사용자명</th>
                                <th>이름</th>
                                <th>이메일</th>
                                <th>역할</th>
                                <th>활성화</th>
                                <th>생성일</th>
                                <th>작업</th>
                            </tr>
                        </thead>
                        <tbody id="users-table-body">
                            <tr>
                                <td colspan="8" class="loading-cell">사용자 목록 로딩 중...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="pagination" id="users-pagination">
                </div>

                <!-- 사용자 추가/수정 모달 -->
                <div id="user-modal" class="modal" style="display: none;">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3 id="modal-title">사용자 추가</h3>
                            <span class="modal-close">&times;</span>
                        </div>
                        <div class="modal-body">
                            <form id="user-form">
                                <div class="form-group">
                                    <label for="username">사용자명 *</label>
                                    <input type="text" id="username" name="username" required>
                                </div>
                                <div class="form-group">
                                    <label for="password">비밀번호 *</label>
                                    <input type="password" id="password" name="password" required>
                                </div>
                                <div class="form-group">
                                    <label for="contact_info">연락처/이름 *</label>
                                    <input type="text" id="contact_info" name="contact_info" required>
                                </div>
                                <div class="form-group">
                                    <label for="role">역할</label>
                                    <select id="role" name="role">
                                        <option value="nutritionist">영양사</option>
                                        <option value="admin">관리자</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>
                                        <input type="checkbox" id="is_active" name="is_active" checked>
                                        활성화
                                    </label>
                                </div>
                                <div class="form-actions">
                                    <button type="submit" class="btn btn-primary">저장</button>
                                    <button type="button" class="btn btn-secondary" onclick="UsersModule.closeModal()">취소</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.applyStyles();
    },

    applyStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .users-module {
                padding: 20px;
                max-width: 1200px;
            }

            .module-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 2px solid #eee;
            }

            .module-header h2 {
                color: #333;
                margin: 0;
            }

            .header-actions {
                display: flex;
                gap: 10px;
                align-items: center;
            }

            .search-input {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                width: 200px;
            }

            .users-stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }

            .stat-card {
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }

            .stat-value {
                font-size: 24px;
                font-weight: bold;
                color: #667eea;
            }

            .stat-label {
                font-size: 14px;
                color: #666;
                margin-top: 5px;
            }

            .users-table-container {
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }

            .users-table {
                width: 100%;
                border-collapse: collapse;
            }

            .users-table th,
            .users-table td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #eee;
            }

            .users-table th {
                background: #f8f9fa;
                font-weight: 600;
                color: #333;
            }

            .users-table tr:hover {
                background: #f8f9fa;
            }

            .loading-cell {
                text-align: center;
                color: #666;
                font-style: italic;
            }

            .btn {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 500;
                text-decoration: none;
                display: inline-block;
            }

            .btn-primary {
                background: #667eea;
                color: white;
            }

            .btn-secondary {
                background: #6c757d;
                color: white;
            }

            .btn-danger {
                background: #dc3545;
                color: white;
            }

            .btn-warning {
                background: #ffc107;
                color: #333;
            }

            .btn:hover {
                opacity: 0.9;
            }

            .btn-sm {
                padding: 4px 8px;
                font-size: 12px;
            }

            .status-badge {
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
            }

            .status-active {
                background: #d4edda;
                color: #155724;
            }

            .status-inactive {
                background: #f8d7da;
                color: #721c24;
            }

            .modal {
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
            }

            .modal-content {
                background: white;
                margin: 5% auto;
                padding: 0;
                border-radius: 8px;
                width: 90%;
                max-width: 500px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }

            .modal-header {
                padding: 20px;
                border-bottom: 1px solid #eee;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .modal-close {
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
                color: #aaa;
            }

            .modal-close:hover {
                color: #000;
            }

            .modal-body {
                padding: 20px;
            }

            .form-group {
                margin-bottom: 15px;
            }

            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: 500;
                color: #333;
            }

            .form-group input,
            .form-group select {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }

            .form-actions {
                display: flex;
                justify-content: flex-end;
                gap: 10px;
                margin-top: 20px;
            }

            .pagination {
                display: flex;
                justify-content: center;
                gap: 5px;
            }

            .pagination button {
                padding: 8px 12px;
                border: 1px solid #ddd;
                background: white;
                cursor: pointer;
            }

            .pagination button.active {
                background: #667eea;
                color: white;
                border-color: #667eea;
            }

            .pagination button:hover:not(.active) {
                background: #f8f9fa;
            }
        `;
        document.head.appendChild(style);
    },

    setupEventListeners(container) {
        // 검색
        const searchInput = container.querySelector('#users-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.searchUsers(e.target.value);
                }, 300);
            });
        }

        // 사용자 추가 버튼
        const addBtn = container.querySelector('#add-user-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.showAddModal());
        }

        // 모달 닫기
        const modal = container.querySelector('#user-modal');
        const closeBtn = container.querySelector('.modal-close');
        if (closeBtn && modal) {
            closeBtn.addEventListener('click', () => this.closeModal());
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.closeModal();
            });
        }

        // 폼 제출
        const form = container.querySelector('#user-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitForm();
            });
        }
    },

    async loadUsers(search = '', page = 1) {
        try {
            const params = {
                page,
                limit: this.pageSize,
                search
            };

            const response = await apiGet('/api/admin/users', params);
            console.log('API Response:', response);
            
            if (response.success !== false) {
                console.log('Response users:', response.users);
                console.log('Users length:', response.users ? response.users.length : 0);
                this.displayUsers(response.users || []);
                this.totalUsers = response.total || 0;
                this.updatePagination(page, Math.ceil(this.totalUsers / this.pageSize));
            } else {
                console.log('Response failed:', response);
                this.displayError('사용자 목록을 불러올 수 없습니다.');
            }

            // 통계 로드
            this.loadStats();

        } catch (error) {
            console.error('사용자 로드 중 오류:', error);
            console.error('Error message:', error.message);
            console.error('Error stack:', error.stack);
            // 오류 발생 시 빈 배열 대신 오류 메시지 표시
            this.displayError(`사용자 목록 로드 실패: ${error.message}`);
            this.displayUsers([]);
            this.totalUsers = 0;
            this.updatePagination(1, 1);
        }
    },

    async loadStats() {
        try {
            const response = await apiGet('/api/admin/user-stats');
            
            if (response.success !== false && response.stats) {
                this.displayStats(response.stats);
            }
        } catch (error) {
            console.warn('사용자 통계 로드 중 인증 오류 (일시적으로 무시):', error.message);
            // 인증 문제인 경우 기본 통계로 표시
            this.displayStats({
                total: 0,
                active: 0,
                inactive: 0,
                admins: 0
            });
        }
    },

    displayUsers(users) {
        const tbody = document.getElementById('users-table-body');
        if (!tbody) return;

        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="loading-cell">등록된 사용자가 없습니다.</td></tr>';
            return;
        }

        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${user.id}</td>
                <td><strong>${user.username}</strong></td>
                <td>${user.contact_info}</td>
                <td>${user.email || '-'}</td>
                <td><span class="status-badge">${user.role}</span></td>
                <td>
                    <span class="status-badge ${user.is_active ? 'status-active' : 'status-inactive'}">
                        ${user.is_active ? '활성' : '비활성'}
                    </span>
                </td>
                <td>${user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}</td>
                <td>
                    <button class="btn btn-sm btn-warning" onclick="UsersModule.editUser(${user.id})">수정</button>
                    <button class="btn btn-sm btn-secondary" onclick="UsersModule.resetPassword(${user.id})">비밀번호 초기화</button>
                    <button class="btn btn-sm btn-danger" onclick="UsersModule.deleteUser(${user.id})">삭제</button>
                </td>
            </tr>
        `).join('');
    },

    displayStats(stats) {
        const container = document.getElementById('users-stats');
        if (!container) return;

        container.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${stats.total_users || 0}</div>
                <div class="stat-label">총 사용자</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.active_users || 0}</div>
                <div class="stat-label">활성 사용자</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.admin_users || 0}</div>
                <div class="stat-label">관리자</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.regular_users || 0}</div>
                <div class="stat-label">일반 사용자</div>
            </div>
        `;
    },

    displayError(message) {
        const tbody = document.getElementById('users-table-body');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="8" class="loading-cell" style="color: #dc3545;">${message}</td></tr>`;
        }
    },

    updatePagination(currentPage, totalPages) {
        const container = document.getElementById('users-pagination');
        if (!container || totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let buttons = [];

        // 이전 페이지
        if (currentPage > 1) {
            buttons.push(`<button onclick="UsersModule.loadUsers('', ${currentPage - 1})">이전</button>`);
        }

        // 페이지 번호들
        for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
            buttons.push(`
                <button class="${i === currentPage ? 'active' : ''}" 
                        onclick="UsersModule.loadUsers('', ${i})">${i}</button>
            `);
        }

        // 다음 페이지
        if (currentPage < totalPages) {
            buttons.push(`<button onclick="UsersModule.loadUsers('', ${currentPage + 1})">다음</button>`);
        }

        container.innerHTML = buttons.join('');
    },

    async searchUsers(query) {
        this.currentPage = 1;
        await this.loadUsers(query, 1);
    },

    showAddModal() {
        document.getElementById('modal-title').textContent = '사용자 추가';
        document.getElementById('user-form').reset();
        
        // 새 사용자 추가 시 비밀번호 필수로 설정
        const passwordField = document.getElementById('password');
        passwordField.placeholder = '비밀번호';
        passwordField.required = true;
        
        document.getElementById('user-modal').style.display = 'block';
        this.editingUserId = null;
    },

    closeModal() {
        document.getElementById('user-modal').style.display = 'none';
    },

    async submitForm() {
        const form = document.getElementById('user-form');
        const formData = new FormData(form);
        
        const userData = {
            username: formData.get('username'),
            contact_info: formData.get('contact_info'),
            role: formData.get('role') || 'nutritionist',
            is_active: formData.has('is_active')
        };

        // 비밀번호가 입력된 경우에만 추가
        const password = formData.get('password');
        if (password && password.trim()) {
            userData.password = password;
        }

        try {
            let response;
            if (this.editingUserId) {
                delete userData.password; // 수정 시 비밀번호 제외
                response = await apiPut(`/api/admin/users/${this.editingUserId}`, userData);
            } else {
                console.log('Sending user data:', userData);
                response = await apiPost('/api/admin/users', userData);
            }

            if (response.success !== false) {
                showMessage(this.editingUserId ? '사용자가 수정되었습니다.' : '사용자가 추가되었습니다.', 'success');
                this.closeModal();
                this.loadUsers();
            } else {
                showMessage(response.message || '처리 중 오류가 발생했습니다.', 'error');
            }
        } catch (error) {
            console.error('사용자 저장 오류:', error);
            
            // HTTP 오류의 경우 더 구체적인 메시지 표시
            if (error.message && error.message.includes('HTTP error! status: 400')) {
                showMessage('이미 존재하는 사용자명입니다. 다른 사용자명을 입력해주세요.', 'error');
            } else if (error.message && error.message.includes('HTTP error! status: 422')) {
                showMessage('입력한 데이터가 올바르지 않습니다. 모든 필수 항목을 확인해주세요.', 'error');
            } else {
                showMessage('사용자 저장 중 오류가 발생했습니다.', 'error');
            }
        }
    },

    async editUser(userId) {
        try {
            const response = await apiGet(`/api/admin/users/${userId}`);
            
            if (response.success !== false) {
                const user = response.user || response;
                
                document.getElementById('modal-title').textContent = '사용자 수정';
                document.getElementById('username').value = user.username;
                document.getElementById('contact_info').value = user.contact_info;
                document.getElementById('role').value = user.role;
                document.getElementById('is_active').checked = user.is_active;
                
                // 비밀번호 필드를 선택사항으로 표시
                const passwordField = document.getElementById('password');
                passwordField.value = '';
                passwordField.placeholder = '새 비밀번호 (변경하지 않으려면 비워두세요)';
                passwordField.required = false;
                
                this.editingUserId = userId;
                document.getElementById('user-modal').style.display = 'block';
            } else {
                showMessage('사용자 정보를 불러올 수 없습니다.', 'error');
            }
        } catch (error) {
            console.error('사용자 정보 로드 오류:', error);
            showMessage('사용자 정보 로딩 중 오류가 발생했습니다.', 'error');
        }
    },

    async deleteUser(userId) {
        confirmAction('정말로 이 사용자를 삭제하시겠습니까?', async () => {
            try {
                const response = await apiDelete(`/api/admin/users/${userId}`);
                
                if (response.success !== false) {
                    showMessage('사용자가 삭제되었습니다.', 'success');
                    this.loadUsers();
                } else {
                    showMessage(response.message || '사용자 삭제 중 오류가 발생했습니다.', 'error');
                }
            } catch (error) {
                console.error('사용자 삭제 오류:', error);
                showMessage('사용자 삭제 중 오류가 발생했습니다.', 'error');
            }
        });
    },

    async resetPassword(userId) {
        confirmAction('이 사용자의 비밀번호를 초기화하시겠습니까?', async () => {
            try {
                const response = await apiPost(`/api/admin/users/${userId}/reset-password`);
                
                if (response.success && response.temporary_password) {
                    alert(`비밀번호가 초기화되었습니다.\\n임시 비밀번호: ${response.temporary_password}`);
                } else {
                    showMessage(response.message || '비밀번호 초기화 중 오류가 발생했습니다.', 'error');
                }
            } catch (error) {
                console.error('비밀번호 초기화 오류:', error);
                showMessage('비밀번호 초기화 중 오류가 발생했습니다.', 'error');
            }
        });
    }
};

console.log('👥 Users Module 준비됨');