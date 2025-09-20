// 완전히 새로운 작동하는 사용자/사업장 관리 시스템
console.log('새로운 테스트 함수들 로드됨');

// 새로운 사용자 생성 함수 - 완전히 처음부터
async function testCreateUser() {
    const userData = {
        username: 'testuser_' + Date.now(),
        password: 'test123',
        role: 'nutritionist',
        department: '테스트부서',
        position: '테스터',
        contact_info: 'test@example.com',
        operator: false,
        semi_operator: false,
        managed_site: ''
    };
    
    console.log('[TEST] 사용자 생성 테스트 시작:', userData);
    
    try {
        const response = await fetch('/api/admin/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });
        
        console.log('[TEST] 응답 상태:', response.status);
        const result = await response.json();
        console.log('[TEST] 응답 데이터:', result);
        
        if (result.success) {
            alert('사용자 생성 성공! ID: ' + result.user_id);
            // 사용자 목록 강제 새로고침
            await testLoadUsers();
        } else {
            alert('사용자 생성 실패: ' + result.message);
        }
    } catch (error) {
        console.error('[TEST] 오류:', error);
        alert('오류 발생: ' + error.message);
    }
}

// 새로운 사용자 목록 로드 함수
async function testLoadUsers() {
    console.log('[TEST] 사용자 목록 로드 시작');
    
    try {
        const response = await fetch('/api/admin/users');
        const result = await response.json();
        
        console.log('[TEST] 사용자 목록:', result);
        
        if (result.success) {
            const userTableBody = document.getElementById('users-table-body');
            if (userTableBody) {
                userTableBody.innerHTML = result.users.map(user => `
                    <tr>
                        <td>${user.id}</td>
                        <td>${user.username}</td>
                        <td>${user.role}</td>
                        <td>${user.department || '-'}</td>
                        <td>${user.position || '-'}</td>
                        <td>${user.contact_info || '-'}</td>
                        <td><span class="${user.is_active ? 'status-active' : 'status-inactive'}">${user.is_active ? '활성' : '비활성'}</span></td>
                        <td>
                            <button class="btn-small btn-edit">수정</button>
                            <button class="btn-small btn-delete">삭제</button>
                        </td>
                    </tr>
                `).join('');
                console.log('[TEST] 사용자 테이블 업데이트 완료:', result.users.length, '명');
            }
        }
    } catch (error) {
        console.error('[TEST] 사용자 목록 로드 오류:', error);
    }
}

// 새로운 사업장 생성 함수 - 완전히 처음부터
async function testCreateSite() {
    const siteData = {
        name: '테스트사업장_' + Date.now(),
        code: 'TEST' + Date.now(),
        site_type: '일반',
        level: 1,
        sort_order: 0,
        address: '테스트 주소',
        contact_phone: '010-1234-5678',
        contact_person: '담당자',
        description: '테스트 사업장입니다',
        is_active: true,
        parent_id: null,
        portion_size: null
    };
    
    console.log('[TEST] 사업장 생성 테스트 시작:', siteData);
    
    try {
        const response = await fetch('/api/admin/sites', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(siteData)
        });
        
        console.log('[TEST] 사업장 응답 상태:', response.status);
        const result = await response.json();
        console.log('[TEST] 사업장 응답 데이터:', result);
        
        if (result.success) {
            alert('사업장 생성 성공! ID: ' + result.id);
            // 사업장 목록 강제 새로고침
            await testLoadSites();
        } else {
            alert('사업장 생성 실패: ' + JSON.stringify(result));
        }
    } catch (error) {
        console.error('[TEST] 사업장 생성 오류:', error);
        alert('오류 발생: ' + error.message);
    }
}

// 새로운 사업장 목록 로드 함수
async function testLoadSites() {
    console.log('[TEST] 사업장 목록 로드 시작');
    
    try {
        const response = await fetch('/api/admin/sites/tree');
        const result = await response.json();
        
        console.log('[TEST] 사업장 목록:', result);
        
        if (result.success) {
            const sitesContainer = document.getElementById('sites-tree');
            if (sitesContainer) {
                const sitesHtml = (result.tree || result.sites || []).map(site => `
                    <div class="tree-node" data-site-id="${site.id}">
                        <div class="tree-item">
                            <span class="site-name">${site.name}</span>
                            <span class="site-type">(${site.site_type})</span>
                            <span class="site-code">[${site.code}]</span>
                        </div>
                    </div>
                `).join('');
                
                sitesContainer.innerHTML = `
                    <div class="sites-tree">
                        ${sitesHtml}
                    </div>
                `;
                console.log('[TEST] 사업장 트리 업데이트 완료:', (result.tree || result.sites || []).length, '개');
            }
        }
    } catch (error) {
        console.error('[TEST] 사업장 목록 로드 오류:', error);
    }
}

// 전역 함수로 노출
window.testCreateUser = testCreateUser;
window.testLoadUsers = testLoadUsers;
window.testCreateSite = testCreateSite;
window.testLoadSites = testLoadSites;

console.log('테스트 함수들 준비 완료 - testCreateUser(), testCreateSite() 등 사용 가능');