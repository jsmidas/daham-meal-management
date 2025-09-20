        // 페이지 네비게이션 관리
        function showPage(pageName) {
            // 모든 페이지 숨기기
            document.querySelectorAll('.page-content').forEach(page => {
                page.classList.add('hidden');
            });
            
            // 선택된 페이지 보이기
            const targetPage = document.getElementById(`${pageName}-page`);
            if (targetPage) {
                targetPage.classList.remove('hidden');
            }
            
            // 네비게이션 활성 상태 변경
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            
            const activeItem = document.querySelector(`[data-page="${pageName}"]`);
            if (activeItem) {
                activeItem.classList.add('active');
            }
            
            // 페이지 제목 변경
            const titles = {
                'dashboard': '관리자 대시보드',
                'users': '사용자 관리',
                'suppliers': '업체 관리',
                'business-locations': '사업장 관리',
                'supplier-mapping': '협력업체 매핑',
                'meal-pricing': '식단가 관리',
                'ingredients': '식자재 관리',
                'pricing': '단가 관리',
                'settings': '시스템 설정',
                'logs': '로그 관리'
            };
            
            document.getElementById('page-title').textContent = titles[pageName] || '관리자 시스템';
        }


        // 네비게이션 클릭 이벤트
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                // target="_blank"가 있는 링크는 새 탭에서 열리도록 허용
                if (e.currentTarget.getAttribute('target') === '_blank') {
                    return; // 기본 동작 허용
                }
                
                // href가 있는 외부 링크(협력업체 관리, 사업장 관리, 급식관리로 이동)는 기본 동작 허용
                const href = e.currentTarget.getAttribute('href');
                if (href && (href.startsWith('/admin/suppliers') || href.startsWith('/admin/business-locations') || href === '/')) {
                    return; // 기본 동작 허용
                }
                
                e.preventDefault();
                const pageName = e.currentTarget.getAttribute('data-page');
                showPage(pageName);
                
                // 페이지별 초기화
                if (pageName === 'users') {
                    loadUsers();
                    loadManagedSites();
                } else if (pageName === 'suppliers') {
                    loadSuppliers();
                } else if (pageName === 'business-locations') {
                    loadSitesTree();
                } else if (pageName === 'meal-pricing') {
                    // 식단가 관리 페이지 초기화
                    if (typeof loadBusinessLocationsForMealPricing === 'function') {
                        loadBusinessLocationsForMealPricing();
                    } else {
                        // 함수가 없으면 직접 실행
                        loadBusinessLocationsForMealPricingDirect();
                    }
                } else if (pageName === 'ingredients') {
                    // 식자재 관리 페이지 초기화
                    // 식자재 목록은 별도 페이지(/ingredients)에서 관리
                    loadUploadHistory();
                    if (window.initializeIngredientsPage) {
                        window.initializeIngredientsPage();
                    }
                }
            });
        });

        // 이미지 모달 함수들
        function openImageModal(imageSrc, title) {
            const modal = document.getElementById('image-modal');
            const modalImg = document.getElementById('image-modal-img');
            const modalTitle = document.getElementById('image-modal-title');
            
            modalImg.src = imageSrc;
            modalImg.alt = title;
            modalTitle.textContent = title;
            modal.classList.remove('hidden');
            
            // ESC 키로 모달 닫기
            document.addEventListener('keydown', handleImageModalEsc);
        }
        
        function closeImageModal() {
            const modal = document.getElementById('image-modal');
            modal.classList.add('hidden');
            
            // ESC 키 이벤트 제거
            document.removeEventListener('keydown', handleImageModalEsc);
        }
        
        function handleImageModalEsc(event) {
            if (event.key === 'Escape') {
                closeImageModal();
            }
        }
        
        // 모달 배경 클릭으로 닫기
        document.addEventListener('click', function(event) {
            const modal = document.getElementById('image-modal');
            if (event.target === modal) {
                closeImageModal();
            }
        });

        // 로그아웃 함수
        async function logout() {
            if (confirm('로그아웃 하시겠습니까?')) {
                try {
                    const response = await fetch('/api/auth/logout', {
                        method: 'POST',
                        credentials: 'include'  // 쿠키 포함
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        window.location.href = result.redirect || '/login';
                    } else {
                        console.error('로그아웃 실패:', result.message);
                        window.location.href = '/login';  // 실패해도 로그인 페이지로 이동
                    }
                } catch (error) {
                    console.error('로그아웃 중 오류:', error);
                    window.location.href = '/login';  // 오류 시에도 로그인 페이지로 이동
                }
            }
        }

        // 대시보드 데이터 로드
        async function loadDashboardData() {
            try {
                // 통계 데이터 가져오기
                const response = await fetch('/api/admin/dashboard-stats');
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('total-users').textContent = data.totalUsers || 0;
                    document.getElementById('total-sites').textContent = data.totalSites || 0;
                    document.getElementById('today-menus').textContent = data.todayMenus || 0;
                    document.getElementById('price-updates').textContent = data.priceUpdates || 0;
                }
            } catch (error) {
                console.error('대시보드 데이터 로드 실패:', error);
            }
        }

        // 최근 활동 로그 로드
        async function loadRecentActivity() {
            try {
                const response = await fetch('/api/admin/recent-activity');
                const result = await response.json();
                const activities = result.activities || result.data || [];
                
                const activityList = document.getElementById('activity-list');
                if (activities.length === 0) {
                    activityList.innerHTML = '<div class="log-item">최근 활동이 없습니다.</div>';
                    return;
                }
                
                activityList.innerHTML = activities.map(activity => `
                    <div class="log-item">
                        <div class="log-time">${activity.time}</div>
                        <div class="log-message">${activity.message}</div>
                        <div class="log-user">${activity.user}</div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('활동 로그 로드 실패:', error);
                document.getElementById('activity-list').innerHTML = 
                    '<div class="log-item">활동 로그를 불러올 수 없습니다.</div>';
            }
        }

        // 전역 변수들
        let pageInitialized = false;
        let allowModalDisplay = false;

        // 페이지 로드시 초기화
        document.addEventListener('DOMContentLoaded', () => {
            console.log('페이지 초기화 시작');
            
            // 강제로 모든 모달 숨김 처리
            setTimeout(() => {
                const userModal = document.getElementById('user-modal');
                const siteModal = document.getElementById('site-modal');
                
                if (userModal) {
                    userModal.style.display = 'none';
                    userModal.classList.add('hidden');
                    console.log('사용자 모달 강제 숨김');
                }
                if (siteModal) {
                    siteModal.style.display = 'none';
                    siteModal.classList.add('hidden');
                    console.log('사업장 모달 강제 숨김');
                }
                
                // 변수 초기화
                if (typeof currentEditUserId !== 'undefined') {
                    currentEditUserId = null;
                }
                if (typeof currentEditSiteId !== 'undefined') {
                    currentEditSiteId = null;
                }
                
                console.log('모든 모달 숨김 처리 완료');
                
                // 초기화 완료 후 1초 뒤에 모달 표시 허용
                setTimeout(() => {
                    window.pageInitialized = true;
                    window.allowModalDisplay = true;
                    console.log('모달 표시 허용됨');
                }, 1000);
            }, 100);
            
            // 기본으로 대시보드 페이지 표시
            console.log('대시보드 페이지 표시');
            showPage('dashboard');
            loadDashboardData();
            loadRecentActivity();
        });

        // 사용자 관리 관련 변수
        window.currentPage = window.currentPage || 1;
        window.totalPages = window.totalPages || 1;
        let currentEditUserId = null;

        // 사용자 관리 함수들

        // 사용자 목록 로드 (포트 8002 서버 사용)
        async function loadUsers() {
            try {
                console.log('[LoadUsers] 사용자 목록 로드 시작...');
                const response = await fetch('http://127.0.0.1:8003/api/admin/users');
                const data = await response.json();
                
                if (data.success) {
                    displayUsers(data.users);
                    updatePagination(data.currentPage, data.totalPages);
                }
            } catch (error) {
                console.error('사용자 목록 로드 실패:', error);
                document.getElementById('users-table-body').innerHTML = 
                    '<tr><td colspan="8">사용자 목록을 불러올 수 없습니다.</td></tr>';
            }
        }

        // 사용자 목록 표시
        function displayUsers(users) {
            const tbody = document.getElementById('users-table-body');
            
            if (!users || users.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8">등록된 사용자가 없습니다.</td></tr>';
                return;
            }
            
            tbody.innerHTML = users.map((user, index) => `
                <tr>
                    <td>${index + 1}</td>
                    <td><strong>${user.name || user.username}</strong><br><small>${user.username}</small></td>
                    <td>${user.role}</td>
                    <td>${user.department || '-'}</td>
                    <td>-</td>
                    <td>-</td>
                    <td>${user.created_at || '-'}</td>
                    <td>
                        <button class="btn-small btn-edit">수정</button>
                        <button class="btn-small btn-delete">삭제</button>
                    </td>
                </tr>
            `).join('');
        }

        // 역할 표시명 변환
        function getRoleDisplay(role) {
            const roleMap = {
                'nutritionist': '영양사',
                'admin': '관리자', 
                'super_admin': '최고관리자'
            };
            return roleMap[role] || role;
        }

        // 페이지네이션 업데이트
        function updatePagination(current, total) {
            window.currentPage = current;
            window.totalPages = total;
            document.getElementById('page-info').textContent = `${current} / ${total}`;
        }

        // 페이지 변경
        function changePage(direction) {
            const newPage = window.currentPage + direction;
            if (newPage >= 1 && newPage <= window.totalPages) {
                window.currentPage = newPage;
                loadUsers();
            }
        }

        // 사용자 검색
        function searchUsers() {
            const keyword = document.getElementById('user-search').value;
            // 실제 구현에서는 검색 API 호출
            console.log('검색 키워드:', keyword);
            loadUsers(); // 임시로 전체 목록 다시 로드
        }

        // 담당 사업장 목록 로드
        async function loadManagedSites() {
            try {
                const response = await fetch('/api/admin/sites');
                const result = await response.json();
                const sites = result.sites || result.data || [];
                
                const select = document.getElementById('user-managed-site');
                select.innerHTML = '<option value="">선택하세요</option>';
                
                sites.forEach(site => {
                    select.innerHTML += `<option value="${site.name}">${site.name}</option>`;
                });
            } catch (error) {
                console.error('사업장 목록 로드 실패:', error);
            }
        }

        // 새 사용자 추가 모달 표시 - 모듈에서 처리
        /* function showAddUserModal() {
            currentEditUserId = null;
            document.getElementById('modal-title').textContent = '새 사용자 추가';
            document.getElementById('user-form').reset();
            document.getElementById('user-modal').classList.remove('hidden');
        } */

        // 사용자 수정 모달 표시
        async function editUser(userId) {
            try {
                const response = await fetch(`/api/admin/users/${userId}`);
                const result = await response.json();
                const user = result.user || result;
                
                if (user) {
                    currentEditUserId = userId;
                    document.getElementById('modal-title').textContent = '사용자 정보 수정';
                    
                    // 폼에 기존 데이터 채우기
                    document.getElementById('user-username').value = user.username;
                    document.getElementById('user-password').value = ''; // 비밀번호는 비움
                    document.getElementById('user-role').value = user.role;
                    document.getElementById('user-contact').value = user.contact_info || '';
                    document.getElementById('user-department').value = user.department || '';
                    document.getElementById('user-position').value = user.position || '';
                    document.getElementById('user-managed-site').value = user.managed_site || '';
                    document.getElementById('user-operator').checked = user.operator || false;
                    document.getElementById('user-semi-operator').checked = user.semi_operator || false;
                    
                    document.getElementById('user-modal').classList.remove('hidden');
                }
            } catch (error) {
                console.error('사용자 정보 로드 실패:', error);
                alert('사용자 정보를 불러올 수 없습니다.');
            }
        }

        // 사용자 모달 닫기
        function closeUserModal() {
            document.getElementById('user-modal').classList.add('hidden');
            currentEditUserId = null;
        }

        // 사용자 저장
        async function saveUser() {
            const userData = {
                username: document.getElementById('user-username').value,
                password: document.getElementById('user-password').value,
                role: document.getElementById('user-role').value,
                contact_info: document.getElementById('user-contact').value,
                department: document.getElementById('user-department').value,
                position: document.getElementById('user-position').value,
                managed_site: document.getElementById('user-managed-site').value,
                operator: document.getElementById('user-operator').checked,
                semi_operator: document.getElementById('user-semi-operator').checked
            };

            try {
                const url = currentEditUserId ? 
                    `/api/admin/users/${currentEditUserId}` : 
                    '/api/admin/users';
                
                const method = currentEditUserId ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(userData)
                });

                const result = await response.json();
                
                if (result.success) {
                    alert(currentEditUserId ? '사용자가 수정되었습니다.' : '새 사용자가 추가되었습니다.');
                    closeUserModal();
                    loadUsers();
                } else {
                    alert(result.message || '저장 중 오류가 발생했습니다.');
                }
            } catch (error) {
                console.error('사용자 저장 실패:', error);
                alert('저장 중 오류가 발생했습니다.');
            }
        }

        // 비밀번호 초기화
        async function resetPassword(userId) {
            if (!confirm('이 사용자의 비밀번호를 초기화하시겠습니까?')) {
                return;
            }

            try {
                const response = await fetch(`/api/admin/users/${userId}/reset-password`, {
                    method: 'POST'
                });

                const result = await response.json();
                
                if (result.success) {
                    alert(`비밀번호가 초기화되었습니다. 새 비밀번호: ${result.newPassword}`);
                } else {
                    alert('비밀번호 초기화에 실패했습니다.');
                }
            } catch (error) {
                console.error('비밀번호 초기화 실패:', error);
                alert('비밀번호 초기화 중 오류가 발생했습니다.');
            }
        }

        // 사용자 삭제
        async function deleteUser(userId) {
            if (!confirm('이 사용자를 삭제하시겠습니까? 이 작업은 취소할 수 없습니다.')) {
                return;
            }

            try {
                const response = await fetch(`/api/admin/users/${userId}`, {
                    method: 'DELETE'
                });

                const result = await response.json();
                
                if (result.success) {
                    alert('사용자가 삭제되었습니다.');
                    loadUsers();
                } else {
                    alert('사용자 삭제에 실패했습니다.');
                }
            } catch (error) {
                console.error('사용자 삭제 실패:', error);
                alert('사용자 삭제 중 오류가 발생했습니다.');
            }
        }

        // 사업장 관리 관련 변수
        let sitesData = [];
        let selectedSiteId = null;
        let currentEditSiteId = null;

        // 사업장 트리 로드
        async function loadSitesTree() {
            try {
                const response = await fetch('/api/admin/sites/tree');
                const data = await response.json();
                
                if (data.success) {
                    sitesData = data.sites || [];
                    renderSitesTree();
                } else {
                    console.error('API 응답 오류:', data.message);
                    const container = document.getElementById('sites-tree');
                    if (container) {
                        container.innerHTML = '<div class="text-center">사업장 정보를 불러올 수 없습니다.</div>';
                    }
                }
            } catch (error) {
                console.error('사업장 트리 로드 실패:', error);
                const container = document.getElementById('sites-tree');
                if (container) {
                    container.innerHTML = '<div class="text-center">사업장 정보를 불러올 수 없습니다.</div>';
                }
            }
        }

        // 사업장 트리 렌더링
        function renderSitesTree() {
            const pageContainer = document.querySelector('#business-locations-page .sites-container');
            if (pageContainer) {
                // 페이지 내 sites-container에 sites-tree 생성
                pageContainer.innerHTML = '<div class="sites-tree" id="sites-tree"></div>';
            }
            
            const container = document.getElementById('sites-tree');
            if (!container) {
                console.log('sites-tree 컨테이너를 찾을 수 없습니다. 현재 페이지에서는 사업장 트리가 필요하지 않습니다.');
                return;
            }
            
            container.innerHTML = '';
            
            if (!Array.isArray(sitesData) || sitesData.length === 0) {
                container.innerHTML = '<div class="text-center">등록된 사업장이 없습니다.</div>';
                return;
            }
            
            // 모든 사업장 렌더링 (헤드 구분 없이)
            sitesData.forEach(site => {
                container.appendChild(createTreeNode(site));
            });
        }

        // 트리 노드 생성
        function createTreeNode(site) {
            const nodeDiv = document.createElement('div');
            nodeDiv.className = 'tree-node';
            nodeDiv.dataset.siteId = site.id;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = `tree-node-content ${site.site_type}-site`;
            contentDiv.onclick = () => selectSite(site.id);
            
            // 드래그 앤 드롭 이벤트 추가
            setupDragAndDrop(contentDiv, site);
            
            // 확장/축소 버튼
            const expandBtn = document.createElement('button');
            expandBtn.className = 'tree-expand-btn';
            const hasChildren = site.children && site.children.length > 0;
            
            if (hasChildren) {
                expandBtn.className += ' expanded';
                expandBtn.onclick = (e) => {
                    e.stopPropagation();
                    toggleNode(site.id);
                };
            } else {
                expandBtn.className += ' no-children';
            }
            
            // 아이콘
            const iconSpan = document.createElement('span');
            iconSpan.className = 'tree-node-icon';
            iconSpan.textContent = getSiteIcon(site.site_type || '일반');
            
            // 라벨
            const labelSpan = document.createElement('span');
            labelSpan.className = 'tree-node-label';
            labelSpan.textContent = site.name;
            
            // 상태
            const statusSpan = document.createElement('span');
            statusSpan.className = `tree-node-status ${site.is_active ? 'active' : 'inactive'}`;
            statusSpan.textContent = site.is_active ? '활성' : '비활성';
            
            // 액션 버튼들
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'tree-node-actions';
            
            if (site.site_type === 'head') {
                const addDetailBtn = document.createElement('button');
                addDetailBtn.className = 'tree-action-btn add';
                addDetailBtn.textContent = '+ 세부';
                addDetailBtn.onclick = (e) => {
                    e.stopPropagation();
                    showAddSiteModal('detail', site.id);
                };
                actionsDiv.appendChild(addDetailBtn);
            } else if (site.site_type === 'detail') {
                const addPeriodBtn = document.createElement('button');
                addPeriodBtn.className = 'tree-action-btn add';
                addPeriodBtn.textContent = '+ 기간';
                addPeriodBtn.onclick = (e) => {
                    e.stopPropagation();
                    showAddSiteModal('period', site.id);
                };
                actionsDiv.appendChild(addPeriodBtn);
            }
            
            const editBtn = document.createElement('button');
            editBtn.className = 'tree-action-btn edit';
            editBtn.textContent = '수정';
            editBtn.onclick = (e) => {
                e.stopPropagation();
                editSite(site.id);
            };
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'tree-action-btn delete';
            deleteBtn.textContent = '삭제';
            deleteBtn.onclick = (e) => {
                e.stopPropagation();
                deleteSite(site.id);
            };
            
            actionsDiv.appendChild(editBtn);
            actionsDiv.appendChild(deleteBtn);
            
            // 컨텐츠 조립
            contentDiv.appendChild(expandBtn);
            contentDiv.appendChild(iconSpan);
            contentDiv.appendChild(labelSpan);
            contentDiv.appendChild(statusSpan);
            contentDiv.appendChild(actionsDiv);
            
            nodeDiv.appendChild(contentDiv);
            
            // 자식 노드들
            if (hasChildren) {
                const childrenDiv = document.createElement('div');
                childrenDiv.className = 'tree-children';
                site.children.forEach(child => {
                    childrenDiv.appendChild(createTreeNode(child));
                });
                nodeDiv.appendChild(childrenDiv);
            }
            
            return nodeDiv;
        }

        // 사업장 아이콘 가져오기
        function getSiteIcon(siteType) {
            switch (siteType) {
                case 'head': return '🏢';
                case 'detail': return '🏫';
                case 'period': return '📅';
                default: return '📍';
            }
        }

        // 노드 확장/축소
        function toggleNode(siteId) {
            const node = document.querySelector(`[data-site-id="${siteId}"]`);
            if (!node) return;
            
            const expandBtn = node.querySelector('.tree-expand-btn');
            const childrenDiv = node.querySelector('.tree-children');
            
            if (!childrenDiv) return;
            
            if (expandBtn.classList.contains('expanded')) {
                expandBtn.className = expandBtn.className.replace('expanded', 'collapsed');
                childrenDiv.classList.add('hidden');
            } else {
                expandBtn.className = expandBtn.className.replace('collapsed', 'expanded');
                childrenDiv.classList.remove('hidden');
            }
        }

        // 모든 노드 확장
        function expandAllSites() {
            document.querySelectorAll('.tree-expand-btn.collapsed').forEach(btn => {
                btn.className = btn.className.replace('collapsed', 'expanded');
            });
            document.querySelectorAll('.tree-children.hidden').forEach(children => {
                children.classList.remove('hidden');
            });
        }

        // 모든 노드 축소
        function collapseAllSites() {
            document.querySelectorAll('.tree-expand-btn.expanded').forEach(btn => {
                btn.className = btn.className.replace('expanded', 'collapsed');
            });
            document.querySelectorAll('.tree-children').forEach(children => {
                children.classList.add('hidden');
            });
        }

        // 사업장 선택
        function selectSite(siteId) {
            // 이전 선택 해제
            document.querySelectorAll('.tree-node-content.selected').forEach(node => {
                node.classList.remove('selected');
            });
            
            // 새 선택
            const node = document.querySelector(`[data-site-id="${siteId}"] .tree-node-content`);
            if (node) {
                node.classList.add('selected');
                selectedSiteId = siteId;
                showSiteDetails(siteId);
            }
        }

        // 사업장 상세정보 표시
        async function showSiteDetails(siteId) {
            try {
                const response = await fetch(`/api/admin/sites/${siteId}`);
                const site = await response.json();
                
                const panel = document.getElementById('site-details-panel');
                const content = document.getElementById('site-details-content');
                
                content.innerHTML = `
                    <div class="site-info-group">
                        <div class="site-info-label">사업장명</div>
                        <div class="site-info-value">${site.name}</div>
                    </div>
                    <div class="site-info-group">
                        <div class="site-info-label">구분</div>
                        <div class="site-info-value">${getSiteTypeDisplay(site.site_type)}</div>
                    </div>
                    <div class="site-info-group">
                        <div class="site-info-label">담당자</div>
                        <div class="site-info-value">${site.contact_person || '-'}</div>
                    </div>
                    <div class="site-info-group">
                        <div class="site-info-label">연락처</div>
                        <div class="site-info-value">${site.contact_phone || '-'}</div>
                    </div>
                    <div class="site-info-group">
                        <div class="site-info-label">주소</div>
                        <div class="site-info-value">${site.address || '-'}</div>
                    </div>
                    <div class="site-info-group">
                        <div class="site-info-label">1인당 제공량</div>
                        <div class="site-info-value">${site.portion_size || 0}g</div>
                    </div>
                    <div class="site-stats">
                        <div class="stat-box">
                            <div class="stat-number">${site.menu_count || 0}</div>
                            <div class="stat-label">등록된 식단</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">${site.children_count || 0}</div>
                            <div class="stat-label">하위 사업장</div>
                        </div>
                    </div>
                `;
                
                panel.classList.remove('hidden');
            } catch (error) {
                console.error('사업장 상세정보 로드 실패:', error);
            }
        }

        // 사업장 구분 표시명
        function getSiteTypeDisplay(siteType) {
            switch (siteType) {
                case '도시락': return '도시락';
                case '운반': return '운반';
                case '학교': return '학교';
                case '요양원': return '요양원';
                case '위탁': return '위탁';
                case '일반음식점': return '일반음식점';
                case '기타': return '기타';
                // 이전 버전과의 호환성
                case 'head': return '헤드 사업장';
                case 'detail': return '세부 사업장';
                case 'period': return '기간별 사업장';
                default: return siteType || '미분류';
            }
        }

        // ==============================================================================
        // 드래그 앤 드롭 기능
        // ==============================================================================
        
        let draggedElement = null;
        let draggedSite = null;

        // 드래그 앤 드롭 이벤트 설정
        function setupDragAndDrop(element, site) {
            element.draggable = true;
            
            element.addEventListener('dragstart', (e) => {
                draggedElement = element;
                draggedSite = site;
                element.classList.add('dragging');
                
                // 드래그 데이터 설정
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/plain', site.id);
                
                console.log('드래그 시작:', site.name);
            });
            
            element.addEventListener('dragend', (e) => {
                element.classList.remove('dragging');
                // 모든 드롭 인디케이터 제거
                clearDropIndicators();
                draggedElement = null;
                draggedSite = null;
                
                console.log('드래그 종료');
            });
            
            element.addEventListener('dragover', (e) => {
                if (!draggedSite || draggedSite.id === site.id) return;
                
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                
                // 유효한 드롭 대상인지 확인
                if (canDropOn(draggedSite, site)) {
                    element.classList.add('drag-over');
                } else {
                    element.classList.add('drop-invalid');
                }
            });
            
            element.addEventListener('dragleave', (e) => {
                element.classList.remove('drag-over', 'drop-invalid');
            });
            
            element.addEventListener('drop', (e) => {
                e.preventDefault();
                element.classList.remove('drag-over', 'drop-invalid');
                
                if (!draggedSite || draggedSite.id === site.id) return;
                
                // 유효한 드롭인지 확인
                if (canDropOn(draggedSite, site)) {
                    handleDrop(draggedSite, site);
                } else {
                    console.log('유효하지 않은 드롭:', draggedSite.name, '->', site.name);
                }
            });
        }

        // 드롭 가능 여부 확인
        function canDropOn(draggedSite, targetSite) {
            // 자기 자신에게는 드롭 불가
            if (draggedSite.id === targetSite.id) return false;
            
            // 계층 구조 규칙 확인
            // head -> detail 또는 detail -> period만 가능
            if (draggedSite.site_type === 'head') {
                // head는 이동 불가
                return false;
            } else if (draggedSite.site_type === 'detail') {
                // detail은 head에만 드롭 가능
                return targetSite.site_type === 'head';
            } else if (draggedSite.site_type === 'period') {
                // period는 detail에만 드롭 가능
                return targetSite.site_type === 'detail';
            }
            
            return false;
        }

        // 드롭 처리
        async function handleDrop(draggedSite, targetSite) {
            console.log(`드롭 처리: ${draggedSite.name} -> ${targetSite.name}`);
            
            // 확인 대화상자
            const message = `"${draggedSite.name}"을(를) "${targetSite.name}" 하위로 이동하시겠습니까?`;
            if (!confirm(message)) {
                return;
            }
            
            try {
                // 서버에 이동 요청
                const response = await fetch(`/api/admin/sites/${draggedSite.id}/move`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        new_parent_id: targetSite.id
                    }),
                });
                
                const result = await response.json();
                
                if (result.success) {
                    console.log('이동 성공:', result.message);
                    // 트리 새로고침
                    loadSitesTree();
                } else {
                    console.error('이동 실패:', result.message);
                    alert(`이동 실패: ${result.message}`);
                }
            } catch (error) {
                console.error('이동 요청 오류:', error);
                alert('이동 중 오류가 발생했습니다.');
            }
        }

        // 드롭 인디케이터 정리
        function clearDropIndicators() {
            document.querySelectorAll('.tree-node-content').forEach(el => {
                el.classList.remove('drag-over', 'drop-invalid');
            });
        }

        // 상세정보 패널 닫기
        function closeSiteDetails() {
            document.getElementById('site-details-panel').classList.add('hidden');
            selectedSiteId = null;
            
            // 선택 해제
            document.querySelectorAll('.tree-node-content.selected').forEach(node => {
                node.classList.remove('selected');
            });
        }

        // 사업장 추가 모달 표시
        function showAddSiteModal(siteType, parentId = null) {
            console.log('showAddSiteModal 호출됨:', siteType, parentId, 'allowModalDisplay:', allowModalDisplay);
            
            // 페이지 초기화가 완료되지 않았으면 실행하지 않음
            if (!allowModalDisplay) {
                console.log('페이지 초기화 중이므로 모달 표시 취소');
                return;
            }
            
            currentEditSiteId = null;
            
            const modal = document.getElementById('site-modal');
            if (!modal) {
                console.error('사업장 모달을 찾을 수 없음');
                return;
            }
            
            document.getElementById('site-modal-title').textContent = `새 ${getSiteTypeDisplay(siteType)} 추가`;
            document.getElementById('site-form').reset();
            document.getElementById('site-parent-id').value = parentId || '';
            document.getElementById('site-type').value = siteType;
            document.getElementById('site-is-active').checked = true;
            
            modal.style.display = 'flex';
            modal.classList.remove('hidden');
            console.log('사업장 모달 표시됨');
        }

        // 사업장 수정
        async function editSite(siteId) {
            try {
                const response = await fetch(`/api/admin/sites/${siteId}`);
                const site = await response.json();
                
                currentEditSiteId = siteId;
                document.getElementById('site-modal-title').textContent = '사업장 정보 수정';
                
                // 폼에 기존 데이터 채우기
                document.getElementById('site-name').value = site.name;
                document.getElementById('site-contact-person').value = site.contact_person || '';
                document.getElementById('site-contact-phone').value = site.contact_phone || '';
                document.getElementById('site-address').value = site.address || '';
                document.getElementById('site-portion-size').value = site.portion_size || '';
                document.getElementById('site-description').value = site.description || '';
                document.getElementById('site-is-active').checked = site.is_active;
                
                document.getElementById('site-modal').classList.remove('hidden');
            } catch (error) {
                console.error('사업장 정보 로드 실패:', error);
                alert('사업장 정보를 불러올 수 없습니다.');
            }
        }

        // 사업장 삭제
        async function deleteSite(siteId) {
            if (!confirm('이 사업장을 삭제하시겠습니까? 하위 사업장도 함께 삭제됩니다.')) {
                return;
            }

            try {
                const response = await fetch(`/api/admin/sites/${siteId}`, {
                    method: 'DELETE'
                });

                const result = await response.json();
                
                if (result.success) {
                    alert('사업장이 삭제되었습니다.');
                    loadSitesTree();
                    closeSiteDetails();
                } else {
                    alert('사업장 삭제에 실패했습니다.');
                }
            } catch (error) {
                console.error('사업장 삭제 실패:', error);
                alert('사업장 삭제 중 오류가 발생했습니다.');
            }
        }

        // 사업장 모달 닫기
        function closeSiteModal() {
            console.log('closeSiteModal 호출됨');
            const modal = document.getElementById('site-modal');
            if (modal) {
                modal.style.display = 'none';
                modal.classList.add('hidden');
                console.log('사업장 모달 완전히 숨김');
            }
            currentEditSiteId = null;
        }

        // 사업장 저장
        async function saveSite() {
            const siteData = {
                name: document.getElementById('site-name').value,
                contact_person: document.getElementById('site-contact-person').value,
                contact_phone: document.getElementById('site-contact-phone').value,
                address: document.getElementById('site-address').value,
                portion_size: parseInt(document.getElementById('site-portion-size').value) || null,
                description: document.getElementById('site-description').value,
                is_active: document.getElementById('site-is-active').checked
            };

            if (!currentEditSiteId) {
                // 새 사업장 추가
                siteData.site_type = document.getElementById('site-type').value;
                siteData.parent_id = document.getElementById('site-parent-id').value || null;
            }

            try {
                const url = currentEditSiteId ? 
                    `/api/admin/sites/${currentEditSiteId}` : 
                    '/api/admin/sites';
                
                const method = currentEditSiteId ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(siteData)
                });

                if (response.ok) {
                    const result = await response.json();
                    if (result.success) {
                        alert(currentEditSiteId ? '사업장이 수정되었습니다.' : '새 사업장이 추가되었습니다.');
                        closeSiteModal();
                        loadSitesTree();
                    } else {
                        alert('❌ ' + (result.message || '저장 중 오류가 발생했습니다.'));
                    }
                } else {
                    const errorText = await response.text();
                    console.error('Server error:', errorText);
                    alert(`❌ 서버 오류 (${response.status}): ${errorText}`);
                }
            } catch (error) {
                console.error('사업장 저장 실패:', error);
                alert('❌ 저장 중 오류가 발생했습니다: ' + error.message);
            }
        }

        // 사업장 테이블 뷰 로드
        async function loadSitesTable() {
            try {
                const response = await fetch('/api/admin/sites/debug');
                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(data.message || '사업장 데이터 로드 실패');
                }
                
                // 테이블 HTML 생성
                let tableHtml = `
                    <div id="sites-table-container" style="margin-top: 20px;">
                        <h4>모든 사업장 목록</h4>
                        <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                            <thead>
                                <tr style="background-color: #f5f5f5; border-bottom: 2px solid #ddd;">
                                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">ID</th>
                                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">코드</th>
                                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">이름</th>
                                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">종류</th>
                                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">상위ID</th>
                                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">레벨</th>
                                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">활성</th>
                                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">연락처</th>
                                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">작업</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                // 각 사업장 데이터 렌더링
                data.sites.forEach(site => {
                    tableHtml += `
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 8px; border: 1px solid #ddd;">${site.id}</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">${site.code || '-'}</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">${site.name}</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">${site.site_type || '-'}</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">${site.parent_id || '-'}</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">${site.level}</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">${site.is_active ? '활성' : '비활성'}</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">${site.contact_person || '-'}</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">
                                <button class="btn-small btn-primary" onclick="editSite(${site.id})" style="margin-right: 5px; padding: 4px 8px; font-size: 12px;">수정</button>
                                <button class="btn-small btn-danger" onclick="deleteSite(${site.id})" style="padding: 4px 8px; font-size: 12px;">삭제</button>
                            </td>
                        </tr>
                    `;
                });
                
                tableHtml += `
                            </tbody>
                        </table>
                    </div>
                `;
                
                // sites-container의 내용을 테이블로 교체
                const sitesContainer = document.querySelector('.sites-container');
                if (sitesContainer) {
                    sitesContainer.innerHTML = tableHtml;
                } else {
                    console.error('sites-container를 찾을 수 없습니다.');
                }
                
            } catch (error) {
                console.error('사업장 테이블 로드 실패:', error);
                alert('사업장 데이터를 불러올 수 없습니다.');
            }
        }

        // ===== 식자재 업로드 관련 함수들 =====
        
        let selectedFiles = [];
        
        // 업로드 섹션 표시/숨기기
        function showUploadSection() {
            const uploadSection = document.getElementById('upload-section');
            const isVisible = uploadSection.style.display !== 'none';
            uploadSection.style.display = isVisible ? 'none' : 'block';
        }

        // 식자재 관리 함수들은 modules/ingredients/ingredients.js로 이동됨

        // 파일 선택 이벤트 처리
        document.addEventListener('DOMContentLoaded', function() {
            const fileInput = document.getElementById('file-input');
            const uploadArea = document.querySelector('.upload-area');
            
            if (fileInput && uploadArea) {
                // 파일 선택 이벤트
                fileInput.addEventListener('change', handleFileSelect);
                
                // 드래그 앤 드롭 이벤트
                uploadArea.addEventListener('dragover', handleDragOver);
                uploadArea.addEventListener('drop', handleDrop);
                uploadArea.addEventListener('dragleave', handleDragLeave);
            }
        });

        function handleFileSelect(event) {
            const files = Array.from(event.target.files);
            addFiles(files);
        }

        function handleDragOver(event) {
            event.preventDefault();
            event.currentTarget.classList.add('dragover');
        }

        function handleDrop(event) {
            event.preventDefault();
            event.currentTarget.classList.remove('dragover');
            const files = Array.from(event.dataTransfer.files);
            addFiles(files);
        }

        function handleDragLeave(event) {
            event.currentTarget.classList.remove('dragover');
        }

        function addFiles(files) {
            // 파일 형식 검증
            const validFiles = files.filter(file => {
                const isValidType = file.type.includes('sheet') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls');
                const isValidSize = file.size <= 10 * 1024 * 1024; // 10MB
                
                if (!isValidType) {
                    alert(`${file.name}은(는) 지원하지 않는 파일 형식입니다.`);
                    return false;
                }
                
                if (!isValidSize) {
                    alert(`${file.name}은(는) 파일 크기가 10MB를 초과합니다.`);
                    return false;
                }
                
                return true;
            });

            // 중복 파일 체크
            validFiles.forEach(file => {
                const isDuplicate = selectedFiles.some(selectedFile => 
                    selectedFile.name === file.name && selectedFile.size === file.size
                );
                
                if (!isDuplicate) {
                    selectedFiles.push(file);
                }
            });

            updateFileList();
            updateUploadButton();
        }

        function updateFileList() {
            const uploadText = document.querySelector('.upload-text h4');
            const uploadBtn = document.getElementById('upload-btn');
            const filesList = document.getElementById('selected-files-list');
            
            if (selectedFiles.length > 0) {
                uploadText.textContent = `${selectedFiles.length}개 파일이 선택되었습니다`;
                uploadBtn.disabled = false;
                
                // 선택된 파일 목록 표시
                let filesHTML = '<h4 style="margin-bottom: 10px;">선택된 파일:</h4>';
                filesHTML += '<ul style="list-style: none; padding: 0;">';
                selectedFiles.forEach((file, index) => {
                    filesHTML += `
                        <li style="padding: 8px; background: #f8f9fa; margin-bottom: 5px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
                            <span>${file.name} (${(file.size / 1024).toFixed(2)} KB)</span>
                            <button onclick="removeFile(${index})" style="background: #dc3545; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">제거</button>
                        </li>
                    `;
                });
                filesHTML += '</ul>';
                filesList.innerHTML = filesHTML;
            } else {
                uploadText.textContent = '파일을 선택하거나 여기로 드래그하세요';
                uploadBtn.disabled = true;
                filesList.innerHTML = '<p style="color: #666; text-align: center; padding: 20px;">선택된 파일이 없습니다.</p>';
            }
        }

        function updateUploadButton() {
            const uploadBtn = document.getElementById('upload-btn');
            uploadBtn.disabled = selectedFiles.length === 0;
        }

        function removeFile(index) {
            selectedFiles.splice(index, 1);
            updateFileList();
            updateUploadButton();
        }
        
        function clearFiles() {
            selectedFiles = [];
            document.getElementById('file-input').value = '';
            updateFileList();
            updateUploadButton();
            hideResults();
        }

        function hideResults() {
            document.getElementById('upload-results').style.display = 'none';
        }

        // 파일 업로드 실행 함수
        async function uploadFiles() {
            if (selectedFiles.length === 0) {
                alert('업로드할 파일을 선택해주세요.');
                return;
            }
            
            const progressSection = document.getElementById('upload-progress');
            const progressFill = document.getElementById('progress-fill');
            const progressText = document.getElementById('progress-text');
            
            // 프로그레스 바 표시
            if (progressSection) {
                progressSection.style.display = 'block';
            }
            
            let successCount = 0;
            let errorCount = 0;
            const results = [];
            
            for (let i = 0; i < selectedFiles.length; i++) {
                const file = selectedFiles[i];
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    // 프로그레스 업데이트
                    const progress = ((i + 1) / selectedFiles.length) * 100;
                    if (progressFill) progressFill.style.width = progress + '%';
                    if (progressText) progressText.textContent = `${i + 1}/${selectedFiles.length} 파일 처리 중...`;
                    
                    const response = await fetch('/api/admin/ingredients/excel/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        successCount++;
                        results.push({
                            filename: file.name,
                            status: 'success',
                            message: `${result.total_rows || 0}개 행 처리 완료`
                        });
                    } else {
                        errorCount++;
                        results.push({
                            filename: file.name,
                            status: 'error',
                            message: result.message || '업로드 실패'
                        });
                    }
                } catch (error) {
                    errorCount++;
                    results.push({
                        filename: file.name,
                        status: 'error',
                        message: error.message
                    });
                }
            }
            
            // 프로그레스 바 숨기기
            if (progressSection) {
                setTimeout(() => {
                    progressSection.style.display = 'none';
                }, 1000);
            }
            
            // 결과 표시
            showUploadResults(successCount, errorCount, results);
            
            // 파일 목록 초기화
            clearFiles();
        }

        function showUploadResults(successCount, errorCount, results) {
            document.getElementById('success-count').textContent = successCount;
            document.getElementById('error-count').textContent = errorCount;
            
            const resultDetails = document.getElementById('result-details');
            resultDetails.innerHTML = '';
            
            results.forEach(result => {
                const resultDiv = document.createElement('div');
                resultDiv.className = `result-file ${result.status}`;
                
                resultDiv.innerHTML = `
                    <div class="file-name">${result.fileName}</div>
                    <div class="file-status ${result.status}">
                        <span>${result.status === 'success' ? '✓' : '✗'}</span>
                        <span>${result.message}</span>
                    </div>
                `;
                
                resultDetails.appendChild(resultDiv);
            });
            
            document.getElementById('upload-results').style.display = 'block';
        }

        // 식자재 목록은 이제 별도 페이지(/ingredients)에서 관리됩니다
        // loadIngredientsList 함수는 더 이상 사용되지 않습니다

        // 공급업체 필터 로드
        async function loadSupplierFilter() {
            try {
                const response = await fetch('/api/admin/suppliers/enhanced');
                const result = await response.json();
                const suppliers = result.suppliers || result.data || [];
                
                const supplierFilter = document.getElementById('supplier-filter');
                supplierFilter.innerHTML = '<option value="">전체 업체</option>';
                
                suppliers.forEach(supplier => {
                    const option = document.createElement('option');
                    option.value = supplier.id;
                    option.textContent = supplier.name;
                    supplierFilter.appendChild(option);
                });
                
            } catch (error) {
                console.error('공급업체 목록 로드 실패:', error);
            }
        }

        // 식자재 수정/삭제 기능은 /ingredients 페이지에서 관리됩니다

        // 업로드 히스토리 로드
        async function loadUploadHistory() {
            try {
                const response = await fetch('/api/admin/ingredient-upload-history');
                const result = await response.json();
                
                if (result.success) {
                    const tbody = document.getElementById('upload-history-tbody');
                    tbody.innerHTML = '';
                    
                    if (result.histories.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: #666;">업로드 히스토리가 없습니다.</td></tr>';
                        return;
                    }
                    
                    result.histories.forEach(history => {
                        const statusBadge = getStatusBadge(history.status);
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td style="border: 1px solid #dee2e6; padding: 10px; text-align: center;">${new Date(history.upload_date).toLocaleDateString()}</td>
                            <td style="border: 1px solid #dee2e6; padding: 10px; text-align: center;">${history.uploaded_by}</td>
                            <td style="border: 1px solid #dee2e6; padding: 10px;">${history.filename}</td>
                            <td style="border: 1px solid #dee2e6; padding: 10px; text-align: center;">${history.total_rows}</td>
                            <td style="border: 1px solid #dee2e6; padding: 10px; text-align: center; color: #28a745; font-weight: bold;">${history.processed_count + history.updated_count}</td>
                            <td style="border: 1px solid #dee2e6; padding: 10px; text-align: center; color: #dc3545; font-weight: bold;">${history.error_count}</td>
                            <td style="border: 1px solid #dee2e6; padding: 10px; text-align: center;">${statusBadge}</td>
                            <td style="border: 1px solid #dee2e6; padding: 10px; text-align: center;">
                                <button onclick="showUploadDetails(${history.id})" style="padding: 4px 8px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 12px;">
                                    상세보기
                                </button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                } else {
                    console.error('업로드 히스토리 로드 실패:', result.message);
                }
            } catch (error) {
                console.error('업로드 히스토리 로드 중 오류:', error);
                document.getElementById('upload-history-tbody').innerHTML = 
                    '<tr><td colspan="8" style="text-align: center; color: #dc3545;">업로드 히스토리를 불러올 수 없습니다.</td></tr>';
            }
        }

        // 상태 배지 생성
        function getStatusBadge(status) {
            switch (status) {
                case 'completed':
                    return '<span style="background: #28a745; color: white; padding: 4px 8px; border-radius: 3px; font-size: 12px;">완료</span>';
                case 'completed_with_errors':
                    return '<span style="background: #ffc107; color: #212529; padding: 4px 8px; border-radius: 3px; font-size: 12px;">일부실패</span>';
                case 'failed':
                    return '<span style="background: #dc3545; color: white; padding: 4px 8px; border-radius: 3px; font-size: 12px;">실패</span>';
                case 'processing':
                    return '<span style="background: #17a2b8; color: white; padding: 4px 8px; border-radius: 3px; font-size: 12px;">처리중</span>';
                default:
                    return '<span style="background: #6c757d; color: white; padding: 4px 8px; border-radius: 3px; font-size: 12px;">알 수 없음</span>';
            }
        }

        // 업로드 상세 보기
        function showUploadDetails(historyId) {
            // 상세 보기 모달 구현 (추후)
            alert(`업로드 ID ${historyId}의 상세 정보 조회 기능은 곧 구현될 예정입니다.`);
        }

        // ===== 식수 등록 관리 관련 함수들 =====
        
        // 식수 등록 페이지 초기화
        function initMealCountsPage() {
            // 오늘 날짜를 기본값으로 설정
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('meal-count-date').value = today;
            document.getElementById('form-meal-date').value = today;
        }

        // 식수 데이터 로드
        async function loadMealCounts() {
            try {
                const selectedDate = document.getElementById('meal-count-date').value;
                const url = selectedDate ? `/api/admin/meal-counts?date=${selectedDate}` : '/api/admin/meal-counts';
                
                const response = await fetch(url);
                const mealCounts = await response.json();
                
                updateMealCountsSummary(mealCounts);
                updateMealCountsTable(mealCounts);
                
            } catch (error) {
                console.error('식수 데이터 로드 실패:', error);
                document.getElementById('meal-counts-tbody').innerHTML = 
                    '<tr><td colspan="8" style="text-align: center; color: #dc3545;">식수 데이터를 불러올 수 없습니다.</td></tr>';
            }
        }

        // 식수 현황 요약 업데이트
        function updateMealCountsSummary(mealCounts) {
            let totalCount = 0;
            let totalCost = 0;
            let deliverySites = new Set();
            
            mealCounts.forEach(item => {
                totalCount += item.total_count || 0;
                totalCost += (item.target_material_cost || 0) * (item.total_count || 0);
                deliverySites.add(item.delivery_site);
            });
            
            document.getElementById('total-meal-count').textContent = `${totalCount.toLocaleString()}명`;
            document.getElementById('avg-material-cost').textContent = 
                totalCount > 0 ? `${Math.round(totalCost / totalCount).toLocaleString()}원` : '0원';
            document.getElementById('delivery-sites-count').textContent = `${deliverySites.size}개소`;
            document.getElementById('estimated-total-cost').textContent = `${totalCost.toLocaleString()}원`;
        }

        // 식수 데이터 테이블 업데이트
        function updateMealCountsTable(mealCounts) {
            const tbody = document.getElementById('meal-counts-tbody');
            tbody.innerHTML = '';
            
            if (mealCounts.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: #666;">등록된 식수 데이터가 없습니다.</td></tr>';
                return;
            }
            
            mealCounts.forEach((item, index) => {
                // 메인 행
                const mainRow = document.createElement('tr');
                mainRow.innerHTML = `
                    <td class="delivery-site-cell" rowspan="${item.site_details.length + 1}">${item.delivery_site}</td>
                    <td class="meal-type-cell" rowspan="${item.site_details.length + 1}">${item.meal_type}</td>
                    <td class="cost-cell" rowspan="${item.site_details.length + 1}">${(item.target_material_cost || 0).toLocaleString()}원</td>
                    <td class="count-cell" rowspan="${item.site_details.length + 1}">${(item.total_count || 0).toLocaleString()}명</td>
                    <td colspan="3" style="background: #f0f8ff; font-weight: 500;">${item.menu_info || '-'}</td>
                    <td rowspan="${item.site_details.length + 1}">
                        <div class="btn-group">
                            <button class="btn-small btn-primary" onclick="editMealCount(${item.id})">수정</button>
                            <button class="btn-small btn-warning" onclick="duplicateMealCount(${item.id})">복사</button>
                        </div>
                    </td>
                `;
                tbody.appendChild(mainRow);
                
                // 사업장별 상세 행들
                item.site_details.forEach(site => {
                    const detailRow = document.createElement('tr');
                    detailRow.className = 'site-detail-row';
                    detailRow.innerHTML = `
                        <td>${site.site_name}</td>
                        <td class="count-cell">${site.count}명</td>
                        <td>${site.notes || '-'}</td>
                    `;
                    tbody.appendChild(detailRow);
                });
            });
        }

        // 식수 등록 모달 표시
        function showAddMealCountModal() {
            document.getElementById('meal-count-modal-title').textContent = '식수 등록';
            document.getElementById('meal-count-form').reset();
            document.getElementById('meal-count-id').value = '';
            
            // 선택된 날짜를 폼에도 반영
            const selectedDate = document.getElementById('meal-count-date').value;
            document.getElementById('form-meal-date').value = selectedDate;
            
            document.getElementById('meal-count-modal').classList.remove('hidden');
        }

        // 식수 등록 모달 닫기
        function closeMealCountModal() {
            document.getElementById('meal-count-modal').classList.add('hidden');
        }

        // 식수 데이터 저장
        async function saveMealCount() {
            try {
                const formData = {
                    meal_date: document.getElementById('form-meal-date').value,
                    delivery_site: document.getElementById('form-delivery-site').value.trim(),
                    meal_type: document.getElementById('form-meal-type').value,
                    target_material_cost: parseInt(document.getElementById('form-target-cost').value) || 0,
                    menu_info: document.getElementById('form-menu-info').value.trim(),
                    site_counts: document.getElementById('form-site-counts').value.trim(),
                    notes: document.getElementById('form-notes').value.trim()
                };

                // 유효성 검사
                if (!formData.meal_date || !formData.delivery_site || !formData.meal_type) {
                    alert('필수 항목을 모두 입력해주세요.');
                    return;
                }

                if (!formData.site_counts) {
                    alert('사업장별 식수를 입력해주세요.');
                    return;
                }

                const mealCountId = document.getElementById('meal-count-id').value;
                const url = mealCountId ? `/api/admin/meal-counts/${mealCountId}` : '/api/admin/meal-counts';
                const method = mealCountId ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();

                if (result.success) {
                    alert(mealCountId ? '식수 정보가 수정되었습니다.' : '식수 정보가 등록되었습니다.');
                    closeMealCountModal();
                    loadMealCounts();
                } else {
                    alert(result.message || '저장 중 오류가 발생했습니다.');
                }
                
            } catch (error) {
                console.error('식수 데이터 저장 실패:', error);
                alert('저장 중 오류가 발생했습니다.');
            }
        }

        // 식수 데이터 수정
        async function editMealCount(mealCountId) {
            try {
                const response = await fetch(`/api/admin/meal-counts/${mealCountId}`);
                const mealCount = await response.json();
                
                if (mealCount) {
                    document.getElementById('meal-count-modal-title').textContent = '식수 수정';
                    document.getElementById('meal-count-id').value = mealCount.id;
                    document.getElementById('form-meal-date').value = mealCount.meal_date;
                    document.getElementById('form-delivery-site').value = mealCount.delivery_site;
                    document.getElementById('form-meal-type').value = mealCount.meal_type;
                    document.getElementById('form-target-cost').value = mealCount.target_material_cost;
                    document.getElementById('form-menu-info').value = mealCount.menu_info || '';
                    document.getElementById('form-notes').value = mealCount.notes || '';
                    
                    // 사업장별 식수 데이터 변환
                    const siteCountsText = mealCount.site_details.map(site => 
                        `${site.site_name}:${site.count}`
                    ).join(',');
                    document.getElementById('form-site-counts').value = siteCountsText;
                    
                    document.getElementById('meal-count-modal').classList.remove('hidden');
                }
                
            } catch (error) {
                console.error('식수 데이터 로드 실패:', error);
                alert('식수 정보를 불러올 수 없습니다.');
            }
        }

        // 식수 데이터 복사
        async function duplicateMealCount(mealCountId) {
            try {
                const response = await fetch(`/api/admin/meal-counts/${mealCountId}`);
                const mealCount = await response.json();
                
                if (mealCount) {
                    document.getElementById('meal-count-modal-title').textContent = '식수 복사 등록';
                    document.getElementById('meal-count-id').value = ''; // 새로운 등록이므로 ID 비움
                    
                    // 오늘 날짜로 설정
                    const today = new Date().toISOString().split('T')[0];
                    document.getElementById('form-meal-date').value = today;
                    
                    document.getElementById('form-delivery-site').value = mealCount.delivery_site;
                    document.getElementById('form-meal-type').value = mealCount.meal_type;
                    document.getElementById('form-target-cost').value = mealCount.target_material_cost;
                    document.getElementById('form-menu-info').value = mealCount.menu_info || '';
                    document.getElementById('form-notes').value = '';
                    
                    // 사업장별 식수 데이터 변환
                    const siteCountsText = mealCount.site_details.map(site => 
                        `${site.site_name}:${site.count}`
                    ).join(',');
                    document.getElementById('form-site-counts').value = siteCountsText;
                    
                    document.getElementById('meal-count-modal').classList.remove('hidden');
                }
                
            } catch (error) {
                console.error('식수 데이터 로드 실패:', error);
                alert('식수 정보를 불러올 수 없습니다.');
            }
        }

        // 식수 데이터 새로고침
        function refreshMealCounts() {
            loadMealCounts();
        }

        // 발주서 출력 (추후 구현)
        function exportMealCounts() {
            alert('발주서 출력 기능은 곧 구현될 예정입니다.');
        }

        // 날짜 변경 이벤트
        document.addEventListener('DOMContentLoaded', function() {
            const mealCountDateInput = document.getElementById('meal-count-date');
            if (mealCountDateInput) {
                mealCountDateInput.addEventListener('change', loadMealCounts);
            }
        });

        // ===================
        // 사용자 관리 확장 기능
        // ===================
        
        // 사용자 비밀번호 초기화
        async function resetPassword(userId) {
            if (!confirm('이 사용자의 비밀번호를 초기화하시겠습니까?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/admin/users/${userId}/reset-password`, {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(`비밀번호가 초기화되었습니다.\n새 비밀번호: ${result.new_password}\n사용자에게 새 비밀번호를 전달해주세요.`);
                } else {
                    alert('비밀번호 초기화에 실패했습니다.');
                }
            } catch (error) {
                console.error('비밀번호 초기화 오류:', error);
                alert('비밀번호 초기화 중 오류가 발생했습니다.');
            }
        }
        
        // 사용자 활성 상태 토글
        async function toggleUserStatus(userId, newStatus) {
            const statusText = newStatus ? '활성화' : '비활성화';
            if (!confirm(`이 사용자를 ${statusText}하시겠습니까?`)) {
                return;
            }
            
            try {
                const response = await fetch(`/api/admin/users/${userId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ is_active: newStatus })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(`사용자가 ${statusText}되었습니다.`);
                    loadUsers(); // 목록 새로고침
                } else {
                    alert('상태 변경에 실패했습니다.');
                }
            } catch (error) {
                console.error('상태 변경 오류:', error);
                alert('상태 변경 중 오류가 발생했습니다.');
            }
        }
        
        // 사업장 관리 모달 표시
        async function manageSites(userId) {
            try {
                // 사용자 사업장 정보 가져오기
                const response = await fetch(`/api/admin/users/${userId}/sites`);
                const data = await response.json();
                
                // 모든 사업장 체크박스 생성
                const sitesList = document.getElementById('sites-list');
                sitesList.innerHTML = '';
                
                data.all_sites.forEach(site => {
                    const isAssigned = data.assigned_site_ids.includes(site.id);
                    const siteDiv = document.createElement('div');
                    siteDiv.innerHTML = `
                        <label class="checkbox-label" style="margin-bottom: 5px;">
                            <input type="checkbox" 
                                   value="${site.id}" 
                                   ${isAssigned ? 'checked' : ''} 
                                   onchange="updateSitesAllStatus()">
                            ${site.name} (${site.location})
                        </label>
                    `;
                    sitesList.appendChild(siteDiv);
                });
                
                // 전체 선택 체크박스 상태 업데이트
                updateSitesAllStatus();
                
                // 모달에 사용자 ID 저장
                document.getElementById('user-sites-container').setAttribute('data-user-id', userId);
                
                // 사업장 관리 모달 표시
                showSitesModal();
                
            } catch (error) {
                console.error('사업장 정보 로드 오류:', error);
                alert('사업장 정보를 불러올 수 없습니다.');
            }
        }
        
        // 사업장 관리 모달 표시 함수
        function showSitesModal() {
            // 간단한 모달 HTML 생성 (기존 모달 재사용할 수도 있음)
            const modalHtml = `
                <div id="sites-modal" class="modal" style="display: block;">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3>사업장 접근 권한 관리</h3>
                            <button class="modal-close" onclick="closeSitesModal()">&times;</button>
                        </div>
                        <div class="modal-body">
                            <div class="form-group">
                                <label>접근 가능한 사업장</label>
                                <div id="user-sites-container-modal" style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; border-radius: 4px;">
                                    <label class="checkbox-label" style="margin-bottom: 10px;">
                                        <input type="checkbox" id="sites-all-modal" onchange="toggleAllSitesModal(this)">
                                        <strong>모든 사업장</strong>
                                    </label>
                                    <div id="sites-list-modal">
                                        ${document.getElementById('sites-list').innerHTML}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button class="btn-primary" onclick="saveSitesAssignment()">저장</button>
                            <button class="btn-secondary" onclick="closeSitesModal()">취소</button>
                        </div>
                    </div>
                </div>
            `;
            
            // 기존 모달 제거 후 새 모달 추가
            const existingModal = document.getElementById('sites-modal');
            if (existingModal) {
                existingModal.remove();
            }
            
            document.body.insertAdjacentHTML('beforeend', modalHtml);
        }
        
        // 사업장 모달 닫기
        function closeSitesModal() {
            const modal = document.getElementById('sites-modal');
            if (modal) {
                modal.remove();
            }
        }
        
        // 모든 사업장 선택/해제
        function toggleAllSites(checkbox) {
            const sitesList = document.getElementById('sites-list');
            const siteCheckboxes = sitesList.querySelectorAll('input[type="checkbox"]');
            
            siteCheckboxes.forEach(cb => {
                cb.checked = checkbox.checked;
            });
        }
        
        // 모든 사업장 선택/해제 (모달용)
        function toggleAllSitesModal(checkbox) {
            const sitesList = document.getElementById('sites-list-modal');
            const siteCheckboxes = sitesList.querySelectorAll('input[type="checkbox"]');
            
            siteCheckboxes.forEach(cb => {
                cb.checked = checkbox.checked;
            });
        }
        
        // 전체 선택 상태 업데이트
        function updateSitesAllStatus() {
            const sitesList = document.getElementById('sites-list');
            const allCheckbox = document.getElementById('sites-all');
            
            if (!sitesList || !allCheckbox) return;
            
            const siteCheckboxes = sitesList.querySelectorAll('input[type="checkbox"]');
            const checkedCount = Array.from(siteCheckboxes).filter(cb => cb.checked).length;
            
            allCheckbox.checked = checkedCount === siteCheckboxes.length && siteCheckboxes.length > 0;
        }
        
        // 사업장 할당 저장
        async function saveSitesAssignment() {
            const userId = document.getElementById('user-sites-container').getAttribute('data-user-id');
            const sitesList = document.getElementById('sites-list-modal');
            const checkedSites = Array.from(sitesList.querySelectorAll('input[type="checkbox"]:checked'))
                                       .map(cb => parseInt(cb.value));
            
            try {
                const response = await fetch(`/api/admin/users/${userId}/sites`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ site_ids: checkedSites })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('사업장 할당이 저장되었습니다.');
                    closeSitesModal();
                    loadUsers(); // 목록 새로고침
                } else {
                    alert('사업장 할당 저장에 실패했습니다.');
                }
            } catch (error) {
                console.error('사업장 할당 저장 오류:', error);
                alert('저장 중 오류가 발생했습니다.');
            }
        }
        
        // 데이터베이스 확장 초기화
        async function initUserExtensions() {
            if (!confirm('사용자 관리 기능을 확장하시겠습니까? (데이터베이스 업데이트)')) {
                return;
            }
            
            try {
                const response = await fetch('/api/admin/init_user_extensions', {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('사용자 관리 기능이 확장되었습니다.\n페이지를 새로고침합니다.');
                    window.location.reload();
                } else {
                    alert('기능 확장에 실패했습니다.');
                }
            } catch (error) {
                console.error('기능 확장 오류:', error);
                alert('기능 확장 중 오류가 발생했습니다.');
            }
        }
        
        // ===========================================
        // 공급업체 관리 확장 기능
        // ===========================================
        
        // 탭 전환 함수들
        function showIngredientTab() {
            document.getElementById('ingredient-tab-content').classList.remove('hidden');
            
            // 탭 버튼 스타일 변경
            const tabButton = document.querySelector('.tab-button');
            if (tabButton) {
                tabButton.style.borderBottomColor = '#007bff';
                tabButton.style.backgroundColor = '#f8f9fa';
            }
        }
        
        
        // 공급업체 기능 확장 초기화
        async function initSupplierExtensions() {
            if (!confirm('공급업체 관리 기능을 확장하시겠습니까? (데이터베이스 업데이트)')) {
                return;
            }
            
            try {
                const response = await fetch('/api/admin/init_supplier_extensions', {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(result.message + '\n페이지를 새로고침합니다.');
                    window.location.reload();
                } else {
                    alert('기능 확장에 실패했습니다: ' + result.message);
                }
            } catch (error) {
                console.error('기능 확장 오류:', error);
                alert('기능 확장 중 오류가 발생했습니다.');
            }
        }
        
        // 공급업체 관리 변수들
        let currentSupplierPage = 1;
        let totalSupplierPages = 1;
        let currentEditSupplierId = null;
        
        // 공급업체 목록 로드
        async function loadSuppliers() {
            try {
                const search = document.getElementById('supplier-search')?.value || '';
                const page = currentSupplierPage || 1;
                const response = await fetch(`/api/admin/suppliers/enhanced?page=${page}&limit=20&search=${encodeURIComponent(search)}`);
                const data = await response.json();
                
                if (data.suppliers) {
                    displaySuppliers(data.suppliers);
                    updateSupplierPagination(data.page, data.total_pages);
                }
            } catch (error) {
                console.error('공급업체 목록 로드 실패:', error);
                document.getElementById('suppliers-table-body').innerHTML = 
                    '<tr><td colspan="11">공급업체 목록을 불러올 수 없습니다.</td></tr>';
            }
        }
        
        // 공급업체 목록 표시
        function displaySuppliers(suppliers) {
            const tbody = document.getElementById('suppliers-table-body');
            
            if (!suppliers || suppliers.length === 0) {
                tbody.innerHTML = '<tr><td colspan="11">등록된 공급업체가 없습니다.</td></tr>';
                return;
            }
            
            tbody.innerHTML = suppliers.map(supplier => `
                <tr>
                    <td><strong>${supplier.parent_code || '-'}</strong></td>
                    <td><strong>${supplier.site_code || '-'}</strong></td>
                    <td>${supplier.site_name || '-'}</td>
                    <td><strong>${supplier.name || '-'}</strong></td>
                    <td>${supplier.phone || supplier.contact || '-'}</td>
                    <td>${supplier.email || '-'}</td>
                    <td><span class="${supplier.is_active ? 'status-active' : 'status-inactive'}">
                        ${supplier.is_active ? '거래중' : '중단'}
                    </span></td>
                    <td>${supplier.business_number || '-'}</td>
                    <td>${supplier.representative || '-'}</td>
                    <td>${supplier.manager_name || '-'}</td>
                    <td>
                        <button class="btn-small btn-edit" onclick="editSupplier(${supplier.id})" style="background: #28a745; margin-right: 5px;">수정</button>
                        <button class="btn-small btn-toggle" onclick="toggleSupplierStatus(${supplier.id}, ${!supplier.is_active})" 
                                style="background: ${supplier.is_active ? '#dc3545' : '#17a2b8'}; margin-right: 5px;">
                            ${supplier.is_active ? '중단' : '재개'}
                        </button>
                        <button class="btn-small btn-delete" onclick="deleteSupplier(${supplier.id})" style="background: #6c757d;">삭제</button>
                    </td>
                </tr>
            `).join('');
        }
        
        // 공급업체 페이지네이션 업데이트
        function updateSupplierPagination(currentPage, totalPages) {
            currentSupplierPage = currentPage;
            totalSupplierPages = totalPages;
            const pageInfoElement = document.getElementById('supplier-page-info');
            if (pageInfoElement) {
                pageInfoElement.textContent = `${currentPage} / ${totalPages}`;
            }
        }
        
        // 공급업체 페이지 변경
        function changeSupplierPage(direction) {
            const newPage = currentSupplierPage + direction;
            if (newPage >= 1 && newPage <= totalSupplierPages) {
                currentSupplierPage = newPage;
                loadSuppliers();
            }
        }
        
        // 공급업체 검색
        function searchSuppliers() {
            currentSupplierPage = 1;
            loadSuppliers();
        }
        
        // 공급업체 추가 모달 표시
        function showAddSupplierModal() {
            currentEditSupplierId = null;
            document.getElementById('supplier-modal-title').textContent = '새 업체 등록';
            clearSupplierForm();
            document.getElementById('supplier-modal').classList.remove('hidden');
        }
        
        // 공급업체 수정 모달 표시
        async function editSupplier(supplierId) {
            try {
                const response = await fetch(`/api/admin/suppliers/${supplierId}/detail`);
                const result = await response.json();
                const supplier = result.supplier || result;
                
                if (!response.ok) {
                    throw new Error('공급업체 정보를 불러올 수 없습니다.');
                }
                
                currentEditSupplierId = supplierId;
                document.getElementById('supplier-modal-title').textContent = '업체 정보 수정';
                
                // 폼에 데이터 채우기
                document.getElementById('supplier-name').value = supplier.name || '';
                document.getElementById('supplier-parent-code').value = supplier.parent_code || '';
                document.getElementById('supplier-site-code').value = supplier.site_code || supplier.parent_code || '';
                document.getElementById('supplier-site-name').value = supplier.site_name || supplier.name || '';
                document.getElementById('supplier-representative').value = supplier.representative || '';
                document.getElementById('supplier-contact').value = supplier.contact || supplier.representative || '';
                document.getElementById('supplier-phone').value = supplier.phone || supplier.headquarters_phone || '';
                document.getElementById('supplier-fax').value = supplier.fax || supplier.headquarters_fax || '';
                document.getElementById('supplier-email').value = supplier.email || '';
                document.getElementById('supplier-address').value = supplier.address || supplier.headquarters_address || '';
                document.getElementById('supplier-business-number').value = supplier.business_number || '';
                document.getElementById('supplier-business-type').value = supplier.business_type || '';
                document.getElementById('supplier-business-item').value = supplier.business_item || '';
                document.getElementById('supplier-manager-name').value = supplier.manager_name || supplier.representative || '';
                document.getElementById('supplier-manager-phone').value = supplier.manager_phone || supplier.headquarters_phone || '';
                document.getElementById('supplier-update-frequency').value = supplier.update_frequency || 'weekly';
                document.getElementById('supplier-is-active').checked = supplier.is_active !== false;
                document.getElementById('supplier-notes').value = supplier.notes || '';
                
                document.getElementById('supplier-modal').classList.remove('hidden');
                
            } catch (error) {
                console.error('공급업체 정보 로드 오류:', error);
                alert('공급업체 정보를 불러올 수 없습니다.');
            }
        }
        
        // 공급업체 폼 초기화
        function clearSupplierForm() {
            document.getElementById('supplier-form').reset();
            document.getElementById('supplier-is-active').checked = true;
        }
        
        // 공급업체 저장
        async function saveSupplier() {
            const supplierData = {
                name: document.getElementById('supplier-name').value.trim(),
                parent_code: document.getElementById('supplier-parent-code').value.trim(),
                site_code: document.getElementById('supplier-site-code').value.trim(),
                site_name: document.getElementById('supplier-site-name').value.trim(),
                representative: document.getElementById('supplier-representative').value,
                contact: document.getElementById('supplier-contact').value,
                phone: document.getElementById('supplier-phone').value.trim(),
                fax: document.getElementById('supplier-fax').value,
                email: document.getElementById('supplier-email').value.trim(),
                address: document.getElementById('supplier-address').value.trim(),
                business_number: document.getElementById('supplier-business-number').value,
                business_type: document.getElementById('supplier-business-type').value,
                business_item: document.getElementById('supplier-business-item').value,
                manager_name: document.getElementById('supplier-manager-name').value,
                manager_phone: document.getElementById('supplier-manager-phone').value,
                update_frequency: document.getElementById('supplier-update-frequency').value,
                is_active: document.getElementById('supplier-is-active').checked,
                notes: document.getElementById('supplier-notes').value
            };
            
            // 필수 필드 검증
            const parentCode = document.getElementById('supplier-parent-code').value.trim();
            const siteName = document.getElementById('supplier-site-name').value.trim();
            const siteCode = document.getElementById('supplier-site-code').value.trim();
            
            
            if (!supplierData.name) {
                alert('식자재업체명은 필수입니다.');
                return;
            }
            
            if (!supplierData.address) {
                alert('주소는 필수입니다.');
                return;
            }
            
            if (!supplierData.phone && !supplierData.email) {
                alert('연락처 또는 이메일 중 하나는 반드시 입력해야 합니다.');
                return;
            }
            
            // 새로운 필드 추가
            supplierData.parent_code = parentCode;
            supplierData.site_name = siteName;
            supplierData.site_code = siteCode;
            
            try {
                const url = currentEditSupplierId 
                    ? `/api/admin/suppliers/${currentEditSupplierId}/update`
                    : '/api/admin/suppliers/create';
                const method = currentEditSupplierId ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(supplierData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(currentEditSupplierId ? '업체 정보가 수정되었습니다.' : '새 업체가 등록되었습니다.');
                    closeSupplierModal();
                    loadSuppliers();
                } else {
                    alert('저장에 실패했습니다: ' + (result.message || '알 수 없는 오류'));
                }
            } catch (error) {
                console.error('공급업체 저장 오류:', error);
                alert('저장 중 오류가 발생했습니다.');
            }
        }
        
        // 공급업체 거래 상태 토글
        async function toggleSupplierStatus(supplierId, newStatus) {
            const statusText = newStatus ? '거래를 재개' : '거래를 중단';
            if (!confirm(`이 업체와의 ${statusText}하시겠습니까?`)) {
                return;
            }
            
            try {
                const response = await fetch(`/api/admin/suppliers/${supplierId}/update`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ is_active: newStatus })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(`업체 거래 상태가 변경되었습니다.`);
                    loadSuppliers();
                } else {
                    alert('상태 변경에 실패했습니다.');
                }
            } catch (error) {
                console.error('상태 변경 오류:', error);
                alert('상태 변경 중 오류가 발생했습니다.');
            }
        }
        
        // 공급업체 삭제
        async function deleteSupplier(supplierId) {
            if (!confirm('이 업체를 삭제하시겠습니까?\n연관된 식자재가 있는 경우 삭제되지 않습니다.')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/admin/suppliers/${supplierId}/delete`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('업체가 삭제되었습니다.');
                    loadSuppliers();
                } else {
                    alert(result.message || '삭제에 실패했습니다.');
                }
            } catch (error) {
                console.error('업체 삭제 오류:', error);
                alert('삭제 중 오류가 발생했습니다.');
            }
        }
        
        // 공급업체 모달 닫기
        function closeSupplierModal() {
            document.getElementById('supplier-modal').classList.add('hidden');
            currentEditSupplierId = null;
        }
        
        // 자코드 자동 생성 함수
        async function suggestSiteCode() {
            const parentCode = document.getElementById('supplier-parent-code').value.trim();
            if (!parentCode) {
                document.getElementById('supplier-site-code').value = '';
                return;
            }
            
            try {
                // 기존 자코드들 조회
                const response = await fetch(`/api/admin/suppliers/enhanced?search=${parentCode}`);
                const result = await response.json();
                
                if (result.success && result.suppliers) {
                    const existingSiteCodes = result.suppliers
                        .filter(s => s.parent_code === parentCode)
                        .map(s => s.site_code)
                        .filter(code => code && code.includes('-'));
                    
                    // 다음 순번 계산
                    let nextNumber = 1;
                    if (existingSiteCodes.length > 0) {
                        const numbers = existingSiteCodes.map(code => {
                            const parts = code.split('-');
                            return parseInt(parts[parts.length - 1]) || 0;
                        });
                        nextNumber = Math.max(...numbers) + 1;
                    }
                    
                    // 자코드 자동 생성
                    const suggestedCode = `${parentCode}-${String(nextNumber).padStart(2, '0')}`;
                    document.getElementById('supplier-site-code').value = suggestedCode;
                    
                    // 기존 사업장 정보 표시 (existing-sites-info 요소가 있는 경우에만)
                    const infoElement = document.getElementById('existing-sites-info');
                    if (infoElement && existingSiteCodes.length > 0) {
                        infoElement.innerHTML = 
                            `<span style="color: #28a745;">기존 사업장 ${existingSiteCodes.length}개 | 신규: ${suggestedCode}</span>`;
                    }
                } else {
                    // 첫 번째 자코드
                    const suggestedCode = `${parentCode}-01`;
                    document.getElementById('supplier-site-code').value = suggestedCode;
                }
            } catch (error) {
                console.error('자코드 생성 오류:', error);
                // 오류 시 기본 자코드 생성
                const suggestedCode = `${parentCode}-01`;
                document.getElementById('supplier-site-code').value = suggestedCode;
            }
        }
        
        // 자코드 직접 수정 기능
        function editSiteCode() {
            const siteCodeInput = document.getElementById('supplier-site-code');
            if (siteCodeInput.readOnly) {
                siteCodeInput.readOnly = false;
                siteCodeInput.style.backgroundColor = '#ffffff';
                siteCodeInput.focus();
            }
        }

        // ===== 통합 식단표 관리 관련 함수들 =====
        
        // 식단표 탭 전환
        function showMealPlanTab(tabName) {
            // 모든 탭 버튼 비활성화
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // 모든 탭 컨텐츠 숨김
            document.querySelectorAll('.meal-plan-tab-content').forEach(tab => {
                tab.classList.add('hidden');
            });
            
            // 선택된 탭 활성화
            const activeBtn = document.querySelector(`[data-tab="${tabName}"]`);
            if (activeBtn) activeBtn.classList.add('active');
            
            const activeTab = document.getElementById(`${tabName}-tab`);
            if (activeTab) activeTab.classList.remove('hidden');
            
            // 탭별 초기화 로직
            if (tabName === 'master') {
                loadMasterMealPlans();
            } else if (tabName === 'batch') {
                initializeBatchTab();
            }
        }

        // 마스터 식단표 목록 로드
        function loadMasterMealPlans() {
            const listContainer = document.getElementById('master-meal-plan-list');
            if (listContainer) {
                listContainer.innerHTML = `
                    <div style="display: grid; gap: 15px;">
                        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h4>🍱 도시락 마스터 식단표</h4>
                                    <p style="color: #666; margin: 5px 0;">2025년 9월 2주차</p>
                                </div>
                                <div>
                                    <button onclick="editMasterMealPlan('dosirak')" style="padding: 6px 12px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; margin-right: 5px;">편집</button>
                                </div>
                            </div>
                        </div>
                        
                        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h4>🚚 운반 마스터 식단표</h4>
                                    <p style="color: #666; margin: 5px 0;">2025년 9월 2주차</p>
                                </div>
                                <div>
                                    <button onclick="editMasterMealPlan('transport')" style="padding: 6px 12px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; margin-right: 5px;">편집</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
        }

        // 일괄 탭 초기화
        function initializeBatchTab() {
            const today = new Date();
            const todayStr = today.toISOString().split('T')[0];
            const weekLater = new Date(today);
            weekLater.setDate(today.getDate() + 7);
            const weekLaterStr = weekLater.toISOString().split('T')[0];
            
            const startDateEl = document.getElementById('batch-start-date');
            const endDateEl = document.getElementById('batch-end-date');
            if (startDateEl) startDateEl.value = todayStr;
            if (endDateEl) endDateEl.value = weekLaterStr;
        }

        // 식단표 유형별 관리
        function manageMealPlanType(type) {
            const typeNames = {
                'dosirak': '도시락',
                'transport': '운반',
                'school': '학교',
                'care': '요양원'
            };
            alert(`${typeNames[type]} 식단표 관리 기능을 구현 중입니다.`);
        }

        // 마스터 식단표 생성
        function createMasterMealPlan() {
            alert('마스터 식단표 생성 기능을 구현 중입니다.');
        }

        // 마스터 식단표 편집
        function editMasterMealPlan(type) {
            window.open('meal_plan_management.html', '_blank');
        }

        // 지시서 생성 함수들
        function generatePreprocessingInstruction() {
            alert('전처리 지시서 일괄 생성 기능을 구현 중입니다.');
        }

        function generateCookingInstruction() {
            alert('조리 지시서 일괄 생성 기능을 구현 중입니다.');
        }

        function generatePortionInstruction() {
            alert('소분 지시서 일괄 생성 기능을 구현 중입니다.');
        }

        function generateAllInstructions() {
            const dateSelect = document.getElementById('instruction-date-select');
            const selectedDate = dateSelect ? dateSelect.value : '';
            
            if (!selectedDate || selectedDate === '생성할 날짜 선택') {
                alert('생성할 날짜를 선택해주세요.');
                return;
            }
            
            if (confirm(`${selectedDate}에 대한 모든 지시서(전처리, 조리, 소분)를 일괄 생성하시겠습니까?`)) {
                alert('모든 지시서 일괄 생성 기능을 구현 중입니다.');
            }
        }

        // 일괄 생성 함수들
        function batchGenerateMealPlans() {
            const startDate = document.getElementById('batch-start-date')?.value;
            const endDate = document.getElementById('batch-end-date')?.value;
            const targetType = document.getElementById('batch-target-type')?.value;
            
            if (!startDate || !endDate) {
                alert('시작일과 종료일을 모두 선택해주세요.');
                return;
            }
            
            const typeNames = {
                'all': '전체',
                'dosirak': '도시락',
                'transport': '운반',
                'school': '학교',
                'care': '요양원'
            };
            
            if (confirm(`${startDate}부터 ${endDate}까지 ${typeNames[targetType]} 식단표를 일괄 생성하시겠습니까?`)) {
                alert('일괄 생성 기능을 구현 중입니다.');
            }
        }

        function createFromTemplate() {
            alert('템플릿 기반 생성 기능을 구현 중입니다.');
        }

        function showWeeklyMealPlans() {
            alert('주간 식단표 보기 기능을 구현 중입니다.');
        }

        // 식단가 관리 - 사업장 목록 로드 함수
        async function loadBusinessLocationsForMealPricingDirect() {
            try {
                console.log('사업장 목록 로드 시작 (Direct)');
                const response = await fetch('/api/admin/sites/tree');
                const result = await response.json();
                console.log('API 응답:', result);
                
                const businessLocations = result.sites || [];
                console.log('사업장 데이터:', businessLocations);
                
                const select = document.getElementById('businessLocationSelect');
                console.log('select 요소:', select);
                
                if (select) {
                    select.innerHTML = '<option value="">사업장을 선택하세요</option>';
                    businessLocations.forEach(location => {
                        console.log('사업장 추가:', location);
                        select.innerHTML += `<option value="${location.id}">${location.name}</option>`;
                    });
                    console.log('select 옵션 최종 개수:', select.options.length);
                } else {
                    console.error('businessLocationSelect 요소를 찾을 수 없음');
                }
            } catch (error) {
                console.error('사업장 목록 로드 실패:', error);
                const select = document.getElementById('businessLocationSelect');
                if (select) {
                    select.innerHTML = '<option value="">사업장 목록을 불러올 수 없습니다</option>';
                }
            }
        }
        
        // 전역 함수로 등록
        window.loadBusinessLocationsForMealPricingDirect = loadBusinessLocationsForMealPricingDirect;
        
        // 식단가 관리 - 전역 변수
        window.mealPlans = [];
        window.currentLocationId = null;
        
        // 식단표 로드 함수
        async function loadMealPlansForLocation() {
            const businessLocationSelect = document.getElementById('businessLocationSelect');
            const mealPlansContainer = document.getElementById('mealPlansContainer');
            const addMealPlanBtn = document.getElementById('addMealPlanBtn');
            
            if (!businessLocationSelect || !mealPlansContainer) {
                console.error('필수 요소를 찾을 수 없음');
                return;
            }
            
            const selectedLocationId = businessLocationSelect.value;
            window.currentLocationId = selectedLocationId;
            
            console.log('선택된 사업장 ID:', selectedLocationId);
            
            if (!selectedLocationId) {
                mealPlansContainer.innerHTML = '<p style="color: #888; text-align: center; padding: 40px;">사업장을 선택하면 세부식단표 목록이 표시됩니다.</p>';
                if (addMealPlanBtn) addMealPlanBtn.style.display = 'none';
                return;
            }
            
            // 선택된 사업장 이름 가져오기
            const selectedOption = businessLocationSelect.options[businessLocationSelect.selectedIndex];
            const locationName = selectedOption ? selectedOption.text : '알 수 없음';
            
            // 실제 데이터 로드
            try {
                const response = await fetch(`/api/admin/meal-pricing/by-location/${selectedLocationId}`);
                const result = await response.json();
                
                if (result.success && result.mealPlans && result.mealPlans.length > 0) {
                    // 기존 데이터가 있으면 사용
                    window.mealPlans = result.mealPlans.map(plan => ({
                        ...plan,
                        location_name: plan.location_name || locationName
                    }));
                } else {
                    // 데이터가 없으면 기본 식단표 생성
                    window.mealPlans = [
                        {
                            id: null,  // 새 데이터임을 표시
                            name: '기본 식단표',
                            location_name: locationName,
                            meal_time: 'lunch',
                            selling_price: 5000,
                            target_material_cost: 3500,
                            location_id: selectedLocationId
                        }
                    ];
                }
            } catch (error) {
                console.error('식단표 로드 실패:', error);
                // 오류 시 기본 데이터로 표시
                window.mealPlans = [
                    {
                        id: null,
                        name: '기본 식단표',
                        location_name: locationName,
                        meal_time: 'lunch',
                        selling_price: 5000,
                        target_material_cost: 3500,
                        location_id: selectedLocationId
                    }
                ];
            }
            
            displayMealPlans();
            
            if (addMealPlanBtn) addMealPlanBtn.style.display = 'inline-block';
        }
        
        // 식단표 표시 함수
        function displayMealPlans() {
            const mealPlansContainer = document.getElementById('mealPlansContainer');
            if (!mealPlansContainer) return;
            
            if (!window.mealPlans || window.mealPlans.length === 0) {
                mealPlansContainer.innerHTML = '<p style="color: #888; text-align: center; padding: 40px;">등록된 식단표가 없습니다.</p>';
                return;
            }
            
            const tableHTML = `
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="border: 1px solid #dee2e6; padding: 12px; text-align: center; font-weight: 600; width: 15%;">사업장명</th>
                            <th style="border: 1px solid #dee2e6; padding: 12px; text-align: center; font-weight: 600; width: 12%;">시간대</th>
                            <th style="border: 1px solid #dee2e6; padding: 12px; text-align: left; font-weight: 600; width: 20%;">식단표명</th>
                            <th style="border: 1px solid #dee2e6; padding: 12px; text-align: right; font-weight: 600; width: 15%;">판매가 (원)</th>
                            <th style="border: 1px solid #dee2e6; padding: 12px; text-align: right; font-weight: 600; width: 15%;">목표재료비 (원)</th>
                            <th style="border: 1px solid #dee2e6; padding: 12px; text-align: center; font-weight: 600; width: 8%;">비율 (%)</th>
                            <th style="border: 1px solid #dee2e6; padding: 12px; text-align: center; font-weight: 600; width: 15%;">관리</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${window.mealPlans.map(plan => {
                            const costRatio = plan.selling_price > 0 ? ((plan.target_material_cost / plan.selling_price) * 100).toFixed(1) : 0;
                            const isOverLimit = parseFloat(costRatio) > 40;
                            const ratioColor = isOverLimit ? '#dc3545' : '#28a745';
                            
                            return `
                                <tr style="border-bottom: 1px solid #eee;">
                                    <td style="border: 1px solid #dee2e6; padding: 12px; text-align: center; font-weight: 500;">
                                        ${plan.location_name || ''}
                                    </td>
                                    <td style="border: 1px solid #dee2e6; padding: 12px; text-align: center;">
                                        <select id="meal-time-${plan.id}" onchange="updateMealPlanField(${plan.id}, 'meal_time', this.value)" 
                                                style="padding: 6px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; width: 100%;">
                                            <option value="breakfast" ${plan.meal_time === 'breakfast' ? 'selected' : ''}>🌅 조식</option>
                                            <option value="lunch" ${plan.meal_time === 'lunch' ? 'selected' : ''}>☀️ 중식</option>
                                            <option value="dinner" ${plan.meal_time === 'dinner' ? 'selected' : ''}>🌙 석식</option>
                                            <option value="night" ${plan.meal_time === 'night' ? 'selected' : ''}>🌃 야식</option>
                                        </select>
                                    </td>
                                    <td style="border: 1px solid #dee2e6; padding: 12px; font-weight: 500;">
                                        <div style="display: flex; align-items: center; gap: 8px;">
                                            <span style="color: #007bff;">📋</span>
                                            <input type="text" id="plan-name-${plan.id}" value="${plan.name}" 
                                                   onchange="updateMealPlanField(${plan.id}, 'name', this.value)"
                                                   style="border: none; background: transparent; font-weight: 500; width: 100%; font-size: 14px;"
                                                   onblur="this.style.background='transparent'" 
                                                   onfocus="this.style.background='#f8f9fa'">
                                        </div>
                                    </td>
                                    <td style="border: 1px solid #dee2e6; padding: 12px; text-align: right;">
                                        <input type="text" id="selling-price-${plan.id}" value="${Number(plan.selling_price || 0).toLocaleString()}" 
                                               onchange="updateMealPlanField(${plan.id}, 'selling_price', this.value.replace(/,/g, ''))"
                                               onfocus="this.select()"
                                               style="width: 100px; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px; text-align: right;">
                                    </td>
                                    <td style="border: 1px solid #dee2e6; padding: 12px; text-align: right;">
                                        <input type="text" id="target-cost-${plan.id}" value="${Number(plan.target_material_cost || 0).toLocaleString()}"
                                               onchange="updateMealPlanField(${plan.id}, 'target_material_cost', this.value.replace(/,/g, ''))"
                                               onfocus="this.select()"
                                               style="width: 100px; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px; text-align: right;">
                                    </td>
                                    <td style="border: 1px solid #dee2e6; padding: 12px; text-align: center;">
                                        <span id="cost-ratio-${plan.id}" style="color: ${ratioColor}; font-weight: bold; font-size: 14px;">
                                            ${costRatio}%
                                        </span>
                                        ${isOverLimit ? '<div style="font-size: 10px; color: #dc3545;">⚠️ 목표 초과</div>' : ''}
                                    </td>
                                    <td style="border: 1px solid #dee2e6; padding: 12px; text-align: center;">
                                        <div style="display: flex; gap: 5px; justify-content: center;">
                                            <button onclick="duplicateMealPlan(${plan.id})" 
                                                    style="padding: 4px 8px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 12px;">
                                                복사
                                            </button>
                                            <button onclick="deleteMealPlan(${plan.id})" 
                                                    style="padding: 4px 8px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 12px; ${window.mealPlans.length <= 1 ? 'opacity: 0.5; cursor: not-allowed;' : ''}">
                                                삭제
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            `;
            
            mealPlansContainer.innerHTML = tableHTML;
        }
        
        // 식단표 필드 업데이트
        function updateMealPlanField(planId, field, value) {
            const plan = window.mealPlans.find(p => p.id === planId);
            if (plan) {
                if (field === 'name' || field === 'meal_time') {
                    plan[field] = value;
                } else {
                    plan[field] = parseInt(value) || 0;
                }
                displayMealPlans();
            }
        }
        
        // 새 식단표 추가
        function addNewMealPlan() {
            const name = prompt('새 식단표 이름을 입력하세요:', '새 식단표');
            if (!name || name.trim() === '') return;
            
            // 현재 선택된 사업장 이름 가져오기
            const businessLocationSelect = document.getElementById('businessLocationSelect');
            const selectedOption = businessLocationSelect.options[businessLocationSelect.selectedIndex];
            const locationName = selectedOption ? selectedOption.text : '알 수 없음';
            
            const newPlan = {
                id: Date.now(),
                name: name.trim(),
                location_name: locationName,
                meal_time: 'lunch',
                selling_price: 0,
                target_material_cost: 0,
                location_id: window.currentLocationId
            };
            
            window.mealPlans.push(newPlan);
            displayMealPlans();
        }
        
        // 식단표 삭제
        function deleteMealPlan(planId) {
            if (window.mealPlans.length <= 1) {
                alert('최소 1개의 식단표는 유지해야 합니다.');
                return;
            }
            
            if (!confirm('이 식단표를 삭제하시겠습니까?')) return;
            
            window.mealPlans = window.mealPlans.filter(p => p.id !== planId);
            displayMealPlans();
        }
        
        // 식단표 복사
        function duplicateMealPlan(planId) {
            const plan = window.mealPlans.find(p => p.id === planId);
            if (!plan) return;
            
            const newPlan = {
                id: Date.now(),
                name: plan.name + ' (복사)',
                location_name: plan.location_name,
                meal_time: plan.meal_time,
                selling_price: plan.selling_price,
                target_material_cost: plan.target_material_cost,
                location_id: window.currentLocationId
            };
            
            window.mealPlans.push(newPlan);
            displayMealPlans();
        }
        
        // 전역 함수로 등록
        window.loadMealPlansForLocation = loadMealPlansForLocation;
        window.displayMealPlans = displayMealPlans;
        window.updateMealPlanField = updateMealPlanField;
        window.addNewMealPlan = addNewMealPlan;
        window.deleteMealPlan = deleteMealPlan;
        window.duplicateMealPlan = duplicateMealPlan;
        
        // 단가관리 및 식단가 관리 함수들은 modules/meal-pricing/meal-pricing.js로 이동됨
        
        // 페이지 로드 시 식단가 관리 초기화
        document.addEventListener('DOMContentLoaded', function() {
            // 식단가 관리 페이지가 표시될 때 초기화
            const mealPricingPage = document.getElementById('meal-pricing-page');
            if (mealPricingPage) {
                const observer = new MutationObserver(function(mutations) {
                    mutations.forEach(function(mutation) {
                        if (mutation.attributeName === 'class') {
                            if (!mealPricingPage.classList.contains('hidden')) {
                                console.log('식단가 관리 페이지가 표시됨, 초기화 시작');
                                // 사업장 목록 로드
                                if (typeof loadBusinessLocationsForMealPricingDirect === 'function') {
                                    loadBusinessLocationsForMealPricingDirect();
                                } else {
                                    console.error('loadBusinessLocationsForMealPricingDirect 함수를 찾을 수 없음');
                                }
                            }
                        }
                    });
                });
                observer.observe(mealPricingPage, { attributes: true });
            } else {
                console.error('meal-pricing-page 요소를 찾을 수 없음');
            }

            // 매핑 관리 페이지가 표시될 때 데이터 로드
            const mappingPage = document.getElementById('supplier-mapping-page');
            if (mappingPage) {
                const mappingObserver = new MutationObserver(function(mutations) {
                    mutations.forEach(function(mutation) {
                        if (mutation.attributeName === 'class') {
                            if (!mappingPage.classList.contains('hidden')) {
                                if (typeof loadMappingData === 'function') {
                                    loadMappingData();
                                }
                            }
                        }
                    });
                });
                mappingObserver.observe(mappingPage, { attributes: true });
            }
        });

        // 매핑 관리 함수들은 modules/mappings/mappings.js로 이동됨

