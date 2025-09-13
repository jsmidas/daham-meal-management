// 식단가 관리 모듈
(function() {
'use strict';

// 식단가 관련 변수
let businessLocations = [];
let mealPlans = [];

// 사업장 목록 로드 (식단가 관리용)
async function loadBusinessLocationsForMealPricing() {
    try {
        console.log('사업장 목록 로드 시작...');
        const response = await fetch('http://localhost:9000/api/admin/sites');
        const result = await response.json();
        console.log('API 응답:', result);
        
        // sites 배열에서 데이터 추출
        businessLocations = result.sites || result || [];
        console.log('로드된 사업장 수:', businessLocations.length);
        
        // businessLocationSelect (기존 UI)
        const businessLocationSelect = document.getElementById('businessLocationSelect');
        if (businessLocationSelect) {
            businessLocationSelect.innerHTML = '<option value="">사업장을 선택하세요</option>';
            businessLocations.forEach(location => {
                businessLocationSelect.innerHTML += `<option value="${location.id}">${location.name}</option>`;
            });
            console.log('businessLocationSelect 업데이트 완료');
        }
        
        // 기존 선택박스 (있다면)
        const oldSelect = document.getElementById('meal-pricing-business-location');
        if (oldSelect) {
            oldSelect.innerHTML = '<option value="">사업장을 선택하세요</option>';
            businessLocations.forEach(location => {
                oldSelect.innerHTML += `<option value="${location.id}">${location.name}</option>`;
            });
        }
        
        // 새 식단가 등록 폼 선택박스
        const newSelect = document.getElementById('meal-pricing-customer-id');
        if (newSelect) {
            newSelect.innerHTML = '<option value="">사업장을 선택하세요</option>';
            businessLocations.forEach(location => {
                newSelect.innerHTML += `<option value="${location.id}">${location.name}</option>`;
            });
        }
    } catch (error) {
        console.error('사업장 목록 로드 실패:', error);
        const businessLocationSelect = document.getElementById('businessLocationSelect');
        const oldSelect = document.getElementById('meal-pricing-business-location');
        const newSelect = document.getElementById('meal-pricing-customer-id');
        
        if (businessLocationSelect) {
            businessLocationSelect.innerHTML = '<option value="">사업장 목록을 불러올 수 없습니다</option>';
        }
        if (oldSelect) {
            oldSelect.innerHTML = '<option value="">사업장 목록을 불러올 수 없습니다</option>';
        }
        if (newSelect) {
            newSelect.innerHTML = '<option value="">사업장 목록을 불러올 수 없습니다</option>';
        }
    }
}

// 식단표 타입 옵션 업데이트
function updateMealPlanOptions() {
    const businessLocationSelect = document.getElementById('meal-pricing-business-location');
    const mealPlanSelect = document.getElementById('meal-pricing-meal-plan-type');
    
    if (!businessLocationSelect || !mealPlanSelect) return;
    
    const selectedLocationId = businessLocationSelect.value;
    
    if (selectedLocationId) {
        // 실제 구현에서는 선택된 사업장에 따라 다른 식단표 타입을 로드할 수 있음
        mealPlanSelect.innerHTML = `
            <option value="">식단표 타입을 선택하세요</option>
            <option value="breakfast">조식</option>
            <option value="lunch">중식</option>
            <option value="dinner">석식</option>
            <option value="snack">간식</option>
        `;
        mealPlanSelect.disabled = false;
    } else {
        mealPlanSelect.innerHTML = '<option value="">사업장을 먼저 선택하세요</option>';
        mealPlanSelect.disabled = true;
    }
}

// 메인 식단 계획 변경 시 처리
function onMasterMealPlanChange() {
    const businessLocationSelect = document.getElementById('meal-pricing-business-location');
    const mealPlanSelect = document.getElementById('meal-pricing-meal-plan-type');
    const resultDiv = document.getElementById('meal-plan-result');
    
    if (!businessLocationSelect || !mealPlanSelect || !resultDiv) {
        console.error('필수 요소를 찾을 수 없습니다');
        return;
    }
    
    const selectedLocationId = businessLocationSelect.value;
    const selectedMealType = mealPlanSelect.value;
    
    if (selectedLocationId && selectedMealType) {
        const locationName = businessLocationSelect.options[businessLocationSelect.selectedIndex].text;
        const mealTypeName = mealPlanSelect.options[mealPlanSelect.selectedIndex].text;
        
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `
            <div style="padding: 15px; background: #e7f3ff; border-radius: 5px; border-left: 4px solid #007bff;">
                <h4 style="margin: 0 0 10px 0; color: #007bff;">선택된 조건</h4>
                <p style="margin: 5px 0;"><strong>사업장:</strong> ${locationName}</p>
                <p style="margin: 5px 0;"><strong>식단표 타입:</strong> ${mealTypeName}</p>
                <div style="margin-top: 15px;">
                    <button onclick="loadDetailedMealPlan('${selectedLocationId}', '${selectedMealType}')" 
                            class="btn-primary" style="background: #007bff;">상세 식단 정보 조회</button>
                </div>
            </div>
        `;
    } else {
        resultDiv.style.display = 'none';
    }
}

// 상세 식단 계획 로드
async function loadDetailedMealPlan(locationId, mealType) {
    const resultDiv = document.getElementById('meal-plan-result');
    
    try {
        resultDiv.innerHTML = `
            <div style="padding: 15px; background: #fff3cd; border-radius: 5px; border-left: 4px solid #ffc107;">
                <p>식단 정보를 조회하고 있습니다...</p>
            </div>
        `;
        
        // 실제 API 호출 (현재는 예시 데이터)
        // const response = await fetch(`/api/admin/meal-plans/${locationId}/${mealType}`);
        // const result = await response.json();
        
        // 예시 데이터
        const exampleMealPlan = {
            location_name: businessLocations.find(loc => loc.id == locationId)?.name || '알 수 없음',
            meal_type: mealType,
            items: [
                { name: '밥', price: 500, category: '주식' },
                { name: '김치찌개', price: 1200, category: '국물' },
                { name: '불고기', price: 2000, category: '반찬' },
                { name: '김치', price: 300, category: '반찬' }
            ],
            total_price: 4000
        };
        
        setTimeout(() => {
            resultDiv.innerHTML = `
                <div style="padding: 15px; background: #d4edda; border-radius: 5px; border-left: 4px solid #28a745;">
                    <h4 style="margin: 0 0 15px 0; color: #28a745;">식단 정보 조회 결과</h4>
                    <div style="background: white; padding: 15px; border-radius: 5px; margin-top: 10px;">
                        <h5>${exampleMealPlan.location_name} - ${getMealTypeKorean(exampleMealPlan.meal_type)}</h5>
                        <table style="width: 100%; margin-top: 10px; border-collapse: collapse;">
                            <thead>
                                <tr style="background: #f8f9fa;">
                                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">메뉴</th>
                                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">분류</th>
                                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: right;">가격</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${exampleMealPlan.items.map(item => `
                                    <tr>
                                        <td style="border: 1px solid #dee2e6; padding: 8px;">${item.name}</td>
                                        <td style="border: 1px solid #dee2e6; padding: 8px;">${item.category}</td>
                                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: right;">${item.price.toLocaleString()}원</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                            <tfoot>
                                <tr style="background: #f8f9fa; font-weight: bold;">
                                    <td style="border: 1px solid #dee2e6; padding: 8px;" colspan="2">총 가격</td>
                                    <td style="border: 1px solid #dee2e6; padding: 8px; text-align: right;">${exampleMealPlan.total_price.toLocaleString()}원</td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </div>
            `;
        }, 1000);
        
    } catch (error) {
        console.error('식단 정보 로드 실패:', error);
        resultDiv.innerHTML = `
            <div style="padding: 15px; background: #f8d7da; border-radius: 5px; border-left: 4px solid #dc3545;">
                <p style="color: #721c24; margin: 0;">식단 정보를 불러올 수 없습니다.</p>
            </div>
        `;
    }
}

// 식단 타입 한글 변환
function getMealTypeKorean(mealType) {
    const typeMap = {
        'breakfast': '조식',
        'lunch': '중식', 
        'dinner': '석식',
        'snack': '간식'
    };
    return typeMap[mealType] || mealType;
}

// 식단가 관리 페이지 초기화
function initializeMealPricingPage() {
    console.log('식단가 관리 페이지 초기화 시작');
    
    // 사업장 목록 로드
    loadBusinessLocationsForMealPricing();
    
    // 식단가 목록 로드
    loadMealPricingList();
    
    // 오늘 날짜를 기본값으로 설정
    const dateInput = document.getElementById('meal-pricing-effective-date');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }
    
    // 기존 코드
    updateMealPlanOptions();
    
    // 사업장 변경 시 식단표 타입 옵션 업데이트
    const businessLocationSelect = document.getElementById('meal-pricing-business-location');
    if (businessLocationSelect) {
        businessLocationSelect.addEventListener('change', updateMealPlanOptions);
    }
    
    // 식단표 타입 변경 시 결과 업데이트
    const mealPlanSelect = document.getElementById('meal-pricing-meal-plan-type');
    if (mealPlanSelect) {
        mealPlanSelect.addEventListener('change', onMasterMealPlanChange);
    }
    
    console.log('식단가 관리 페이지 초기화 완료');
}

// 식단가 저장 기능 추가
async function saveMealPricing(mealPricingData) {
    try {
        const response = await fetch('http://localhost:9000/api/admin/meal-pricing', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(mealPricingData)
        });

        const result = await response.json();
        
        if (response.ok) {
            return { success: true, data: result };
        } else {
            return { success: false, message: result.detail || '식단가 저장에 실패했습니다.' };
        }
    } catch (error) {
        console.error('식단가 저장 중 오류:', error);
        return { success: false, message: '네트워크 오류가 발생했습니다.' };
    }
}

// 기존 UI용 식단가 저장 함수 (원래 saveMealPricing 함수를 오버라이드)
async function saveMealPricing() {
    console.log('🚀 기존 UI - 식단가 저장 시작');
    
    // 선택된 사업장 확인
    const businessLocationSelect = document.getElementById('businessLocationSelect');
    if (!businessLocationSelect || !businessLocationSelect.value) {
        alert('사업장을 먼저 선택해주세요.');
        return;
    }

    // 사업장 정보
    const customerId = businessLocationSelect.value;
    const customerName = businessLocationSelect.options[businessLocationSelect.selectedIndex].text;
    console.log('선택된 사업장:', customerId, customerName);

    // 현재 페이지에 있는 식단표들 확인
    const mealPlanInputs = document.querySelectorAll('[data-meal-plan-id]');
    console.log('발견된 식단표 입력 필드들:', mealPlanInputs.length);

    if (mealPlanInputs.length === 0) {
        // 식단표가 없으면 간단한 입력 폼으로 데이터 받기
        const mealType = prompt('식사 타입을 입력하세요 (breakfast/lunch/dinner/snack):', 'lunch');
        if (!mealType) return;

        const priceInput = prompt('가격을 입력하세요 (원):', '5000');
        if (!priceInput || isNaN(priceInput)) {
            alert('유효한 가격을 입력해주세요.');
            return;
        }

        const effectiveDate = prompt('적용 시작일 (YYYY-MM-DD):', new Date().toISOString().split('T')[0]);
        if (!effectiveDate) return;

        const notes = prompt('비고 (선택사항):', '');

        // 저장 데이터 준비
        const mealPricingData = {
            customer_id: parseInt(customerId),
            meal_type: mealType,
            price: parseFloat(priceInput),
            effective_date: effectiveDate,
            notes: notes || null
        };

        console.log('저장할 데이터:', mealPricingData);

        // 저장 시도
        const result = await saveMealPricingToAPI(mealPricingData);
        
        if (result.success) {
            alert(`식단가가 성공적으로 등록되었습니다!\n사업장: ${customerName}\n타입: ${getMealTypeKorean(mealType)}\n가격: ${priceInput.toLocaleString()}원`);
            loadMealPricingList();
        } else {
            alert(`저장 실패: ${result.message}`);
        }
    } else {
        // 기존 UI에서 식단표들이 있는 경우, 각각을 저장
        const effectiveDate = prompt('적용 시작일 (YYYY-MM-DD):', new Date().toISOString().split('T')[0]);
        if (!effectiveDate) return;

        let savedCount = 0;
        let failedCount = 0;

        // 각 식단표 저장
        for (const input of mealPlanInputs) {
            try {
                const mealPlanId = input.getAttribute('data-meal-plan-id');
                const priceValue = input.value;
                
                if (!priceValue || isNaN(priceValue) || parseFloat(priceValue) <= 0) {
                    console.log(`식단표 ${mealPlanId} 건너뛰기: 가격이 없거나 유효하지 않음`);
                    continue;
                }

                // 식단표 정보 찾기 (전역 변수에서)
                const mealPlan = window.currentMealPlans?.find(plan => plan.id == mealPlanId);
                if (!mealPlan) {
                    console.log(`식단표 ${mealPlanId} 정보를 찾을 수 없음`);
                    continue;
                }

                const mealPricingData = {
                    customer_id: parseInt(customerId),
                    meal_type: mealPlan.meal_time || 'lunch',
                    price: parseFloat(priceValue),
                    effective_date: effectiveDate,
                    notes: `${customerName} - ${mealPlan.name || '식단표'}`
                };

                console.log(`식단표 ${mealPlanId} 저장 시도:`, mealPricingData);
                const result = await saveMealPricingToAPI(mealPricingData);
                
                if (result.success) {
                    savedCount++;
                    console.log(`✅ 식단표 ${mealPlanId} 저장 성공`);
                } else {
                    failedCount++;
                    console.log(`❌ 식단표 ${mealPlanId} 저장 실패:`, result.message);
                }
            } catch (error) {
                failedCount++;
                console.error(`식단표 저장 중 오류:`, error);
            }
        }

        // 결과 표시
        if (savedCount > 0) {
            alert(`식단가 저장 완료!\n성공: ${savedCount}개\n실패: ${failedCount}개`);
            loadMealPricingList();
        } else {
            alert(`저장할 유효한 식단가가 없습니다.\n가격이 입력된 식단표를 확인해주세요.`);
        }
    }
}

// API 호출 함수 (기존 saveMealPricing과 구분)
async function saveMealPricingToAPI(mealPricingData) {
    try {
        const response = await fetch('http://localhost:9000/api/admin/meal-pricing', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(mealPricingData)
        });

        const result = await response.json();
        
        if (response.ok) {
            return { success: true, data: result };
        } else {
            return { success: false, message: result.detail || '식단가 저장에 실패했습니다.' };
        }
    } catch (error) {
        console.error('식단가 저장 중 오류:', error);
        return { success: false, message: '네트워크 오류가 발생했습니다.' };
    }
}

// 새로운 폼용 등록 처리 함수 (이전에 만든 것)
async function handleMealPricingSubmit() {
    // 폼 요소들 가져오기
    const customerId = document.getElementById('meal-pricing-customer-id')?.value;
    const mealType = document.getElementById('meal-pricing-meal-type')?.value;
    const price = document.getElementById('meal-pricing-price')?.value;
    const effectiveDate = document.getElementById('meal-pricing-effective-date')?.value;
    const notes = document.getElementById('meal-pricing-notes')?.value;

    // 유효성 검사
    if (!customerId) {
        alert('사업장을 선택해주세요.');
        return;
    }
    if (!mealType) {
        alert('식사 타입을 선택해주세요.');
        return;
    }
    if (!price || isNaN(price) || parseFloat(price) <= 0) {
        alert('유효한 가격을 입력해주세요.');
        return;
    }
    if (!effectiveDate) {
        alert('적용 날짜를 선택해주세요.');
        return;
    }

    // 저장 데이터 준비
    const mealPricingData = {
        customer_id: parseInt(customerId),
        meal_type: mealType,
        price: parseFloat(price),
        effective_date: effectiveDate,
        notes: notes || null
    };

    // 저장 시도
    const result = await saveMealPricingToAPI(mealPricingData);
    
    if (result.success) {
        alert('식단가가 성공적으로 등록되었습니다.');
        // 폼 초기화
        document.getElementById('meal-pricing-form')?.reset();
        // 목록 새로고침 (있다면)
        loadMealPricingList();
    } else {
        alert(`저장 실패: ${result.message}`);
    }
}

// 식단가 목록 로드
async function loadMealPricingList() {
    try {
        const response = await fetch('http://localhost:9000/api/admin/meal-pricing');
        const result = await response.json();
        
        if (response.ok && result.pricings) {
            displayMealPricingList(result.pricings);
        }
    } catch (error) {
        console.error('식단가 목록 로드 실패:', error);
    }
}

// 식단가 목록 표시
function displayMealPricingList(pricings) {
    const listContainer = document.getElementById('meal-pricing-list');
    if (!listContainer) return;

    if (pricings.length === 0) {
        listContainer.innerHTML = '<p>등록된 식단가가 없습니다.</p>';
        return;
    }

    const tableHTML = `
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>사업장</th>
                    <th>식사 타입</th>
                    <th>가격</th>
                    <th>적용일</th>
                    <th>비고</th>
                    <th>등록일</th>
                </tr>
            </thead>
            <tbody>
                ${pricings.map(pricing => `
                    <tr>
                        <td>${pricing.customer_name || pricing.customer_id}</td>
                        <td>${getMealTypeKorean(pricing.meal_type)}</td>
                        <td>${pricing.price.toLocaleString()}원</td>
                        <td>${pricing.effective_date}</td>
                        <td>${pricing.notes || '-'}</td>
                        <td>${new Date(pricing.created_at).toLocaleDateString()}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    listContainer.innerHTML = tableHTML;
}

// 전역 함수로 내보내기
window.loadBusinessLocationsForMealPricing = loadBusinessLocationsForMealPricing;
window.updateMealPlanOptions = updateMealPlanOptions;
window.onMasterMealPlanChange = onMasterMealPlanChange;
window.loadDetailedMealPlan = loadDetailedMealPlan;
window.getMealTypeKorean = getMealTypeKorean;
window.saveMealPricing = saveMealPricing;
window.handleMealPricingSubmit = handleMealPricingSubmit;
window.loadMealPricingList = loadMealPricingList;
window.initializeMealPricingPage = initializeMealPricingPage;

})(); // IIFE 종료

// 모듈 래퍼 추가
window.MealPricingModule = {
    async load() {
        const container = document.getElementById('meal-pricing-module');
        if (!container) return;

        container.innerHTML = `
            <div class="meal-pricing-container">
                <div class="meal-pricing-header">
                    <h2 class="meal-pricing-title">💰 식단가 관리</h2>
                    <button class="add-pricing-btn" onclick="showMealPricingForm()">
                        식단가 등록
                    </button>
                </div>

                <div class="pricing-setup-panel">
                    <div class="setup-header">
                        <span>⚙️</span>
                        <h3 class="setup-title">식단가 설정</h3>
                    </div>
                    
                    <div class="setup-form">
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">사업장 선택</label>
                                <select id="meal-pricing-business-location" class="form-select" onchange="updateMealPlanOptions()">
                                    <option value="">사업장을 선택하세요</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">식단표 타입</label>
                                <select id="meal-pricing-meal-plan-type" class="form-select" onchange="onMasterMealPlanChange()" disabled>
                                    <option value="">사업장을 먼저 선택하세요</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    
                    <div id="meal-plan-result" class="meal-plan-result"></div>
                </div>

                <div class="pricing-list">
                    <div class="pricing-list-header">
                        <h3 class="pricing-list-title">등록된 식단가</h3>
                    </div>
                    <div id="meal-pricing-list"></div>
                </div>
            </div>
        `;

        // 초기화 함수 호출
        if (window.initializeMealPricingPage) {
            window.initializeMealPricingPage();
        }

        console.log('💰 MealPricing Module 로드됨');
    }
};

// 간단한 식단가 폼 표시 함수
function showMealPricingForm() {
    const formHTML = `
        <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000;">
            <div style="background: white; padding: 20px; border-radius: 8px; width: 400px;">
                <h3>새 식단가 등록</h3>
                <form id="meal-pricing-form">
                    <div class="form-group">
                        <label>사업장</label>
                        <select id="meal-pricing-customer-id" class="form-select">
                            <option value="">사업장 선택</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>식사 타입</label>
                        <select id="meal-pricing-meal-type" class="form-select">
                            <option value="breakfast">조식</option>
                            <option value="lunch">중식</option>
                            <option value="dinner">석식</option>
                            <option value="snack">간식</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>가격 (원)</label>
                        <input type="number" id="meal-pricing-price" class="form-input" min="0" step="100">
                    </div>
                    <div class="form-group">
                        <label>적용 날짜</label>
                        <input type="date" id="meal-pricing-effective-date" class="form-input">
                    </div>
                    <div class="form-group">
                        <label>비고</label>
                        <textarea id="meal-pricing-notes" class="form-input" rows="3"></textarea>
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 15px;">
                        <button type="button" class="btn-primary" onclick="handleMealPricingSubmit()">등록</button>
                        <button type="button" class="btn-secondary" onclick="this.closest('[style*=fixed]').remove()">취소</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', formHTML);
    
    // 사업장 목록 로드
    if (window.loadBusinessLocationsForMealPricing) {
        window.loadBusinessLocationsForMealPricing();
    }
}