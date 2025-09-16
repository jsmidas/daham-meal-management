/**
 * 사용자 관리 모듈 (개선 버전)
 * 권한 관리 가이드라인 기반 구현
 */

class EnhancedUserManagement {
    constructor() {
        this.API_BASE_URL = window.CONFIG?.API_BASE_URL || 'http://127.0.0.1:8010';
        this.currentUserId = null;
        this.isEditMode = false;
        this.users = [];
        this.filteredUsers = [];
        this.businessLocations = [];
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.isSaving = false;  // 중복 저장 방지 플래그
    }

    // 권한 레벨 정의
    static PERMISSION_LEVELS = {
        SYSTEM_ADMIN: { role: 'admin', operator: true, label: '시스템 관리자', level: 1, color: '#dc3545' },
        SITE_ADMIN: { role: 'admin', operator: false, label: '사업장 관리자', level: 2, color: '#ffc107' },
        NUTRITIONIST: { role: 'nutritionist', operator: false, label: '영양사', level: 3, color: '#28a745' },
        OPERATOR: { role: 'operator', semi_operator: true, label: '운영 담당자', level: 4, color: '#17a2b8' },
        VIEWER: { role: 'viewer', operator: false, label: '조회 전용', level: 5, color: '#6c757d' }
    };

    // 권한별 기능 매트릭스
    static PERMISSION_MATRIX = {
        '사용자 관리': { 1: 'full', 2: 'limited', 3: 'none', 4: 'none', 5: 'none' },
        '사업장 관리': { 1: 'full', 2: 'limited', 3: 'view', 4: 'view', 5: 'view' },
        '협력업체 관리': { 1: 'full', 2: 'full', 3: 'view', 4: 'full', 5: 'view' },
        '식재료 관리': { 1: 'full', 2: 'full', 3: 'full', 4: 'full', 5: 'view' },
        '메뉴/레시피': { 1: 'full', 2: 'full', 3: 'full', 4: 'view', 5: 'view' },
        '식단 관리': { 1: 'full', 2: 'full', 3: 'full', 4: 'view', 5: 'view' },
        '발주 관리': { 1: 'full', 2: 'approve', 3: 'view', 4: 'full', 5: 'view' },
        '입고 관리': { 1: 'full', 2: 'full', 3: 'view', 4: 'full', 5: 'view' },
        '전처리 지시서': { 1: 'full', 2: 'full', 3: 'full', 4: 'full', 5: 'view' },
        '통계/보고서': { 1: 'full', 2: 'limited', 3: 'full', 4: 'full', 5: 'view' }
    };

    async init() {
        console.log('🚀 [Enhanced User Management] 초기화 시작');
        this.renderHTML();
        this.setupEventListeners();
        await this.loadBusinessLocations();
        await this.loadUsers();
    }

