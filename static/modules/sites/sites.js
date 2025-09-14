/**
 * 사업장 관리 모듈
 * - 사업장 CRUD 작업
 * - 사업장 검색 및 필터링
 * - 사업장 상태 관리
 */

// BusinessLocationsModule for admin_dashboard.html
window.BusinessLocationsModule = {
    async init() {
        console.log('🏢 Business Locations Module 초기화');
        this.loadSiteStats();
        this.loadSites();
        this.setupEventListeners();
        return this;
    },

    setupEventListeners() {
        // 전체 선택 체크박스
        const selectAll = document.getElementById('selectAllSites');
        if (selectAll) {
            selectAll.addEventListener('change', (e) => {
                const checkboxes = document.querySelectorAll('#sitesTableBody input[type="checkbox"]');
                checkboxes.forEach(cb => cb.checked = e.target.checked);
            });
        }
    },

    async loadSiteStats() {
        console.log('📊 loadSiteStats 함수 실행됨');
        try {
            // API에서 실제 통계 가져오기
            const response = await fetch(`${window.CONFIG.API_BASE_URL || 'http://127.0.0.1:8010'}/api/admin/business-locations`);
            const data = await response.json();
            console.log('📊 API 응답 데이터:', data);

            if (data.success) {
                const locations = data.locations || [];

                // 통계 계산
                const totalSites = locations.length;
                const activeSites = locations.filter(l => l.is_active).length;
                const regions = new Set(locations.map(l => l.region).filter(r => r && r !== '미지정')).size;

                console.log(`📊 통계: 전체=${totalSites}, 활성=${activeSites}, 지역=${regions}`);

                // UI 업데이트
                const totalElement = document.getElementById('totalSites');
                if (totalElement) {
                    totalElement.textContent = totalSites;
                    console.log('✅ totalSites 업데이트:', totalSites);
                } else {
                    console.error('❌ totalSites 엘리먼트를 찾을 수 없음');
                }

                const activeElement = document.getElementById('activeSites');
                if (activeElement) {
                    activeElement.textContent = activeSites;
                    console.log('✅ activeSites 업데이트:', activeSites);
                } else {
                    console.error('❌ activeSites 엘리먼트를 찾을 수 없음');
                }

                const regionElement = document.getElementById('regionCount');
                if (regionElement) {
                    regionElement.textContent = regions;
                    console.log('✅ regionCount 업데이트:', regions);
                } else {
                    console.error('❌ regionCount 엘리먼트를 찾을 수 없음');
                }
            }
        } catch (error) {
            console.error('❌ 통계 데이터 로드 오류:', error);
            // 오류 시 0으로 표시
            ['totalSites', 'activeSites', 'regionCount'].forEach(id => {
                const element = document.getElementById(id);
                if (element) element.textContent = '0';
            });
        }
    },

    async loadSites() {
        const tbody = document.getElementById('sitesTableBody');
        if (!tbody) return;

        try {
            // API에서 데이터 가져오기
            const response = await fetch(`${window.CONFIG.API_BASE_URL || 'http://127.0.0.1:8010'}/api/admin/business-locations`);
            const data = await response.json();

            if (data.success) {
                window.currentSiteData = data.locations || [];
            }
        } catch (error) {
            console.error('사업장 데이터 로드 오류:', error);
        }

        const siteData = window.currentSiteData;

        tbody.innerHTML = siteData.map(site => `
            <tr>
                <td>${site.site_code}</td>
                <td>
                    <div class="site-info">
                        <strong>${site.site_name}</strong>
                    </div>
                </td>
                <td>${site.site_type}</td>
                <td>${site.region || '-'}</td>
                <td>${site.manager_name || '-'}</td>
                <td>${site.manager_phone || '-'}</td>
                <td>
                    <span class="status-badge ${site.is_active ? 'active' : 'inactive'}">
                        ${site.is_active ? '활성' : '비활성'}
                    </span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-icon" onclick="editSite(${site.id})" title="수정">✏️</button>
                        <button class="btn-icon btn-danger" onclick="deleteSite(${site.id})" title="삭제">🗑️</button>
                    </div>
                </td>
            </tr>
        `).join('');
    }
};

// API에서 데이터를 가져오도록 수정
window.currentSiteData = [];

// 사업장 수정 함수 - 모달 띄우기
window.editSite = function(siteId) {
    const site = window.currentSiteData.find(s => s.id === siteId);
    if (!site) {
        alert('사업장을 찾을 수 없습니다.');
        return;
    }

    // 모달에 데이터 채우기
    document.getElementById('editSiteId').value = site.id;
    document.getElementById('editSiteCode').value = site.site_code;
    document.getElementById('editSiteName').value = site.site_name;
    document.getElementById('editSiteType').value = site.site_type;
    document.getElementById('editSiteRegion').value = site.region || '서울';
    document.getElementById('editSiteManager').value = site.manager_name || '';
    document.getElementById('editSitePhone').value = site.manager_phone || '';
    document.getElementById('editSiteStatus').value = site.is_active ? 'true' : 'false';

    // 모달 표시 및 스타일 강제 적용
    const modal = document.getElementById('siteEditModal');
    modal.style.display = 'block';

    // 모달 콘텐츠 스타일 강제 적용
    const modalContent = modal.querySelector('.modal-content');
    if (modalContent) {
        modalContent.style.maxHeight = '70vh';
        modalContent.style.margin = '3% auto';
        modalContent.style.width = '450px';
    }
};

