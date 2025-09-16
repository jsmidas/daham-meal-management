// 협력업체 매핑 관리 모듈
(function() {
'use strict';

// 매핑 관련 변수
let currentMappingPage = 1;
let totalMappingPages = 1;
let currentEditMappingId = null;
let suppliersCache = [];
let customersCache = [];

// 매핑 목록 로드
async function loadMappingData() {
    try {
        const response = await fetch('/api/admin/customer-supplier-mappings');
        const data = await response.json();
        
        if (data.success) {
            const mappings = data.mappings || [];
            // 고객과 공급업체 데이터를 별도로 로드
            await Promise.all([
                loadCustomersAndSuppliers()
            ]);
            displayMappings(mappings, customersCache || [], suppliersCache || []);
            // 간단한 페이지네이션 (클라이언트 사이드)
            updateMappingPagination(1, Math.ceil(mappings.length / 20));
        }
    } catch (error) {
        console.error('매핑 목록 로드 실패:', error);
        const tbody = document.getElementById('mappings-table-body');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="5">매핑 목록을 불러올 수 없습니다.</td></tr>';
        }
    }
}

// 매핑 목록 표시 (5개 컬럼으로 단순화)
function displayMappings(mappings, customers, suppliers) {
    const tbody = document.getElementById('mappings-table-body');
    if (!tbody) return;
    
    if (!mappings || mappings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">등록된 매핑이 없습니다.</td></tr>';
        return;
    }
    
    tbody.innerHTML = mappings.map(mapping => {
        const customer = customers.find(c => c.id === mapping.customer_id);
        const supplier = suppliers.find(s => s.id === mapping.supplier_id);
        
        return `
            <tr style="border-bottom: 1px solid #eee;">
                <td style="font-weight: 500;">${customer ? customer.name : '⚠️ 삭제된 사업장'}</td>
                <td>${supplier ? supplier.name : '⚠️ 삭제된 업체'}</td>
                <td>
                    <code style="background: #e3f2fd; padding: 2px 6px; border-radius: 3px; margin-right: 4px;">협력: ${mapping.supplier_code || '미설정'}</code>
                    <code style="background: #fff3cd; padding: 2px 6px; border-radius: 3px;">배송: ${mapping.delivery_code || '미설정'}</code>
                </td>
                <td>
                    <span style="color: ${mapping.is_active ? '#28a745' : '#dc3545'}; font-weight: bold;">
                        ${mapping.is_active ? '🟢 거래중' : '🔴 중단'}
                    </span>
                </td>
                <td>
                    <div style="display: flex; gap: 5px; flex-wrap: wrap;">
                        <button class="btn-small btn-edit" onclick="editMapping(${mapping.id})" style="background: #007bff;">수정</button>
                        <button class="btn-small" onclick="toggleMappingStatus(${mapping.id}, ${!mapping.is_active})" 
                                style="background: ${mapping.is_active ? '#dc3545' : '#28a745'};">
                            ${mapping.is_active ? '중단' : '재개'}
                        </button>
                        <button class="btn-small btn-delete" onclick="deleteMapping(${mapping.id})" style="background: #dc3545;">삭제</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// 매핑 페이지네이션 업데이트
function updateMappingPagination(currentPage, totalPages) {
    currentMappingPage = currentPage;
    totalMappingPages = totalPages;
    const pageInfo = document.getElementById('mapping-page-info');
    if (pageInfo) {
        pageInfo.textContent = `${currentPage} / ${totalPages}`;
    }
}

// 매핑 페이지 변경
function changeMappingPage(direction) {
    const newPage = currentMappingPage + direction;
    if (newPage >= 1 && newPage <= totalMappingPages) {
        currentMappingPage = newPage;
        loadMappingData();
    }
}

// 매핑 검색
function searchMappings() {
    currentMappingPage = 1;
    loadMappingData();
}

// 매핑 추가 모달 표시
async function showAddMappingModal() {
    currentEditMappingId = null;
    document.getElementById('mapping-modal-title').textContent = '새 협력업체 매핑 추가';
    
    // 폼 초기화
    document.getElementById('mapping-form').reset();
    
    // 고객 및 공급업체 목록 로드
    await loadCustomersAndSuppliers();
    
    document.getElementById('mapping-modal').classList.remove('hidden');
}

// 고객 및 공급업체 목록 로드
async function loadCustomersAndSuppliers() {
    try {
        const [customersResponse, suppliersResponse] = await Promise.all([
            fetch('/api/admin/sites/tree'),
            fetch('/api/admin/suppliers/enhanced')
        ]);
        
        const customersData = await customersResponse.json();
        const suppliersData = await suppliersResponse.json();
        
        customersCache = customersData.sites || [];
        suppliersCache = suppliersData.suppliers || [];
        
        // 고객 select 박스 업데이트
        const customerSelect = document.getElementById('mapping-customer');
        if (customerSelect) {
            customerSelect.innerHTML = '<option value="">사업장을 선택하세요</option>';
            customersCache.forEach(customer => {
                customerSelect.innerHTML += `<option value="${customer.id}">${customer.name}</option>`;
            });
            console.log('고객 select 박스 업데이트 완료, 옵션 수:', customerSelect.options.length);
        } else {
            console.error('mapping-customer select 요소를 찾을 수 없음');
        }
        
        // 공급업체 select 박스 업데이트
        const supplierSelect = document.getElementById('mapping-supplier-id');
        if (supplierSelect) {
            supplierSelect.innerHTML = '<option value="">공급업체를 선택하세요</option>';
            suppliersCache.forEach(supplier => {
                supplierSelect.innerHTML += `<option value="${supplier.id}">${supplier.name}</option>`;
            });
        }
        
    } catch (error) {
        console.error('고객/공급업체 목록 로드 실패:', error);
    }
}

// 매핑 수정
async function editMapping(mappingId) {
    try {
        console.log('매핑 수정 요청:', mappingId);
        const response = await fetch(`/api/admin/customer-supplier-mappings/${mappingId}`);
        const result = await response.json();
        
        console.log('매핑 API 응답:', result);
        
        // result가 배열인 경우 첫 번째 요소 사용
        const mapping = Array.isArray(result) ? result[0] : (result.mapping || result);
        
        if (mapping) {
            console.log('처리할 매핑 데이터:', mapping);
            currentEditMappingId = mappingId;
            document.getElementById('mapping-modal-title').textContent = '협력업체 매핑 수정';
            
            // 고객 및 공급업체 목록 먼저 로드
            await loadCustomersAndSuppliers();
            console.log('고객/공급업체 목록 로드 완료');
            
            // 모달 표시
            document.getElementById('mapping-modal').classList.remove('hidden');
            
            // DOM이 준비된 후 값 설정 (약간의 지연)
            setTimeout(() => {
                // 사업장 선택
                const customerSelect = document.getElementById('mapping-customer');
                if (customerSelect) {
                    console.log('사업장 선택 설정 시도:', mapping.customer_id);
                    customerSelect.value = mapping.customer_id || '';
                    console.log('사업장 선택 결과:', customerSelect.value);
                } else {
                    console.error('mapping-customer 요소를 찾을 수 없음');
                }
                
                // 특이사항
                const notesElement = document.getElementById('mapping-notes');
                if (notesElement) {
                    notesElement.value = mapping.notes || '';
                    console.log('특이사항 설정:', notesElement.value);
                }
                
                // 기존 supplier rows 초기화 후 데이터로 행 추가
                const container = document.getElementById('supplier-rows-container');
                if (container) {
                    container.innerHTML = '';
                    console.log('공급업체 행 추가 시도:', {
                        supplier_id: mapping.supplier_id,
                        delivery_code: mapping.delivery_code
                    });
                    
                    // 매핑 데이터로 supplier row 추가
                    addSupplierRow({
                        supplier_id: mapping.supplier_id,
                        delivery_code: mapping.delivery_code
                    });
                } else {
                    console.error('supplier-rows-container 요소를 찾을 수 없음');
                }
            }, 100);
            
        } else {
            console.error('매핑 데이터가 없음:', result);
            alert('매핑 데이터를 찾을 수 없습니다.');
        }
    } catch (error) {
        console.error('매핑 정보 로드 실패:', error);
        alert('매핑 정보를 불러올 수 없습니다.');
    }
}

// 매핑 저장
async function saveMapping() {
    const mappingData = {
        customer_id: parseInt(document.getElementById('mapping-customer-id').value),
        supplier_id: parseInt(document.getElementById('mapping-supplier-id').value),
        delivery_code: document.getElementById('mapping-delivery-code').value,
        is_active: document.getElementById('mapping-is-active').checked
    };
    
    if (!mappingData.customer_id || !mappingData.supplier_id) {
        alert('사업장과 공급업체를 모두 선택해주세요.');
        return;
    }

    try {
        const url = currentEditMappingId ? 
            `/api/admin/customer-supplier-mappings/${currentEditMappingId}` : 
            '/api/admin/customer-supplier-mappings/create';
        
        const method = currentEditMappingId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(mappingData)
        });

        const result = await response.json();
        
        if (result.success) {
            alert(currentEditMappingId ? '매핑이 수정되었습니다.' : '새 매핑이 추가되었습니다.');
            closeMappingModal();
            loadMappingData();
        } else {
            alert('저장에 실패했습니다: ' + (result.message || '알 수 없는 오류'));
        }
    } catch (error) {
        console.error('매핑 저장 오류:', error);
        alert('저장 중 오류가 발생했습니다.');
    }
}

// 매핑 상태 토글
async function toggleMappingStatus(mappingId, newStatus) {
    const statusText = newStatus ? '재개' : '중단';
    if (!confirm(`이 거래를 ${statusText}하시겠습니까?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/customer-supplier-mappings/${mappingId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: newStatus })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`거래가 ${statusText}되었습니다.`);
            loadMappingData();
        } else {
            alert('상태 변경에 실패했습니다.');
        }
    } catch (error) {
        console.error('상태 변경 오류:', error);
        alert('상태 변경 중 오류가 발생했습니다.');
    }
}