    renderHTML() {
        const container = document.getElementById('users-content') || document.getElementById('content-area');
        if (!container) return;

        container.innerHTML = `
            <div class="enhanced-user-management">
                <!-- 헤더 -->
                <div class="page-header">
                    <h1><i class="fas fa-users"></i> 사용자 관리</h1>
                    <button class="btn btn-primary" onclick="enhancedUserMgmt.openUserModal()">
                        <i class="fas fa-plus"></i> 사용자 추가
                    </button>
                </div>

                <!-- 통계 카드 -->
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-icon bg-primary"><i class="fas fa-users"></i></div>
                        <div class="stat-content">
                            <h3 id="totalUsers">0</h3>
                            <p>전체 사용자</p>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon bg-success"><i class="fas fa-user-check"></i></div>
                        <div class="stat-content">
                            <h3 id="activeUsers">0</h3>
                            <p>활성 사용자</p>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon bg-danger"><i class="fas fa-user-shield"></i></div>
                        <div class="stat-content">
                            <h3 id="adminUsers">0</h3>
                            <p>관리자</p>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon bg-info"><i class="fas fa-user-nurse"></i></div>
                        <div class="stat-content">
                            <h3 id="nutritionistUsers">0</h3>
                            <p>영양사</p>
                        </div>
                    </div>
                </div>

                <!-- 개선된 검색 박스 -->
                <div class="search-filter-section">
                    <div class="enhanced-search-box">
                        <i class="fas fa-search"></i>
                        <input type="text" id="userSearchInput" placeholder="이름, 아이디, 연락처, 부서로 검색..."
                               onkeyup="enhancedUserMgmt.searchUsers(this.value)">
                        <button class="clear-search" onclick="enhancedUserMgmt.clearSearch()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>

                    <div class="filter-buttons">
                        <select id="roleFilter" onchange="enhancedUserMgmt.filterByRole(this.value)">
                            <option value="">모든 권한</option>
                            <option value="1">시스템 관리자</option>
                            <option value="2">사업장 관리자</option>
                            <option value="3">영양사</option>
                            <option value="4">운영 담당자</option>
                            <option value="5">조회 전용</option>
                        </select>

                        <select id="statusFilter" onchange="enhancedUserMgmt.filterByStatus(this.value)">
                            <option value="">모든 상태</option>
                            <option value="active">활성</option>
                            <option value="inactive">비활성</option>
                            <option value="locked">잠김</option>
                        </select>
                    </div>
                </div>

                <!-- 권한별 기능 매트릭스 표 -->
                <div class="permission-matrix-section" style="display: none;">
                    <h3>권한별 기능 매트릭스</h3>
                    <table class="permission-matrix-table">
                        <thead>
                            <tr>
                                <th>기능 모듈</th>
                                <th>시스템관리자</th>
                                <th>사업장관리자</th>
                                <th>영양사</th>
                                <th>운영담당자</th>
                                <th>조회전용</th>
                            </tr>
                        </thead>
                        <tbody id="permissionMatrixBody"></tbody>
                    </table>
                </div>

                <!-- 사용자 테이블 -->
                <div class="users-table-container">
                    <table class="enhanced-users-table">
                        <thead>
                            <tr>
                                <th width="30"><input type="checkbox" id="selectAll"></th>
                                <th>사용자 정보</th>
                                <th>권한 레벨</th>
                                <th>사업장</th>
                                <th>상태</th>
                                <th>마지막 로그인</th>
                                <th>수정/초기화/삭제</th>
                            </tr>
                        </thead>
                        <tbody id="usersTableBody"></tbody>
                    </table>
                </div>

                <!-- 페이지네이션 -->
                <div class="pagination-container" id="pagination"></div>
            </div>
        `;

        this.addStyles();
    }

    addStyles() {
        if (document.getElementById('enhanced-user-styles')) return;

        const style = document.createElement('style');
        style.id = 'enhanced-user-styles';
        style.textContent = `
            .enhanced-user-management {
                padding: 20px;
                max-width: 1400px;
                margin: 0 auto;
            }

            .page-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
                padding-bottom: 15px;
                border-bottom: 2px solid #e0e0e0;
            }

            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }

            .stat-card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                display: flex;
                align-items: center;
                gap: 15px;
                transition: transform 0.3s;
            }

            .stat-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.12);
            }

            .stat-icon {
                width: 60px;
                height: 60px;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                color: white;
            }

            .stat-icon.bg-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .stat-icon.bg-success { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
            .stat-icon.bg-danger { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
            .stat-icon.bg-info { background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); }

            .search-filter-section {
                display: flex;
                gap: 20px;
                margin-bottom: 30px;
                flex-wrap: wrap;
            }

            .enhanced-search-box {
                flex: 1;
                min-width: 300px;
                position: relative;
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                overflow: hidden;
            }

            .enhanced-search-box i {
                position: absolute;
                left: 15px;
                top: 50%;
                transform: translateY(-50%);
                color: #999;
            }

            .enhanced-search-box input {
                width: 100%;
                padding: 15px 45px;
                border: none;
                outline: none;
                font-size: 15px;
            }

            .enhanced-search-box .clear-search {
                position: absolute;
                right: 15px;
                top: 50%;
                transform: translateY(-50%);
                background: none;
                border: none;
                color: #999;
                cursor: pointer;
                padding: 5px;
            }

            .filter-buttons {
                display: flex;
                gap: 10px;
            }

            .filter-buttons select {
                padding: 12px 20px;
                border: 1px solid #ddd;
                border-radius: 8px;
                background: white;
                cursor: pointer;
                font-size: 14px;
            }

            .enhanced-users-table {
                width: 100%;
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            }

            .enhanced-users-table thead {
                background: #f8f9fa;
            }

            .enhanced-users-table th {
                padding: 15px;
                text-align: left;
                font-weight: 600;
                color: #333;
                border-bottom: 2px solid #e0e0e0;
            }

            .enhanced-users-table td {
                padding: 15px;
                border-bottom: 1px solid #f0f0f0;
            }

            .user-info-cell {
                display: flex;
                align-items: center;
                gap: 15px;
            }

            .user-avatar {
                width: 45px;
                height: 45px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 18px;
            }

            .user-details h4 {
                margin: 0 0 5px 0;
                font-size: 16px;
                color: #333;
            }

            .user-details p {
                margin: 0;
                font-size: 13px;
                color: #666;
            }

            .permission-badge {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 600;
                color: white;
            }

            .status-badge {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: 600;
            }

            .status-active { background: #d4edda; color: #155724; }
            .status-inactive { background: #f8d7da; color: #721c24; }
            .status-locked { background: #fff3cd; color: #856404; }

            .action-buttons {
                display: flex;
                gap: 8px;
            }

            .action-buttons button {
                padding: 8px 12px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s;
            }

            .btn-edit {
                background: #007bff;
                color: white;
            }

            .btn-password {
                background: #ffc107;
                color: #333;
            }

            .btn-delete {
                background: #dc3545;
                color: white;
            }

            .permission-matrix-table {
                width: 100%;
                background: white;
                border-radius: 10px;
                overflow: hidden;
                margin-top: 20px;
            }

            .permission-matrix-table th {
                background: #f8f9fa;
                padding: 12px;
                text-align: center;
                font-size: 14px;
            }

            .permission-matrix-table td {
                padding: 10px;
                text-align: center;
                border: 1px solid #e0e0e0;
            }

            .permission-icon {
                font-size: 18px;
            }

            .permission-full { color: #28a745; }
            .permission-limited { color: #ffc107; }
            .permission-view { color: #17a2b8; }
            .permission-none { color: #dc3545; }
        `;
        document.head.appendChild(style);
    }