// 사업장 삭제 함수
window.deleteSite = function(siteId) {
    if (confirm('정말로 이 사업장을 삭제하시겠습니까?')) {
        // API 호출
        fetch(`${window.CONFIG.API_BASE_URL}/api/admin/sites/${siteId}`, {
            method: 'DELETE'
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // alert 제거 - 바로 새로고침
                window.BusinessLocationsModule.loadSites();
            } else {
                alert('삭제 실패: ' + (data.error || '알 수 없는 오류'));
            }
        })
        .catch(err => {
            console.error('삭제 오류:', err);
            alert('삭제 중 오류가 발생했습니다.');
        });
    }
};

// 모달 닫기 함수
window.closeSiteModal = function() {
    document.getElementById('siteEditModal').style.display = 'none';
};

window.closeAddSiteModal = function() {
    document.getElementById('siteAddModal').style.display = 'none';
};

// 사업장 변경사항 저장
window.saveSiteChanges = function() {
    const siteId = document.getElementById('editSiteId').value;
    const data = {
        name: document.getElementById('editSiteName').value,
        type: document.getElementById('editSiteType').value,
        parent_id: document.getElementById('editSiteRegion').value,
        address: document.getElementById('editSiteRegion').value,
        manager_name: document.getElementById('editSiteManager').value || null,
        contact_info: document.getElementById('editSitePhone').value || null,
        is_active: document.getElementById('editSiteStatus').value === 'true'
    };

    // API 호출
    fetch(`${window.CONFIG.API_BASE_URL}/api/admin/sites/${siteId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            // alert 제거 - 바로 모달 닫기
            closeSiteModal();
            // 로컬 데이터도 업데이트
            const site = window.currentSiteData.find(s => s.id == siteId);
            if (site) {
                site.site_name = document.getElementById('editSiteName').value;
                site.site_type = document.getElementById('editSiteType').value;
                site.region = document.getElementById('editSiteRegion').value;
                site.manager_name = document.getElementById('editSiteManager').value || null;
                site.manager_phone = document.getElementById('editSitePhone').value || null;
                site.is_active = document.getElementById('editSiteStatus').value === 'true';
            }
            window.BusinessLocationsModule.loadSites();
        } else {
            alert('수정 실패: ' + (result.error || '알 수 없는 오류'));
        }
    })
    .catch(err => {
        console.error('저장 오류:', err);
        alert('저장 중 오류가 발생했습니다.');
    });
};

// HTML에서 호출하는 전역 함수들
window.filterSitesByType = function() {
    const filter = document.getElementById('siteTypeFilter')?.value;
    const tbody = document.getElementById('sitesTableBody');
    if (!tbody) return;

    // 하드코딩 대신 전역 변수 사용
    const siteData = window.currentSiteData;

    let filteredData = siteData;
    if (filter) {
        filteredData = siteData.filter(s => s.site_name === filter);
    }

    if (filteredData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">검색 결과가 없습니다.</td></tr>';
        return;
    }

    tbody.innerHTML = filteredData.map(site => `
        <tr>
            <td>${site.site_code}</td>
            <td>${site.site_name}</td>
            <td>${site.site_type}</td>
            <td>${site.region || '-'}</td>
            <td>${site.manager_name || '-'}</td>
            <td>${site.manager_phone || '-'}</td>
            <td>
                <span class="status-badge ${site.is_active ? 'active' : 'inactive'}">
                    ${site.is_active ? '활성' : '비활성'}
                </span>
            </td>
            <td>
                <div class="action-buttons">
                    <button class="btn-icon" onclick="editSite(${site.id})" title="수정">✏️</button>
                    <button class="btn-icon btn-danger" onclick="deleteSite(${site.id})" title="삭제">🗑️</button>
                </div>
            </td>
        </tr>
    `).join('');
};

window.searchSites = function() {
    const searchTerm = document.getElementById('siteSearchInput')?.value.toLowerCase();
    const tbody = document.getElementById('sitesTableBody');
    if (!tbody) return;

    // 하드코딩 대신 전역 변수 사용
    const siteData = window.currentSiteData;

    if (!searchTerm) {
        BusinessLocationsModule.loadSites();
        return;
    }

    const filteredData = siteData.filter(site =>
        site.site_name.toLowerCase().includes(searchTerm) ||
        site.site_code.toLowerCase().includes(searchTerm) ||
        site.site_type.toLowerCase().includes(searchTerm)
    );

    if (filteredData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">검색 결과가 없습니다.</td></tr>';
        return;
    }

    tbody.innerHTML = filteredData.map(site => `
        <tr>
            <td>${site.site_code}</td>
            <td>${site.site_name}</td>
            <td>${site.site_type}</td>
            <td>${site.region || '-'}</td>
            <td>${site.manager_name || '-'}</td>
            <td>${site.manager_phone || '-'}</td>
            <td>
                <span class="status-badge ${site.is_active ? 'active' : 'inactive'}">
                    ${site.is_active ? '활성' : '비활성'}
                </span>
            </td>
            <td>
                <div class="action-buttons">
                    <button class="btn-icon" onclick="editSite(${site.id})" title="수정">✏️</button>
                    <button class="btn-icon btn-danger" onclick="deleteSite(${site.id})" title="삭제">🗑️</button>
                </div>
            </td>
        </tr>
    `).join('');
};

// 새 사업장 추가 모달 표시
window.showAddSiteModal = function() {
    // site_code는 서버에서 자동 생성하므로 프론트엔드에서 생성하지 않음
    // 폼 초기화 - 모든 필드를 빈 값으로
    document.getElementById('newSiteCode').value = '자동 생성됩니다';
    document.getElementById('newSiteName').value = '';
    document.getElementById('newSiteType').value = '';  // 빈 값으로 변경
    document.getElementById('newSiteRegion').value = '';  // 빈 값으로 변경
    document.getElementById('newSiteManager').value = '';
    document.getElementById('newSitePhone').value = '';

    // 모달 표시 및 스타일 강제 적용
    const modal = document.getElementById('siteAddModal');
    modal.style.display = 'block';

    // 모달 콘텐츠 스타일 강제 적용
    const modalContent = modal.querySelector('.modal-content');
    if (modalContent) {
        modalContent.style.maxHeight = '70vh';
        modalContent.style.margin = '3% auto';
        modalContent.style.width = '450px';
    }
};

// 새 사업장 추가
window.addNewSite = function() {
    // site_code는 서버에서 자동 생성하므로 전송하지 않음
    const data = {
        // site_code 제거 - 서버에서 자동 생성
        name: document.getElementById('newSiteName').value,
        type: document.getElementById('newSiteType').value,
        parent_id: document.getElementById('newSiteRegion').value,
        address: document.getElementById('newSiteRegion').value,
        contact_info: document.getElementById('newSitePhone').value || null,
        manager_name: document.getElementById('newSiteManager').value || null,  // 관리자 필드 추가
        is_active: true
    };

    // 필수 필드 검증 (사업장명만 검증, 코드는 자동생성)
    if (!data.name) {
        alert('사업장명은 필수입니다.');
        return;
    }

    // API 호출
    fetch(`${window.CONFIG.API_BASE_URL}/api/admin/sites`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            // alert 제거 - 바로 모달 닫기
            closeAddSiteModal();
            window.BusinessLocationsModule.loadSites();
        } else {
            alert('추가 실패: ' + (result.error || '알 수 없는 오류'));
        }
    })
    .catch(err => {
        console.error('추가 오류:', err);
        alert('추가 중 오류가 발생했습니다.');
    });
};

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
        console.log('[DEBUG] render() called');
        const container = document.getElementById('sites-module');
        console.log('[DEBUG] sites-module container:', container);
        if (!container) {
            console.error('[ERROR] sites-module container not found!');
            return;
        }

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
                                <th>사업장타입</th>
                                <th>지역</th>
                                <th>연락처</th>
                                <th>상태</th>
                                <th>등록일</th>
                                <th>작업</th>
                            </tr>
                        </thead>
                        <tbody id="sites-table-body">
                            <tr>
                                <td colspan="8" class="loading-cell">사업장 목록을 불러오는 중...</td>
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
            
            console.log('[DEBUG] response.success:', response.success);
            console.log('[DEBUG] response.sites length:', response.sites ? response.sites.length : 'undefined');
            
            if (response.success) {
                console.log('[DEBUG] Calling renderSites with sites:', response.sites);
                console.log('[DEBUG] First site data:', response.sites[0]);
                window.lastSitesData = response.sites; // 디버깅용
                this.renderSites(response.sites || []);
                this.updatePagination(response.total, response.page, response.limit);
                await this.loadSiteStats();
            } else {
                console.error('[ERROR] API response success is false');
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
        console.log('[DEBUG] renderSites called with:', sites);
        const tbody = document.getElementById('sites-table-body');
        console.log('[DEBUG] tbody element:', tbody);
        if (!tbody) {
            console.error('[ERROR] sites-table-body element not found!');
            return;
        }

        if (sites.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="loading-cell">등록된 사업장이 없습니다.</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = sites.map(site => `
            <tr>
                <td>${site.id}</td>
                <td><strong>${site.site_name || '-'}</strong></td>
                <td>${site.site_type || '-'}</td>
                <td>${site.region || '-'}</td>
                <td>${site.phone || site.manager_phone || '-'}</td>
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