/**
 * 사업장 관리 모듈
 * - 사업장 CRUD 작업
 * - 사업장 검색 및 필터링
 * - 사업장 상태 관리
 */

window.SitesModule = {
    currentPage: 1,
    pageSize: 20,
    totalPages: 0,
    editingSiteId: null,

    async load() {
        console.log('🏢 Sites Module 로딩 시작...');
        await this.render();
        await this.loadSites();
        this.setupEventListeners();
        console.log('🏢 Sites Module 로드됨');
    },

    async render() {
        const container = document.getElementById('sites-module');
        if (!container) return;

        container.innerHTML = `
            <style>
            .sites-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }

            .sites-header {
                background: white;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                margin-bottom: 25px;
            }

            .sites-header h1 {
                margin: 0 0 10px 0;
                color: #2c3e50;
                font-size: 28px;
                font-weight: 600;
            }

            .sites-header p {
                margin: 0;
                color: #7f8c8d;
                font-size: 16px;
            }

            .sites-toolbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                gap: 15px;
                flex-wrap: wrap;
            }

            .search-box {
                display: flex;
                align-items: center;
                gap: 10px;
                flex: 1;
                max-width: 400px;
            }

            .search-box input {
                flex: 1;
                padding: 12px 15px;
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                font-size: 14px;
                transition: border-color 0.3s;
            }

            .search-box input:focus {
                outline: none;
                border-color: #667eea;
            }

            .sites-content {
                background: white;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                overflow: hidden;
            }

            .sites-table {
                width: 100%;
                border-collapse: collapse;
                margin: 0;
            }

            .sites-table th,
            .sites-table td {
                padding: 15px;
                text-align: left;
                border-bottom: 1px solid #f1f3f4;
                vertical-align: middle;
            }

            .sites-table th {
                background: #f8f9fa;
                font-weight: 600;
                color: #333;
            }

            .sites-table tr:hover {
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
                color: #aaa;
                cursor: pointer;
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
            .form-group select,
            .form-group textarea {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }

            .form-group textarea {
                height: 80px;
                resize: vertical;
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
                align-items: center;
                padding: 20px;
                gap: 10px;
            }

            .pagination button {
                padding: 8px 12px;
                border: 1px solid #ddd;
                background: white;
                cursor: pointer;
                border-radius: 4px;
            }

            .pagination button:hover {
                background: #f8f9fa;
            }

            .pagination button.active {
                background: #667eea;
                color: white;
                border-color: #667eea;
            }

            .pagination button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }

            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-left: 4px solid #667eea;
            }

            .stat-card h3 {
                margin: 0;
                font-size: 32px;
                color: #667eea;
                font-weight: 700;
            }

            .stat-card p {
                margin: 0;
                color: #666;
                font-size: 16px;
                font-weight: 500;
            }

            .stat-icon {
                font-size: 36px;
                opacity: 0.7;
            }
            </style>

            <div class="sites-container">
                <!-- 헤더 -->
                <div class="sites-header">
                    <h1>🏢 사업장 관리</h1>
                    <p>사업장 정보를 등록하고 관리합니다</p>
                </div>

                <!-- 통계 -->
                <div class="stats-grid" id="sites-stats">
                    <div class="stat-card" style="border-left-color: #667eea;">
                        <div>
                            <p>전체 사업장</p>
                            <h3 id="total-sites">-</h3>
                        </div>
                        <div class="stat-icon">🏢</div>
                    </div>
                    <div class="stat-card" style="border-left-color: #28a745;">
                        <div>
                            <p>활성 사업장</p>
                            <h3 id="active-sites">-</h3>
                        </div>
                        <div class="stat-icon">✅</div>
                    </div>
                    <div class="stat-card" style="border-left-color: #dc3545;">
                        <div>
                            <p>비활성 사업장</p>
                            <h3 id="inactive-sites">-</h3>
                        </div>
                        <div class="stat-icon">❌</div>
                    </div>
                </div>

                <!-- 툴바 -->
                <div class="sites-toolbar">
                    <div class="search-box">
                        <input type="text" id="site-search" placeholder="사업장명, 주소로 검색...">
                        <button class="btn btn-secondary" onclick="SitesModule.searchSites()">🔍</button>
                    </div>
                    <button class="btn btn-primary" onclick="SitesModule.showCreateModal()">+ 새 사업장</button>
                </div>

                <!-- 사업장 목록 -->
                <div class="sites-content">
                    <table class="sites-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>사업장명</th>
                                <th>주소</th>
                                <th>연락처</th>
                                <th>상태</th>
                                <th>등록일</th>
                                <th>작업</th>
                            </tr>
                        </thead>
                        <tbody id="sites-table-body">
                            <tr>
                                <td colspan="7" class="loading-cell">사업장 목록을 불러오는 중...</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <!-- 페이지네이션 -->
                    <div class="pagination" id="sites-pagination">
                        <!-- 페이지네이션 버튼들이 여기에 동적으로 생성됩니다 -->
                    </div>
                </div>
            </div>

            <!-- 사업장 생성/수정 모달 -->
            <div id="site-modal" class="modal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 id="modal-title">새 사업장</h3>
                        <span class="modal-close" onclick="SitesModule.closeModal()">&times;</span>
                    </div>
                    <div class="modal-body">
                        <form id="site-form" onsubmit="SitesModule.saveSite(event)">
                            <div class="form-group">
                                <label for="site_name">사업장명 *</label>
                                <input type="text" id="site_name" name="site_name" required>
                            </div>
                            <div class="form-group">
                                <label for="address">주소</label>
                                <input type="text" id="address" name="address">
                            </div>
                            <div class="form-group">
                                <label for="contact_info">연락처</label>
                                <input type="text" id="contact_info" name="contact_info">
                            </div>
                            <div class="form-group">
                                <label for="description">설명</label>
                                <textarea id="description" name="description" placeholder="사업장에 대한 추가 설명..."></textarea>
                            </div>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="is_active" name="is_active" checked>
                                    활성화
                                </label>
                            </div>
                            <div class="form-actions">
                                <button type="submit" class="btn btn-primary">저장</button>
                                <button type="button" class="btn btn-secondary" onclick="SitesModule.closeModal()">취소</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;
    },

    setupEventListeners() {
        // 검색 엔터키 처리
        const searchInput = document.getElementById('site-search');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchSites();
                }
            });
        }

        // 모달 외부 클릭시 닫기
        const modal = document.getElementById('site-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal();
                }
            });
        }
    },

    async loadSites() {
        try {
            const search = document.getElementById('site-search')?.value || '';
            
            console.log(`Loading sites - page: ${this.currentPage}, search: "${search}"`);
            
            const response = await apiGet(`/api/admin/sites?page=${this.currentPage}&limit=${this.pageSize}&search=${encodeURIComponent(search)}`);
            
            console.log('Sites response:', response);
            
            if (response.success) {
                this.renderSites(response.sites || []);
                this.updatePagination(response.total, response.page, response.limit);
                await this.loadSiteStats();
            } else {
                showMessage('사업장 목록을 불러올 수 없습니다.', 'error');
                this.renderSites([]);
            }
        } catch (error) {
            console.error('사업장 로드 중 오류:', error);
            console.error('Error message:', error.message);
            console.error('Error stack:', error.stack);
            showMessage('사업장 목록을 불러오는 중 오류가 발생했습니다.', 'error');
            this.renderSites([]);
        }
    },

    async loadSiteStats() {
        try {
            const response = await apiGet('/api/admin/site-stats');
            if (response.success) {
                const stats = response.stats;
                document.getElementById('total-sites').textContent = stats.total_sites || 0;
                document.getElementById('active-sites').textContent = stats.active_sites || 0;
                document.getElementById('inactive-sites').textContent = stats.inactive_sites || 0;
            }
        } catch (error) {
            console.error('사업장 통계 로드 중 오류:', error);
        }
    },

    renderSites(sites) {
        const tbody = document.getElementById('sites-table-body');
        if (!tbody) return;

        if (sites.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="loading-cell">등록된 사업장이 없습니다.</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = sites.map(site => `
            <tr>
                <td>${site.id}</td>
                <td><strong>${site.site_name}</strong></td>
                <td>${site.address || '-'}</td>
                <td>${site.contact_info || '-'}</td>
                <td>
                    <span class="status-badge ${site.is_active ? 'status-active' : 'status-inactive'}">
                        ${site.is_active ? '활성' : '비활성'}
                    </span>
                </td>
                <td>${site.created_at ? new Date(site.created_at).toLocaleDateString() : '-'}</td>
                <td>
                    <button class="btn btn-sm btn-warning" onclick="SitesModule.editSite(${site.id})">수정</button>
                    <button class="btn btn-sm btn-danger" onclick="SitesModule.deleteSite(${site.id})">삭제</button>
                </td>
            </tr>
        `).join('');
    },

    updatePagination(total, page, limit) {
        this.totalPages = Math.ceil(total / limit);
        this.currentPage = page;

        const paginationContainer = document.getElementById('sites-pagination');
        if (!paginationContainer) return;

        let paginationHTML = '';

        // 이전 페이지
        paginationHTML += `
            <button ${this.currentPage <= 1 ? 'disabled' : ''} onclick="SitesModule.goToPage(${this.currentPage - 1})">
                이전
            </button>
        `;

        // 페이지 번호들
        for (let i = Math.max(1, this.currentPage - 2); i <= Math.min(this.totalPages, this.currentPage + 2); i++) {
            paginationHTML += `
                <button class="${i === this.currentPage ? 'active' : ''}" onclick="SitesModule.goToPage(${i})">
                    ${i}
                </button>
            `;
        }

        // 다음 페이지
        paginationHTML += `
            <button ${this.currentPage >= this.totalPages ? 'disabled' : ''} onclick="SitesModule.goToPage(${this.currentPage + 1})">
                다음
            </button>
        `;

        paginationContainer.innerHTML = paginationHTML;
    },

    goToPage(page) {
        if (page >= 1 && page <= this.totalPages) {
            this.currentPage = page;
            this.loadSites();
        }
    },

    searchSites() {
        this.currentPage = 1;
        this.loadSites();
    },

    showCreateModal() {
        document.getElementById('modal-title').textContent = '새 사업장';
        document.getElementById('site-form').reset();
        
        // 기본값 설정
        document.getElementById('is_active').checked = true;
        
        document.getElementById('site-modal').style.display = 'block';
        this.editingSiteId = null;
    },

    closeModal() {
        document.getElementById('site-modal').style.display = 'none';
        document.getElementById('site-form').reset();
        this.editingSiteId = null;
    },

    async saveSite(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const siteData = {
            site_name: formData.get('site_name'),
            address: formData.get('address'),
            contact_info: formData.get('contact_info'),
            description: formData.get('description'),
            is_active: formData.has('is_active')
        };

        try {
            let response;
            if (this.editingSiteId) {
                response = await apiPut(`/api/admin/sites/${this.editingSiteId}`, siteData);
            } else {
                console.log('Sending site data:', siteData);
                response = await apiPost('/api/admin/sites', siteData);
            }

            if (response.success !== false) {
                showMessage(this.editingSiteId ? '사업장이 수정되었습니다.' : '사업장이 추가되었습니다.', 'success');
                this.closeModal();
                this.loadSites();
            } else {
                showMessage(response.message || '저장 중 오류가 발생했습니다.', 'error');
            }
        } catch (error) {
            console.error('사업장 저장 중 오류:', error);
            
            if (error.message.includes('422')) {
                showMessage('입력 데이터를 확인해 주세요.', 'error');
            } else if (error.message.includes('400')) {
                showMessage('이미 존재하는 사업장명입니다.', 'error');
            } else {
                showMessage('사업장 저장 중 오류가 발생했습니다.', 'error');
            }
        }
    },

    async editSite(siteId) {
        try {
            const response = await apiGet(`/api/admin/sites/${siteId}`);
            
            if (response.success !== false) {
                const site = response.site || response;
                
                document.getElementById('modal-title').textContent = '사업장 수정';
                document.getElementById('site_name').value = site.site_name;
                document.getElementById('address').value = site.address || '';
                document.getElementById('contact_info').value = site.contact_info || '';
                document.getElementById('description').value = site.description || '';
                document.getElementById('is_active').checked = site.is_active;
                
                this.editingSiteId = siteId;
                document.getElementById('site-modal').style.display = 'block';
            } else {
                showMessage('사업장 정보를 불러올 수 없습니다.', 'error');
            }
        } catch (error) {
            console.error('사업장 로드 중 오류:', error);
            showMessage('사업장 정보를 불러오는 중 오류가 발생했습니다.', 'error');
        }
    },

    async deleteSite(siteId) {
        if (!confirm('정말로 이 사업장을 삭제하시겠습니까?')) {
            return;
        }

        try {
            const response = await apiDelete(`/api/admin/sites/${siteId}`);
            
            if (response.success !== false) {
                showMessage('사업장이 삭제되었습니다.', 'success');
                this.loadSites();
            } else {
                showMessage('사업장 삭제 중 오류가 발생했습니다.', 'error');
            }
        } catch (error) {
            console.error('사업장 삭제 중 오류:', error);
            showMessage('사업장 삭제 중 오류가 발생했습니다.', 'error');
        }
    }
};

console.log('🏢 Sites Module 정의됨');