    setupEventListeners() {
        // 전체 선택 체크박스
        const selectAll = document.getElementById('selectAll');
        if (selectAll) {
            selectAll.addEventListener('change', (e) => {
                const checkboxes = document.querySelectorAll('.user-checkbox');
                checkboxes.forEach(cb => cb.checked = e.target.checked);
            });
        }
    }

    async loadUsers() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/api/admin/users`);
            const data = await response.json();

            if (data.success) {
                this.users = data.users || [];
                this.filteredUsers = [...this.users];
                this.updateStats();
                this.renderUsers();
                this.renderPermissionMatrix();
            }
        } catch (error) {
            console.error('사용자 로드 실패:', error);
        }
    }

    updateStats() {
        document.getElementById('totalUsers').textContent = this.users.length;
        document.getElementById('activeUsers').textContent =
            this.users.filter(u => u.is_active).length;
        document.getElementById('adminUsers').textContent =
            this.users.filter(u => u.role === 'admin').length;
        document.getElementById('nutritionistUsers').textContent =
            this.users.filter(u => u.role === 'nutritionist').length;
    }

    renderUsers() {
        const tbody = document.getElementById('usersTableBody');
        if (!tbody) return;

        const start = (this.currentPage - 1) * this.itemsPerPage;
        const end = start + this.itemsPerPage;
        const pageUsers = this.filteredUsers.slice(start, end);

        tbody.innerHTML = pageUsers.map(user => {
            const permissionLevel = this.getUserPermissionLevel(user);
            const permissionInfo = this.getPermissionInfo(permissionLevel);

            return `
                <tr>
                    <td><input type="checkbox" class="user-checkbox" value="${user.id}"></td>
                    <td>
                        <div class="user-info-cell">
                            <div class="user-avatar">${user.username.charAt(0).toUpperCase()}</div>
                            <div class="user-details">
                                <h4>${user.username}</h4>
                                <p>${user.contact_info || '연락처 없음'} | ${user.department || '부서 없음'}</p>
                            </div>
                        </div>
                    </td>
                    <td>
                        <span class="permission-badge" style="background: ${permissionInfo.color}">
                            ${permissionInfo.label}
                        </span>
                    </td>
                    <td>${user.managed_site || '전체'}</td>
                    <td>
                        <span class="status-badge status-${user.is_active ? 'active' : 'inactive'}">
                            ${user.is_active ? '활성' : '비활성'}
                        </span>
                    </td>
                    <td>${this.formatDate(user.last_login) || '없음'}</td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn-edit" onclick="enhancedUserMgmt.editUser(${user.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn-password" onclick="enhancedUserMgmt.resetPassword(${user.id})">
                                <i class="fas fa-key"></i>
                            </button>
                            <button class="btn-delete" onclick="enhancedUserMgmt.deleteUser(${user.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        this.renderPagination();
    }

    renderPermissionMatrix() {
        const tbody = document.getElementById('permissionMatrixBody');
        if (!tbody) return;

        tbody.innerHTML = Object.entries(EnhancedUserManagement.PERMISSION_MATRIX).map(([module, permissions]) => {
            return `
                <tr>
                    <td><strong>${module}</strong></td>
                    ${[1, 2, 3, 4, 5].map(level => {
                        const permission = permissions[level];
                        let icon, className;

                        switch(permission) {
                            case 'full':
                                icon = '✅';
                                className = 'permission-full';
                                break;
                            case 'limited':
                            case 'approve':
                                icon = '⚠️';
                                className = 'permission-limited';
                                break;
                            case 'view':
                                icon = '👁️';
                                className = 'permission-view';
                                break;
                            case 'none':
                                icon = '❌';
                                className = 'permission-none';
                                break;
                        }

                        return `<td class="${className}"><span class="permission-icon">${icon}</span></td>`;
                    }).join('')}
                </tr>
            `;
        }).join('');
    }

    getUserPermissionLevel(user) {
        if (user.role === 'admin' && user.operator) return 1;
        if (user.role === 'admin') return 2;
        if (user.role === 'nutritionist') return 3;
        if (user.semi_operator) return 4;
        return 5;
    }

    getPermissionInfo(level) {
        const levels = Object.values(EnhancedUserManagement.PERMISSION_LEVELS);
        return levels.find(l => l.level === level) || levels[levels.length - 1];
    }

    searchUsers(query) {
        query = query.toLowerCase().trim();

        if (!query) {
            this.filteredUsers = [...this.users];
        } else {
            this.filteredUsers = this.users.filter(user =>
                user.username.toLowerCase().includes(query) ||
                (user.contact_info && user.contact_info.toLowerCase().includes(query)) ||
                (user.department && user.department.toLowerCase().includes(query))
            );
        }

        this.currentPage = 1;
        this.renderUsers();
    }

    clearSearch() {
        document.getElementById('userSearchInput').value = '';
        this.filteredUsers = [...this.users];
        this.renderUsers();
    }

    filterByRole(level) {
        if (!level) {
            this.filteredUsers = [...this.users];
        } else {
            this.filteredUsers = this.users.filter(user =>
                this.getUserPermissionLevel(user) === parseInt(level)
            );
        }
        this.currentPage = 1;
        this.renderUsers();
    }

    filterByStatus(status) {
        if (!status) {
            this.filteredUsers = [...this.users];
        } else {
            this.filteredUsers = this.users.filter(user => {
                if (status === 'active') return user.is_active;
                if (status === 'inactive') return !user.is_active;
                if (status === 'locked') return user.is_locked;
                return true;
            });
        }
        this.currentPage = 1;
        this.renderUsers();
    }

    renderPagination() {
        const totalPages = Math.ceil(this.filteredUsers.length / this.itemsPerPage);
        const pagination = document.getElementById('pagination');
        if (!pagination) return;

        let html = '';

        if (totalPages > 1) {
            html += `<button onclick="enhancedUserMgmt.goToPage(${this.currentPage - 1})"
                     ${this.currentPage === 1 ? 'disabled' : ''}>이전</button>`;

            for (let i = 1; i <= totalPages; i++) {
                html += `<button onclick="enhancedUserMgmt.goToPage(${i})"
                        class="${this.currentPage === i ? 'active' : ''}">${i}</button>`;
            }

            html += `<button onclick="enhancedUserMgmt.goToPage(${this.currentPage + 1})"
                     ${this.currentPage === totalPages ? 'disabled' : ''}>다음</button>`;
        }

        pagination.innerHTML = html;
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredUsers.length / this.itemsPerPage);
        if (page < 1 || page > totalPages) return;

        this.currentPage = page;
        this.renderUsers();
    }

