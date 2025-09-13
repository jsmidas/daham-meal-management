// 협력업체 매핑 - 단순 버전
(function() {
    'use strict';

    console.log('📦 Simple Mapping Module Loading...');

    async function initSimpleMapping() {
        console.log('🚀 Simple Mapping 초기화 시작');

        const container = document.getElementById('supplier-mapping-content');
        if (!container) {
            console.error('❌ supplier-mapping-content 컨테이너를 찾을 수 없음');
            return;
        }

        // 컨테이너 상태 확인
        console.log('📍 컨테이너 찾음:', container);
        console.log('📍 컨테이너 display:', window.getComputedStyle(container).display);
        console.log('📍 컨테이너 visibility:', window.getComputedStyle(container).visibility);

        // display:none인 경우 block으로 변경
        if (window.getComputedStyle(container).display === 'none') {
            console.log('⚠️ 컨테이너가 숨겨져 있음. display를 block으로 변경');
            container.style.display = 'block';
        }

        // 단순한 HTML 구조 생성
        container.innerHTML = `
            <div style="padding: 20px;">
                <h2>협력업체 매핑 관리</h2>
                <p style="color: #666;">협력업체와 사업장 간의 배송코드를 관리합니다.</p>

                <div style="background: white; padding: 20px; border-radius: 8px; margin-top: 20px;">
                    <table id="simple-mapping-table" style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 12px; text-align: left; border: 1px solid #dee2e6;">협력업체</th>
                                <th style="padding: 12px; text-align: left; border: 1px solid #dee2e6;">사업장</th>
                                <th style="padding: 12px; text-align: left; border: 1px solid #dee2e6;">배송 코드</th>
                                <th style="padding: 12px; text-align: center; border: 1px solid #dee2e6;">상태</th>
                                <th style="padding: 12px; text-align: center; border: 1px solid #dee2e6;">등록일</th>
                            </tr>
                        </thead>
                        <tbody id="simple-mapping-tbody">
                            <tr>
                                <td colspan="5" style="text-align: center; padding: 20px; border: 1px solid #dee2e6;">
                                    데이터 로딩 중...
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        // 데이터 로드
        await loadMappingData();
    }

    async function loadMappingData() {
        console.log('📊 매핑 데이터 로드 시작');

        try {
            const response = await fetch('http://127.0.0.1:8010/api/admin/customer-supplier-mappings');
            const data = await response.json();

            console.log('✅ 데이터 로드 성공:', data);

            if (data.success && data.mappings) {
                displayMappings(data.mappings);
            } else {
                console.error('❌ 데이터 형식 오류');
                displayError();
            }
        } catch (error) {
            console.error('❌ 데이터 로드 실패:', error);
            displayError();
        }
    }

    function displayMappings(mappings) {
        console.log(`📝 ${mappings.length}개 매핑 표시`);

        const tbody = document.getElementById('simple-mapping-tbody');
        if (!tbody) {
            console.error('❌ tbody를 찾을 수 없음');
            return;
        }

        if (mappings.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 20px; border: 1px solid #dee2e6;">
                        등록된 매핑이 없습니다
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = mappings.map(mapping => {
            const createdDate = mapping.created_at ?
                new Date(mapping.created_at).toLocaleDateString('ko-KR') : '-';

            return `
                <tr>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">
                        ${mapping.supplier_name || '-'}
                    </td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">
                        ${mapping.customer_name || '-'}
                    </td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">
                        <code style="background: #f5f5f5; padding: 2px 6px; border-radius: 3px;">
                            ${mapping.delivery_code || '미설정'}
                        </code>
                    </td>
                    <td style="padding: 12px; text-align: center; border: 1px solid #dee2e6;">
                        ${mapping.is_active ?
                            '<span style="color: #28a745;">✅ 활성</span>' :
                            '<span style="color: #dc3545;">❌ 비활성</span>'}
                    </td>
                    <td style="padding: 12px; text-align: center; border: 1px solid #dee2e6;">
                        ${createdDate}
                    </td>
                </tr>
            `;
        }).join('');

        console.log('✅ 매핑 표시 완료');

        // DOM 상태 확인
        const finalTbody = document.getElementById('simple-mapping-tbody');
        console.log('📍 최종 tbody 내용 길이:', finalTbody ? finalTbody.innerHTML.length : 'tbody 없음');
        console.log('📍 최종 tbody 행 수:', finalTbody ? finalTbody.getElementsByTagName('tr').length : 'tbody 없음');

        const container = document.getElementById('supplier-mapping-content');
        console.log('📍 최종 컨테이너 display:', container ? window.getComputedStyle(container).display : 'container 없음');
    }

    function displayError() {
        const tbody = document.getElementById('simple-mapping-tbody');
        if (!tbody) return;

        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 20px; border: 1px solid #dee2e6; color: #dc3545;">
                    데이터를 불러올 수 없습니다. 서버 연결을 확인해주세요.
                </td>
            </tr>
        `;
    }

    // 전역 함수로 등록
    window.initSimpleMapping = initSimpleMapping;

    console.log('✅ Simple Mapping Module 로드 완료');
})();