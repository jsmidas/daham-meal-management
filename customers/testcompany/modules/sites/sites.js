// 사업장 관리 모듈
(function() {
'use strict';

// 사업장 관리 관련 변수
let sitesData = [];
let selectedSiteId = null;
let currentEditSiteId = null;

// 사업장 트리 로드
async function loadSitesTree() {
    try {
        console.log('사업장 트리 로딩 시작...');
        const response = await fetch('/api/admin/sites/tree?' + new Date().getTime());
        const data = await response.json();
        console.log('API 응답:', data);
        
        if (data.success) {
            sitesData = data.sites || data.tree || [];
            console.log('[Sites] 사업장 데이터:', sitesData.length, '개');
            renderSitesTree();
        } else {
            console.error('API 오류:', data.message);
            document.getElementById('sites-tree').innerHTML = 
                '<div class="error-message">사업장 목록을 불러올 수 없습니다.</div>';
        }
    } catch (error) {
        console.error('사업장 트리 로드 실패:', error);
        document.getElementById('sites-tree').innerHTML = 
            '<div class="error-message">서버와 연결할 수 없습니다.</div>';
    }
}

// 사업장 트리 렌더링
function renderSitesTree() {
    console.log('[Sites] renderSitesTree 호출됨');
    const container = document.getElementById('sites-tree');
    
    if (!container) {
        console.error('[Sites] sites-tree 요소를 찾을 수 없음');
        return;
    }
    
    console.log('[Sites] 컨테이너 발견됨, 사업장 데이터:', sitesData);
    
    if (!sitesData || sitesData.length === 0) {
        container.innerHTML = '<div class="empty-message">등록된 사업장이 없습니다.</div>';
        console.log('[Sites] 빈 메시지 표시');
        return;
    }
    
    console.log('[Sites] 트리 노드 생성 중...');
    const treeHtml = sitesData.map((site, index) => {
        console.log(`[Sites] 사업장 ${index + 1}:`, site);
        return createTreeNode(site);
    }).join('');
    
    const finalHtml = `
        <div class="tree-controls">
            <button onclick="expandAllSites()" class="btn-small">모두 펼치기</button>
            <button onclick="collapseAllSites()" class="btn-small">모두 접기</button>
        </div>
        <div class="sites-tree">${treeHtml}</div>
    `;
    
    console.log('[Sites] 최종 HTML 길이:', finalHtml.length);
    container.innerHTML = finalHtml;
    console.log('[Sites] 트리 렌더링 완료');
}

// 트리 노드 생성
function createTreeNode(site) {
    const hasChildren = site.children && site.children.length > 0;
    const isExpanded = site.expanded || false;
    const icon = getSiteIcon(site.site_type);
    
    let html = `
        <div class="tree-node" data-site-id="${site.id}">
            <div class="tree-item ${selectedSiteId === site.id ? 'selected' : ''}" 
                 onclick="selectSite(${site.id})">
                ${hasChildren ? `<span class="toggle-icon ${isExpanded ? 'expanded' : ''}" 
                                      onclick="event.stopPropagation(); toggleNode(${site.id})">▶</span>` : 
                                '<span class="spacer"></span>'}
                <span class="site-icon">${icon}</span>
                <span class="site-name">${site.name}</span>
                <span class="site-type">(${getSiteTypeDisplay(site.site_type)})</span>
                <div class="site-actions">
                    <button onclick="event.stopPropagation(); showSiteDetails(${site.id})" class="btn-small">상세</button>
                    <button onclick="event.stopPropagation(); editSite(${site.id})" class="btn-small btn-edit">수정</button>
                    <button onclick="event.stopPropagation(); deleteSite(${site.id})" class="btn-small btn-delete">삭제</button>
                </div>
            </div>
    `;
    
    if (hasChildren && isExpanded) {
        html += `<div class="tree-children">
            ${site.children.map(child => createTreeNode(child)).join('')}
        </div>`;
    }
    
    html += '</div>';
    return html;
}

// 사업장 아이콘 반환
function getSiteIcon(siteType) {
    const icons = {
        'company': '🏢',
        'department': '🏬',
        'location': '🏪',
        'default': '📍'
    };
    return icons[siteType] || icons.default;
}

// 사업장 타입 표시명 반환
function getSiteTypeDisplay(siteType) {
    const typeMap = {
        'company': '회사',
        'department': '부서',
        'location': '사업장'
    };
    return typeMap[siteType] || siteType;
}

// 노드 토글
function toggleNode(siteId) {
    const site = findSiteById(sitesData, siteId);
    if (site) {
        site.expanded = !site.expanded;
        renderSitesTree();
    }
}

// 사업장 ID로 찾기
function findSiteById(sites, siteId) {
    for (const site of sites) {
        if (site.id === siteId) {
            return site;
        }
        if (site.children) {
            const found = findSiteById(site.children, siteId);
            if (found) return found;
        }
    }
    return null;
}

// 모든 사업장 펼치기
function expandAllSites() {
    expandCollapseAll(sitesData, true);
    renderSitesTree();
}

// 모든 사업장 접기
function collapseAllSites() {
    expandCollapseAll(sitesData, false);
    renderSitesTree();
}

// 재귀적으로 모든 노드 펼치기/접기
function expandCollapseAll(sites, expand) {
    sites.forEach(site => {
        site.expanded = expand;
        if (site.children) {
            expandCollapseAll(site.children, expand);
        }
    });
}

// 사업장 선택
function selectSite(siteId) {
    selectedSiteId = siteId;
    renderSitesTree();
    
    // 선택된 사업장 정보 표시
    const site = findSiteById(sitesData, siteId);
    if (site) {
        console.log('선택된 사업장:', site);
    }
}

// 사업장 상세 정보 표시
async function showSiteDetails(siteId) {
    try {
        const response = await fetch(`/api/admin/sites/${siteId}`);
        const result = await response.json();
        const site = result.site || result;
        
        if (site) {
            // 상세 정보 모달이나 패널에 표시
            console.log('사업장 상세 정보:', site);
            alert(`사업장 정보:\n이름: ${site.name}\n주소: ${site.address || '없음'}\n연락처: ${site.phone || '없음'}`);
        }
    } catch (error) {
        console.error('사업장 상세 정보 로드 실패:', error);
        alert('상세 정보를 불러올 수 없습니다.');
    }
}

// 사업장 추가 모달 표시
function showAddSiteModal(siteType, parentId = null) {
    console.log('[Sites] 사업장 추가 모달 표시, 타입:', siteType, '부모ID:', parentId);
    currentEditSiteId = null;
    
    const modalTitle = document.getElementById('site-modal-title');
    const siteForm = document.getElementById('site-form');
    const siteModal = document.getElementById('site-modal');
    
    if (modalTitle) {
        modalTitle.textContent = '새 사업장 추가';
        console.log('[Sites] 모달 제목 설정됨');
    } else {
        console.error('[Sites] site-modal-title 요소를 찾을 수 없음');
    }
    
    if (siteForm) {
        siteForm.reset();
        console.log('[Sites] 사업장 폼 초기화됨');
    } else {
        console.error('[Sites] site-form 요소를 찾을 수 없음');
    }
    
    if (siteType) {
        const siteTypeElement = document.getElementById('site-type');
        if (siteTypeElement) {
            siteTypeElement.value = siteType;
            console.log('[Sites] 사업장 타입 설정됨:', siteType);
        }
    }
    
    if (parentId) {
        const parentIdElement = document.getElementById('site-parent-id');
        if (parentIdElement) {
            parentIdElement.value = parentId;
            console.log('[Sites] 부모 ID 설정됨:', parentId);
        }
    }
    
    if (siteModal) {
        siteModal.classList.remove('hidden');
        // 강제로 display 스타일 설정
        siteModal.style.display = 'flex';
        siteModal.style.visibility = 'visible';
        siteModal.style.opacity = '1';
        siteModal.style.zIndex = '9999';
        console.log('[Sites] 사업장 모달 표시됨');
        console.log('[Sites] 모달 현재 클래스:', siteModal.className);
        console.log('[Sites] 모달 현재 스타일:', siteModal.style.cssText);
    } else {
        console.error('[Sites] site-modal 요소를 찾을 수 없음');
    }
}

// 사업장 수정
async function editSite(siteId) {
    console.log(`[Sites] editSite 함수 호출됨, siteId: ${siteId}`);
    try {
        console.log(`[Sites] API 요청 시작: /api/admin/sites/${siteId}`);
        const response = await fetch(`/api/admin/sites/${siteId}`);
        console.log(`[Sites] API 응답 상태:`, response.status, response.statusText);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log(`[Sites] API 응답 데이터:`, result);
        const site = result.site || result;
        
        // 에러 응답 체크
        if (result.success === false) {
            throw new Error(result.message || '사업장 정보를 불러올 수 없습니다.');
        }
        
        if (site) {
            console.log(`[Sites] 사업장 데이터 확인됨:`, site);
            currentEditSiteId = siteId;
            
            // 모달 제목 설정
            const modalTitle = document.getElementById('site-modal-title');
            if (modalTitle) {
                modalTitle.textContent = '사업장 정보 수정';
                console.log(`[Sites] 모달 제목 설정됨`);
            } else {
                console.error(`[Sites] site-modal-title 요소를 찾을 수 없음`);
            }
            
            // 폼에 기존 데이터 채우기
            const fillField = (id, value) => {
                const element = document.getElementById(id);
                if (element) {
                    if (element.type === 'checkbox') {
                        element.checked = !!value;
                    } else {
                        element.value = value || '';
                    }
                    console.log(`[Sites] ${id} 필드 설정됨:`, value);
                } else {
                    console.warn(`[Sites] ${id} 요소를 찾을 수 없음`);
                }
            };
            
            fillField('site-name', site.name);
            fillField('site-type', site.site_type || site.type);
            fillField('site-address', site.address);
            fillField('site-contact-phone', site.contact_phone || site.phone);
            fillField('site-description', site.description);
            fillField('site-is-active', site.is_active);
            
            // 모달 표시
            const modal = document.getElementById('site-modal');
            if (modal) {
                modal.classList.remove('hidden');
                // CSS 스타일 직접 설정
                modal.style.display = 'flex';
                modal.style.position = 'fixed';
                modal.style.top = '0';
                modal.style.left = '0';
                modal.style.width = '100%';
                modal.style.height = '100%';
                modal.style.background = 'rgba(0,0,0,0.5)';
                modal.style.justifyContent = 'center';
                modal.style.alignItems = 'center';
                modal.style.zIndex = '1000';
                console.log(`[Sites] 모달 표시됨`);
                console.log(`[Sites] 모달 현재 클래스:`, modal.className);
                console.log(`[Sites] 모달 현재 스타일:`, modal.style.cssText);
            } else {
                console.error(`[Sites] site-modal 요소를 찾을 수 없음`);
            }
        } else {
            console.error(`[Sites] 사업장 데이터가 없음`);
        }
    } catch (error) {
        console.error('[Sites] 사업장 정보 로드 실패:', error);
        alert('사업장 정보를 불러올 수 없습니다: ' + error.message);
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
        } else {
            alert('사업장 삭제에 실패했습니다.');
        }
    } catch (error) {
        console.error('사업장 삭제 실패:', error);
        alert('삭제 중 오류가 발생했습니다.');
    }
}

// 사업장 모달 닫기
function closeSiteModal() {
    const modal = document.getElementById('site-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.style.display = 'none';
        console.log(`[Sites] 모달 숨김`);
    }
    currentEditSiteId = null;
}

// 사업장 저장
async function saveSite() {
    const siteData = {
        name: document.getElementById('site-name')?.value || '',
        site_type: document.getElementById('site-type')?.value || '',
        address: document.getElementById('site-address')?.value || '',
        contact_phone: document.getElementById('site-contact-phone')?.value || '',
        contact_person: document.getElementById('site-contact-person')?.value || '',
        portion_size: document.getElementById('site-portion-size')?.value || null,
        description: document.getElementById('site-description')?.value || '',
        is_active: document.getElementById('site-is-active')?.checked || false,
        parent_id: document.getElementById('site-parent-id')?.value || null
    };

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

        const result = await response.json();
        
        if (result.success) {
            alert(currentEditSiteId ? '사업장이 수정되었습니다.' : '새 사업장이 추가되었습니다.');
            closeSiteModal();
            loadSitesTree();
        } else {
            alert('저장 중 오류가 발생했습니다: ' + (result.message || '알 수 없는 오류'));
        }
    } catch (error) {
        console.error('사업장 저장 실패:', error);
        alert('저장 중 오류가 발생했습니다.');
    }
}

// 전역 함수로 내보내기
window.loadSitesTree = loadSitesTree;
window.renderSitesTree = renderSitesTree;
window.createTreeNode = createTreeNode;
window.getSiteIcon = getSiteIcon;
window.getSiteTypeDisplay = getSiteTypeDisplay;
window.toggleNode = toggleNode;
window.expandAllSites = expandAllSites;
window.collapseAllSites = collapseAllSites;
window.selectSite = selectSite;
window.showSiteDetails = showSiteDetails;
window.showAddSiteModal = showAddSiteModal;
window.editSite = editSite;
window.deleteSite = deleteSite;
window.closeSiteModal = closeSiteModal;
window.saveSite = saveSite;

})(); // IIFE 종료