// 매핑 삭제
async function deleteMapping(mappingId) {
    if (!confirm('이 매핑을 삭제하시겠습니까? 이 작업은 취소할 수 없습니다.')) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/customer-supplier-mappings/${mappingId}`, {
            method: 'DELETE'
        });

        const result = await response.json();
        
        if (result.success) {
            alert('매핑이 삭제되었습니다.');
            loadMappingData();
        } else {
            alert(result.message || '삭제에 실패했습니다.');
        }
    } catch (error) {
        console.error('매핑 삭제 오류:', error);
        alert('삭제 중 오류가 발생했습니다.');
    }
}

// 협력업체 행 추가 함수 (매핑 모달용)
function addSupplierRow(supplierData = null) {
    const container = document.getElementById('supplier-rows-container');
    if (!container) return;
    
    const rowDiv = document.createElement('div');
    rowDiv.className = 'supplier-row';
    rowDiv.style.cssText = 'display: flex; gap: 10px; align-items: center; margin-bottom: 10px; padding: 10px; border: 1px solid #eee; border-radius: 5px;';
    
    rowDiv.innerHTML = `
        <div style="flex: 1;">
            <label>협력업체</label>
            <select class="supplier-select" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" required>
                <option value="">협력업체를 선택하세요</option>
                ${suppliersCache.map(supplier => {
                    const selected = supplierData && supplier.id === supplierData.supplier_id ? 'selected' : '';
                    return `<option value="${supplier.id}" ${selected}>${supplier.name}</option>`;
                }).join('')}
            </select>
        </div>
        <div style="flex: 1;">
            <label>배송코드</label>
            <input type="text" class="delivery-code-input" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" 
                   value="${supplierData ? (supplierData.delivery_code || '') : ''}" 
                   placeholder="배송코드를 입력하세요" maxlength="20" required>
        </div>
        <div style="padding-top: 20px;">
            <button type="button" onclick="removeSupplierRow(this)" style="background: #dc3545; color: white; border: none; padding: 8px; border-radius: 4px; cursor: pointer;">
                삭제
            </button>
        </div>
    `;
    
    container.appendChild(rowDiv);
}

// 협력업체 행 제거 함수
function removeSupplierRow(button) {
    const row = button.closest('.supplier-row');
    if (row) {
        row.remove();
    }
}

// 매핑 모달 닫기
function closeMappingModal() {
    document.getElementById('mapping-modal').classList.add('hidden');
    currentEditMappingId = null;
}

// 전역 함수로 내보내기
window.loadMappingData = loadMappingData;
window.displayMappings = displayMappings;
window.updateMappingPagination = updateMappingPagination;
window.changeMappingPage = changeMappingPage;
window.searchMappings = searchMappings;
window.showAddMappingModal = showAddMappingModal;
window.loadCustomersAndSuppliers = loadCustomersAndSuppliers;
window.editMapping = editMapping;
window.saveMapping = saveMapping;
window.toggleMappingStatus = toggleMappingStatus;
window.deleteMapping = deleteMapping;
window.addSupplierRow = addSupplierRow;
window.removeSupplierRow = removeSupplierRow;
window.closeMappingModal = closeMappingModal;

})(); // IIFE 종료