    openUserModal(userId = null) {
        this.showCompactModal(userId);
    }

    showCompactModal(userId = null) {
        const isEdit = userId !== null;
        const user = isEdit ? this.users.find(u => u.id === userId) : null;

        const modalHtml = `
            <div id="userModal" class="modal-overlay">
                <div class="compact-modal">
                    <div class="modal-header">
                        <h2>${isEdit ? '사용자 수정' : '새 사용자 추가'}</h2>
                        <button class="close-btn" onclick="enhancedUserMgmt.closeModal()">×</button>
                    </div>

                    <form id="userForm">
                        <div class="ultra-compact-grid">
                            <!-- 좌측: 기본 정보 + 추가 옵션 -->
                            <div class="left-column">
                                <div class="form-section-compact">
                                    <h4>기본 정보</h4>
                                    <div class="form-row-compact">
                                        <div class="form-group-compact">
                                            <label>사용자명*</label>
                                            <input type="text" name="username" value="${isEdit && user ? user.username : ''}" required>
                                        </div>
                                        <div class="form-group-compact">
                                            <label>비밀번호${isEdit ? '' : '*'}</label>
                                            <input type="password" name="password" ${isEdit ? '' : 'required'}
                                                   placeholder="${isEdit ? '변경시 입력' : ''}">
                                        </div>
                                    </div>
                                    <div class="form-row-compact">
                                        <div class="form-group-compact">
                                            <label>연락처</label>
                                            <input type="text" name="contact_info" value="${isEdit && user ? (user.contact_info || '') : ''}">
                                        </div>
                                        <div class="form-group-compact">
                                            <label>직책</label>
                                            <input type="text" name="position" value="${isEdit && user ? (user.position || '') : ''}">
                                        </div>
                                    </div>
                                    <div class="form-row-compact">
                                        <div class="form-group-compact">
                                            <label>부서</label>
                                            <input type="text" name="department" value="${isEdit && user ? (user.department || '') : ''}">
                                        </div>
                                        <div class="form-group-compact">
                                            <label>직책</label>
                                            <input type="text" name="position" value="${isEdit && user ? (user.position || '') : ''}">
                                        </div>
                                    </div>
                                </div>

                                <div class="form-section-compact">
                                    <h4>추가 옵션</h4>
                                    <div class="checkbox-group-compact">
                                        <label>
                                            <input type="checkbox" name="is_active" ${!isEdit || (user && user.is_active !== false) ? 'checked' : ''}>
                                            <span>계정 활성화</span>
                                        </label>
                                        <label>
                                            <input type="checkbox" name="email_notifications" ${isEdit && user && user.email_notifications ? 'checked' : ''}>
                                            <span>이메일 알림</span>
                                        </label>
                                    </div>
                                </div>
                            </div>

                            <!-- 우측: 권한 설정 -->
                            <div class="right-column">
                                <div class="form-section-compact">
                                    <h4>권한 설정</h4>
                                    <div class="permission-selector-compact">
                                        <label class="permission-label-compact">
                                            <input type="radio" name="permission_level" value="1"
                                                   ${user && this.getUserPermissionLevel(user) === 1 ? 'checked' : ''}>
                                            <div class="permission-info">
                                                <span class="permission-title" style="color: #dc3545">시스템 관리자</span>
                                                <span class="permission-desc">모든 기능 접근</span>
                                            </div>
                                        </label>
                                        <label class="permission-label-compact">
                                            <input type="radio" name="permission_level" value="2"
                                                   ${user && this.getUserPermissionLevel(user) === 2 ? 'checked' : ''}>
                                            <div class="permission-info">
                                                <span class="permission-title" style="color: #ffc107">사업장 관리자</span>
                                                <span class="permission-desc">담당 사업장 관리</span>
                                            </div>
                                        </label>
                                        <label class="permission-label-compact">
                                            <input type="radio" name="permission_level" value="3"
                                                   ${user && this.getUserPermissionLevel(user) === 3 ? 'checked' : ''}>
                                            <div class="permission-info">
                                                <span class="permission-title" style="color: #28a745">영양사</span>
                                                <span class="permission-desc">식단/메뉴 관리</span>
                                            </div>
                                        </label>
                                        <label class="permission-label-compact">
                                            <input type="radio" name="permission_level" value="4"
                                                   ${user && this.getUserPermissionLevel(user) === 4 ? 'checked' : ''}>
                                            <div class="permission-info">
                                                <span class="permission-title" style="color: #17a2b8">운영 담당자</span>
                                                <span class="permission-desc">일일 운영</span>
                                            </div>
                                        </label>
                                        <label class="permission-label-compact">
                                            <input type="radio" name="permission_level" value="5"
                                                   ${!user || this.getUserPermissionLevel(user) === 5 ? 'checked' : ''}>
                                            <div class="permission-info">
                                                <span class="permission-title" style="color: #6c757d">조회 전용</span>
                                                <span class="permission-desc">읽기 전용</span>
                                            </div>
                                        </label>
                                    </div>

                                    <div class="form-group-compact" style="margin-top: 15px;">
                                        <label>관리 사업장</label>
                                        <select name="managed_site">
                                            <option value="">전체</option>
                                            ${this.businessLocations.map(loc => `
                                                <option value="${loc.site_name || loc.name}"
                                                    ${isEdit && user && user.managed_site === (loc.site_name || loc.name) ? 'selected' : ''}>
                                                    ${loc.site_name || loc.name}
                                                </option>
                                            `).join('')}
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="modal-footer">
                            <div class="footer-buttons">
                                <button type="button" class="btn btn-secondary" onclick="enhancedUserMgmt.closeModal()">취소</button>
                                <button type="submit" class="btn btn-primary">
                                    ${isEdit ? '수정' : '추가'}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.addModalStyles();

        // 폼 이벤트 리스너 등록 (한 번만)
        const form = document.getElementById('userForm');
        if (form) {
            form.onsubmit = (e) => this.saveUser(e);
        }

        // 수정 모드일 때 데이터 로드
        if (userId && user) {
            this.loadUserDataToForm(user);
        }
    }

    loadUserDataToForm(user) {
        // 사용자 데이터를 폼에 로드
        const form = document.getElementById('userForm');
        if (!form) return;

        // 기본 정보
        if (form.username) form.username.value = user.username || '';
        if (form.contact_info) form.contact_info.value = user.contact_info || '';
        if (form.department) form.department.value = user.department || '';
        if (form.position) form.position.value = user.position || '';
        if (form.managed_site) form.managed_site.value = user.managed_site || '';

        // 권한 레벨 설정
        let permissionLevel = 5; // 기본값: 조회 전용
        if (user.role === 'admin' && user.operator) permissionLevel = 1;
        else if (user.role === 'admin') permissionLevel = 2;
        else if (user.role === 'nutritionist') permissionLevel = 3;
        else if (user.role === 'operator' || user.semi_operator) permissionLevel = 4;

        if (form.permission_level) {
            const radioButtons = form.querySelectorAll('input[name="permission_level"]');
            radioButtons.forEach(radio => {
                if (parseInt(radio.value) === permissionLevel) {
                    radio.checked = true;
                }
            });
        }

        // 활성 상태
        if (form.is_active) form.is_active.checked = user.is_active;
    }

    addModalStyles() {
        if (document.getElementById('compact-modal-styles')) return;

        const style = document.createElement('style');
        style.id = 'compact-modal-styles';
        style.textContent = `
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
            }

            .compact-modal {
                background: white;
                border-radius: 10px;
                width: 90%;
                max-width: 800px;
                max-height: 85vh;
                overflow: hidden;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }

            .compact-modal .modal-header {
                padding: 12px 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .compact-modal .modal-header h2 {
                margin: 0;
                font-size: 18px;
            }

            .compact-modal .close-btn {
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: white;
                opacity: 0.8;
            }

            .compact-modal .modal-body {
                padding: 15px;
                background: #f8f9fa;
                max-height: calc(85vh - 120px);
                overflow-y: auto;
            }

            .ultra-compact-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }

            .form-section-compact {
                background: white;
                padding: 12px;
                border-radius: 6px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.08);
            }

            .form-section-compact h4 {
                margin: 0 0 10px 0;
                color: #333;
                font-size: 13px;
                font-weight: 600;
                border-bottom: 1px solid #e9ecef;
                padding-bottom: 5px;
            }

            .form-group-compact {
                margin-bottom: 8px;
            }

            .form-group-compact label {
                display: block;
                font-size: 11px;
                font-weight: 500;
                color: #495057;
                margin-bottom: 3px;
            }

            .form-group-compact input,
            .form-group-compact select,
            .form-group-compact textarea {
                width: 100%;
                padding: 5px 8px;
                border: 1px solid #ced4da;
                border-radius: 3px;
                font-size: 12px;
            }

            .form-group-compact input:focus,
            .form-group-compact select:focus,
            .form-group-compact textarea:focus {
                border-color: #667eea;
                outline: none;
                box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.1);
            }

            .required::after {
                content: ' *';
                color: #dc3545;
                font-size: 10px;
            }

            .radio-group-compact {
                display: flex;
                gap: 10px;
                margin-top: 3px;
                flex-wrap: wrap;
            }

            .radio-label-compact {
                display: flex;
                align-items: center;
                cursor: pointer;
                font-size: 11px;
            }

            .radio-label-compact input[type="radio"] {
                width: auto;
                margin-right: 3px;
                transform: scale(0.9);
            }

            .permission-matrix-compact {
                background: #f8f9fa;
                padding: 8px;
                border-radius: 4px;
                margin-top: 8px;
                max-height: 180px;
                overflow-y: auto;
            }

            .permission-item-compact {
                display: flex;
                align-items: center;
                padding: 4px 6px;
                margin-bottom: 3px;
                background: white;
                border-radius: 3px;
                font-size: 11px;
            }

            .permission-label-compact {
                flex: 1;
                color: #495057;
            }

            .compact-modal .modal-footer {
                padding: 12px 20px;
                background: #f8f9fa;
                border-top: 1px solid #dee2e6;
                display: flex;
                justify-content: center;
                align-items: center;
            }

            .footer-buttons {
                display: flex;
                gap: 10px;
            }

            .btn {
                padding: 6px 14px;
                border: none;
                border-radius: 4px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s;
                font-size: 12px;
            }

            .btn-primary {
                background: #667eea;
                color: white;
            }

            .btn-primary:hover {
                background: #5a67d8;
            }

            .btn-secondary {
                background: #6c757d;
                color: white;
            }

            .btn-danger {
                background: #dc3545;
                color: white;
            }

            /* 스크롤바 스타일 */
            .compact-modal .modal-body::-webkit-scrollbar,
            .permission-matrix-compact::-webkit-scrollbar {
                width: 6px;
            }

            .compact-modal .modal-body::-webkit-scrollbar-track,
            .permission-matrix-compact::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 3px;
            }

            .compact-modal .modal-body::-webkit-scrollbar-thumb,
            .permission-matrix-compact::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 3px;
            }

            .permission-selector {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }

            .permission-selector label {
                display: flex;
                align-items: center;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                cursor: pointer;
                transition: all 0.3s;
            }

            .permission-selector label:hover {
                background: #f0f0f0;
            }

            .permission-selector input[type="radio"] {
                margin-right: 10px;
            }

            .permission-option {
                display: flex;
                flex-direction: column;
            }

            .permission-option strong {
                font-size: 14px;
            }

            .permission-option small {
                font-size: 12px;
                color: #666;
            }

            .checkbox-group {
                display: flex;
                gap: 20px;
                margin-bottom: 15px;
            }

            .checkbox-group label {
                display: flex;
                align-items: center;
                gap: 5px;
                font-size: 14px;
            }

            .modal-actions {
                padding: 20px;
                border-top: 1px solid #e0e0e0;
                display: flex;
                justify-content: flex-end;
                gap: 10px;
            }

            .btn {
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.3s;
            }

            .btn-primary {
                background: #007bff;
                color: white;
            }

            .btn-secondary {
                background: #6c757d;
                color: white;
            }

            .btn-warning {
                background: #ffc107;
                color: #333;
            }

            .btn:hover {
                opacity: 0.9;
                transform: translateY(-2px);
            }
        `;
        document.head.appendChild(style);
    }

    closeModal() {
        const modal = document.getElementById('userModal');
        if (modal) modal.remove();
        this.isSaving = false;  // 플래그 초기화
        this.isEditMode = false;
        this.currentUserId = null;
    }

    async saveUser(event) {
        event.preventDefault();

        // 중복 저장 방지
        if (this.isSaving) {
            console.log('이미 저장 중입니다...');
            return;
        }

        this.isSaving = true;
        const submitButton = event.target.querySelector('button[type="submit"]');
        const originalText = submitButton ? submitButton.textContent : '';

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = '저장 중...';
        }

        const formData = new FormData(event.target);
        const userData = Object.fromEntries(formData);

        // 권한 레벨에 따라 role과 operator 설정
        const permissionLevel = parseInt(userData.permission_level);
        switch(permissionLevel) {
            case 1:
                userData.role = 'admin';
                userData.operator = true;
                userData.semi_operator = false;
                break;
            case 2:
                userData.role = 'admin';
                userData.operator = false;
                userData.semi_operator = false;
                break;
            case 3:
                userData.role = 'nutritionist';
                userData.operator = false;
                userData.semi_operator = false;
                break;
            case 4:
                userData.role = 'operator';
                userData.operator = false;
                userData.semi_operator = true;
                break;
            default:
                userData.role = 'viewer';
                userData.operator = false;
                userData.semi_operator = false;
        }

        // 불린 값 변환
        userData.is_active = userData.is_active === 'on';
        userData.email_notifications = userData.email_notifications === 'on';

        // permission_level 필드 제거 (API에서 불필요)
        delete userData.permission_level;

        // 수정 모드에서 비밀번호가 비어있으면 제거
        if (this.isEditMode && (!userData.password || userData.password === '')) {
            delete userData.password;
        }

        // 빈 문자열을 null로 변환
        Object.keys(userData).forEach(key => {
            if (userData[key] === '') {
                userData[key] = null;
            }
        });

        console.log('저장할 데이터:', userData);
        console.log('URL:', this.isEditMode ? `${this.API_BASE_URL}/api/admin/users/${this.currentUserId}` : `${this.API_BASE_URL}/api/admin/users`);

        try {
            const url = this.isEditMode ?
                `${this.API_BASE_URL}/api/admin/users/${this.currentUserId}` :
                `${this.API_BASE_URL}/api/admin/users`;

            const method = this.isEditMode ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });

            const result = await response.json();
            console.log('API 응답:', result);

            if (result.success || response.ok) {
                // 성공 시 알림 없이 바로 닫기
                this.closeModal();
                await this.loadUsers();
            } else {
                alert('오류: ' + (result.message || result.detail || '처리 실패'));
            }
        } catch (error) {
            console.error('사용자 저장 실패:', error);
            alert('사용자 저장 중 오류가 발생했습니다.\n' + error.message);
        } finally {
            // 저장 완료 후 플래그 해제
            this.isSaving = false;
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        }
    }

    editUser(userId) {
        this.isEditMode = true;
        this.currentUserId = userId;
        this.showCompactModal(userId);
    }

    async resetPassword(userId) {
        if (!confirm('이 사용자의 비밀번호를 초기화하시겠습니까?\n초기 비밀번호는 "1234"입니다.')) return;

        try {
            const response = await fetch(`${this.API_BASE_URL}/api/admin/users/${userId}/reset-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ new_password: '1234' })
            });

            const result = await response.json();

            if (result.success) {
                alert('비밀번호가 초기화되었습니다.\n초기 비밀번호: 1234');
            } else {
                alert('비밀번호 초기화 실패: ' + (result.message || ''));
            }
        } catch (error) {
            console.error('비밀번호 초기화 실패:', error);
            alert('비밀번호 초기화 중 오류가 발생했습니다.');
        }
    }

    async deleteUser(userId) {
        if (!confirm('정말로 이 사용자를 삭제하시겠습니까?')) return;

        try {
            const response = await fetch(`${this.API_BASE_URL}/api/admin/users/${userId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                alert('사용자가 삭제되었습니다.');
                await this.loadUsers();
            } else {
                alert('삭제 실패: ' + (result.message || ''));
            }
        } catch (error) {
            console.error('사용자 삭제 실패:', error);
            alert('사용자 삭제 중 오류가 발생했습니다.');
        }
    }

    formatDate(dateString) {
        if (!dateString) return null;
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR') + ' ' + date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    }

    async loadBusinessLocations() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/api/admin/business-locations`);
            const data = await response.json();
            if (data.success) {
                this.businessLocations = data.locations || [];
                console.log('✅ 사업장 정보 로드 완료:', this.businessLocations.length, '개');
            }
        } catch (error) {
            console.error('❌ 사업장 로드 실패:', error);
            // 폴백 데이터
            this.businessLocations = [
                { site_name: '도시락' },
                { site_name: '운반' },
                { site_name: '학교' },
                { site_name: '요양원' },
                { site_name: '영남 도시락' },
                { site_name: '영남 운반' }
            ];
        }
    }
}

// 전역 인스턴스 생성
window.enhancedUserMgmt = new EnhancedUserManagement();

// 자동 초기화
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (document.getElementById('users-content') || window.location.hash === '#users') {
            window.enhancedUserMgmt.init();
        }
    });
} else {
    if (document.getElementById('users-content') || window.location.hash === '#users') {
        window.enhancedUserMgmt.init();
    }
}