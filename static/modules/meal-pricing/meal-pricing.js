// 식단가 관리 모듈
(function() {
'use strict';

// 식단가 관련 변수 - window 객체에 등록하여 전역에서 접근 가능하도록
window.businessLocations = [];
window.currentLocationId = null;
window.mealPlans = [];

// 로컬 참조용 변수
let businessLocations = window.businessLocations;
let currentLocationId = window.currentLocationId;
let mealPlans = window.mealPlans;

// MealPricingModule 객체 (다른 모듈과 일관성 유지)
window.MealPricingModule = {
    currentPage: 1,
    totalPages: 1,
    editingId: null,

    // 모듈 초기화
    async init() {
        console.log('💰 MealPricing Module 초기화');
        await this.loadMealPricingStatistics();
        await loadBusinessLocationsForMealPricing();
        this.setupEventListeners();
        return this;
    },

    // 이벤트 리스너 설정
    setupEventListeners() {
        console.log('식단가 관리 이벤트 리스너 설정');
    },

    // 식단가 통계 로드
    async loadMealPricingStatistics() {
        try {
            const apiBase = window.CONFIG?.API?.BASE_URL || 'http://127.0.0.1:8010';
            const response = await fetch(`${apiBase}/api/admin/meal-pricing`);
            const result = await response.json();

            if (result.success && result.meal_pricing) {
                const mealPlans = result.meal_pricing;

                // 통계 계산
                const totalMealPlans = mealPlans.length;
                const activeMealPlans = mealPlans.filter(p => p.is_active).length;

                // 사업장별로 그룹화
                const locationMap = new Map();
                mealPlans.forEach(plan => {
                    if (!locationMap.has(plan.location_id)) {
                        locationMap.set(plan.location_id, []);
                    }
                    locationMap.get(plan.location_id).push(plan);
                });
                const locationsWithPricing = locationMap.size;

                // 평균 판매가 및 원가율 계산
                const validPlans = mealPlans.filter(p => p.selling_price > 0);
                const averageSellingPrice = validPlans.length > 0
                    ? validPlans.reduce((sum, p) => sum + p.selling_price, 0) / validPlans.length
                    : 0;

                const averageCostRatio = validPlans.length > 0
                    ? validPlans.reduce((sum, p) => sum + (p.material_cost_guideline / p.selling_price * 100), 0) / validPlans.length
                    : 0;

                this.updateStatistics({
                    totalMealPlans,
                    activeMealPlans,
                    locationsWithPricing,
                    averageSellingPrice: Math.round(averageSellingPrice),
                    averageCostRatio
                });
            } else {
                // 데이터가 없을 때 기본값
                this.updateStatistics({
                    totalMealPlans: 0,
                    activeMealPlans: 0,
                    locationsWithPricing: 0,
                    averageSellingPrice: 0,
                    averageCostRatio: 0
                });
            }
        } catch (error) {
            console.error('식단가 통계 로드 실패:', error);
            // 에러 시 기본값 표시
            this.updateStatistics({
                totalMealPlans: '-',
                activeMealPlans: '-',
                locationsWithPricing: '-',
                averageSellingPrice: '-',
                averageCostRatio: '-'
            });
        }
    },

    // 통계 업데이트
    updateStatistics(stats) {
        const totalElement = document.getElementById('total-meal-plans-count');
        const activeTextElement = document.getElementById('active-meal-plans-text');
        const locationsElement = document.getElementById('locations-with-pricing-count');
        const avgPriceElement = document.getElementById('average-selling-price');
        const avgRatioElement = document.getElementById('average-cost-ratio');

        if (totalElement) totalElement.textContent = stats.totalMealPlans || '-';
        if (activeTextElement) activeTextElement.textContent = `활성: ${stats.activeMealPlans || 0}개`;
        if (locationsElement) locationsElement.textContent = stats.locationsWithPricing || '-';
        if (avgPriceElement) {
            if (typeof stats.averageSellingPrice === 'number') {
                avgPriceElement.textContent = '₩' + Number(stats.averageSellingPrice).toLocaleString();
            } else {
                avgPriceElement.textContent = stats.averageSellingPrice || '-';
            }
        }
        if (avgRatioElement) {
            if (typeof stats.averageCostRatio === 'number') {
                avgRatioElement.textContent = stats.averageCostRatio.toFixed(1) + '%';
            } else {
                avgRatioElement.textContent = stats.averageCostRatio || '-';
            }
        }
    },

    // 사업장별 식단표 로드 (메서드 형태로 변경)
    async loadMealPlansForLocation() {
        return await loadMealPlansForLocation();
    }
};

// 사업장 목록 로드 (식단가 관리용)
async function loadBusinessLocationsForMealPricing() {
    try {
        console.log('사업장 목록 로드 시작');
        const apiBase = window.CONFIG?.API?.BASE_URL || 'http://127.0.0.1:8010';
        const response = await fetch(`${apiBase}/api/admin/business-locations`);
        const result = await response.json();
        console.log('API 응답:', result);

        businessLocations = result.locations || result.business_locations || result || [];
        window.businessLocations = businessLocations;
        console.log('사업장 데이터:', businessLocations);

        const select = document.getElementById('businessLocationSelect');
        console.log('select 요소:', select);

        if (select) {
            select.innerHTML = '<option value="all" selected>전체</option>';
            businessLocations.forEach(location => {
                console.log('사업장 추가:', location);
                const locationName = location.site_name || location.name || '이름없음';
                select.innerHTML += `<option value="${location.id}">${locationName}</option>`;
            });
            console.log('select 옵션 최종 개수:', select.options.length);

            // 초기 로드 시 전체 선택 상태로 샘플 데이터 표시
            loadMealPlansForLocation();
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

// 선택된 사업장의 식단표 목록 로드
async function loadMealPlansForLocation() {
    const businessLocationSelect = document.getElementById('businessLocationSelect');
    const mealPlansContainer = document.getElementById('mealPlansContainer');
    const addMealPlanBtn = document.getElementById('addMealPlanBtn');
    const saveMealPricingBtn = document.getElementById('saveMealPricingBtn');

    if (!businessLocationSelect || !mealPlansContainer) {
        console.error('필수 요소를 찾을 수 없음');
        return Promise.resolve();
    }

    const selectedLocationId = businessLocationSelect.value;
    const selectedLocationName = businessLocationSelect.options[businessLocationSelect.selectedIndex]?.text;
    window.currentLocationId = selectedLocationId;
    window.currentLocationName = selectedLocationName;
    currentLocationId = selectedLocationId;

    // "전체" 선택 시 처리
    if (selectedLocationId === 'all') {
        console.log('전체 사업장 선택');

        try {
            // API에서 모든 식단가 데이터 가져오기
            const apiBase = window.CONFIG?.API?.BASE_URL || 'http://127.0.0.1:8010';
            const response = await fetch(`${apiBase}/api/admin/meal-pricing`);
            const result = await response.json();

            if (result.success && result.meal_pricing && result.meal_pricing.length > 0) {
                // 모든 사업장의 데이터 표시
                window.mealPlans = result.meal_pricing.map(mp => ({
                    id: mp.id,
                    name: mp.plan_name || mp.meal_type || '식단표',
                    meal_time: mp.meal_plan_type || '중식',
                    selling_price: mp.selling_price || 0,
                    target_material_cost: mp.material_cost_guideline || 0,
                    location_id: mp.location_id,
                    location_name: mp.location_name
                }));
            } else {
                // 데이터가 없으면 샘플 데이터 생성
                window.mealPlans = [
                    {
                        id: Date.now(),
                        name: '기본 식단표 (샘플)',
                        meal_time: '중식',
                        selling_price: 5000,
                        target_material_cost: 3500,
                        location_id: 'all',
                        location_name: '전체'
                    }
                ];
            }
        } catch (error) {
            console.error('전체 데이터 로드 실패:', error);
            // 오류 시 샘플 데이터
            window.mealPlans = [
                {
                    id: Date.now(),
                    name: '기본 식단표 (샘플)',
                    meal_time: '중식',
                    selling_price: 5000,
                    target_material_cost: 3500,
                    location_id: 'all',
                    location_name: '전체'
                }
            ];
        }

        mealPlans = window.mealPlans;
        displayMealPlans();

        if (addMealPlanBtn) addMealPlanBtn.style.display = 'inline-block';
        if (saveMealPricingBtn) saveMealPricingBtn.style.display = 'inline-block';
        return Promise.resolve();
    }

    if (!selectedLocationId) {
        mealPlansContainer.innerHTML = '<p style="color: #888; text-align: center; padding: 40px;">사업장을 선택하면 세부식단표 목록이 표시됩니다.</p>';
        if (addMealPlanBtn) addMealPlanBtn.style.display = 'none';
        if (saveMealPricingBtn) saveMealPricingBtn.style.display = 'none';
        return Promise.resolve();
    }

    console.log('선택된 사업장 ID:', selectedLocationId, 'Name:', selectedLocationName);

    try {
        // API에서 식단가 데이터 가져오기
        const apiBase = window.CONFIG?.API?.BASE_URL || 'http://127.0.0.1:8010';
        const response = await fetch(`${apiBase}/api/admin/meal-pricing`);
        const result = await response.json();

        if (result.success && result.meal_pricing) {
            // 현재 사업장에 해당하는 데이터만 필터링
            const filteredPlans = result.meal_pricing.filter(mp =>
                mp.location_name === selectedLocationName || mp.location_id === parseInt(selectedLocationId)
            );

            if (filteredPlans.length > 0) {
                window.mealPlans = filteredPlans.map(mp => ({
                    id: mp.id,
                    name: mp.plan_name || mp.meal_type || '식단표',
                    meal_time: mp.meal_plan_type || '중식',
                    selling_price: mp.selling_price || 0,
                    target_material_cost: mp.material_cost_guideline || 0,
                    location_id: mp.location_id,
                    location_name: mp.location_name
                }));
            } else {
                // 데이터가 없으면 기본값 생성
                window.mealPlans = [
                    {
                        id: Date.now(),
                        name: '기본 식단표',
                        meal_time: '중식',
                        selling_price: 5000,
                        target_material_cost: 3500,
                        location_id: selectedLocationId,
                        location_name: selectedLocationName
                    }
                ];
            }
        } else {
            // API 오류 시 기본값
            window.mealPlans = [
                {
                    id: Date.now(),
                    name: '기본 식단표',
                    meal_time: '중식',
                    selling_price: 5000,
                    target_material_cost: 3500,
                    location_id: selectedLocationId,
                    location_name: selectedLocationName
                }
            ];
        }
    } catch (error) {
        console.error('식단가 데이터 로드 실패:', error);
        // 오류 시 기본값
        window.mealPlans = [
            {
                id: Date.now(),
                name: '기본 식단표',
                meal_time: '중식',
                selling_price: 5000,
                target_material_cost: 3500,
                location_id: selectedLocationId,
                location_name: selectedLocationName
            }
        ];
    }

    mealPlans = window.mealPlans;

    displayMealPlans();

    if (addMealPlanBtn) addMealPlanBtn.style.display = 'inline-block';
    if (saveMealPricingBtn) saveMealPricingBtn.style.display = 'inline-block';

    return Promise.resolve();
}

// 식단표 목록 표시
function displayMealPlans() {
    const mealPlansContainer = document.getElementById('mealPlansContainer');
    if (!mealPlansContainer) return;

    const mealPlans = window.mealPlans;
    if (!window.mealPlans || window.mealPlans.length === 0) {
        mealPlansContainer.innerHTML = '<p style="color: #888; text-align: center; padding: 40px;">등록된 식단표가 없습니다.</p>';
        return;
    }

    // 선택된 사업장명 가져오기
    const businessLocationSelect = document.getElementById('businessLocationSelect');
    const selectedLocationName = businessLocationSelect?.options[businessLocationSelect.selectedIndex]?.text || '사업장';

    const tableHTML = `
        <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
            <thead>
                <tr style="background: #f8f9fa;">
                    <th style="border: 1px solid #dee2e6; padding: 4px 6px; text-align: center; font-weight: 600; width: 12%; font-size: 12px;">사업장명</th>
                    <th style="border: 1px solid #dee2e6; padding: 4px 6px; text-align: center; font-weight: 600; width: 10%; font-size: 12px;">운영타입</th>
                    <th style="border: 1px solid #dee2e6; padding: 4px 6px; text-align: left; font-weight: 600; width: 18%; font-size: 12px;">계획명</th>
                    <th style="border: 1px solid #dee2e6; padding: 4px 6px; text-align: right; font-weight: 600; width: 13%; font-size: 12px;">판매가 (원)</th>
                    <th style="border: 1px solid #dee2e6; padding: 4px 6px; text-align: right; font-weight: 600; width: 13%; font-size: 12px;">목표재료비 (원)</th>
                    <th style="border: 1px solid #dee2e6; padding: 4px 6px; text-align: center; font-weight: 600; width: 10%; font-size: 12px;">비율 (%)</th>
                    <th style="border: 1px solid #dee2e6; padding: 4px 6px; text-align: center; font-weight: 600; width: 15%; font-size: 12px;">관리</th>
                </tr>
            </thead>
            <tbody>
                ${mealPlans.map(plan => {
                    const costRatio = plan.selling_price > 0 ? ((plan.target_material_cost / plan.selling_price) * 100).toFixed(1) : 0;
                    const isOverLimit = parseFloat(costRatio) > 40;
                    const ratioColor = isOverLimit ? '#dc3545' : '#28a745';

                    // 전체 선택 시 각 행의 사업장명 표시
                    const displayLocationName = window.currentLocationId === 'all'
                        ? (plan.location_name || '미지정')
                        : selectedLocationName;

                    return `
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="border: 1px solid #dee2e6; padding: 3px 6px; text-align: center; font-size: 11px; font-weight: 500;">
                                ${displayLocationName}
                            </td>
                            <td style="border: 1px solid #dee2e6; padding: 3px 6px; text-align: center;">
                                <select id="meal-time-${plan.id}" onchange="updateMealPlanField(${plan.id}, 'meal_time', this.value)"
                                        style="padding: 2px 4px; border: 1px solid #ddd; border-radius: 3px; font-size: 11px; width: 100%; height: 22px;">
                                    <option value="조식" ${plan.meal_time === '조식' || plan.meal_time === 'breakfast' ? 'selected' : ''}>🌅 조식</option>
                                    <option value="중식" ${plan.meal_time === '중식' || plan.meal_time === 'lunch' ? 'selected' : ''}>☀️ 중식</option>
                                    <option value="석식" ${plan.meal_time === '석식' || plan.meal_time === 'dinner' ? 'selected' : ''}>🌙 석식</option>
                                    <option value="야식" ${plan.meal_time === '야식' || plan.meal_time === 'night' ? 'selected' : ''}>🌃 야식</option>
                                </select>
                            </td>
                            <td style="border: 1px solid #dee2e6; padding: 3px 6px; font-weight: 500;">
                                <div style="display: flex; align-items: center; gap: 4px;">
                                    <input type="text" id="plan-name-${plan.id}" value="${plan.name}"
                                           onchange="updateMealPlanField(${plan.id}, 'name', this.value)"
                                           style="border: 1px solid #e0e0e0; background: #fff; padding: 2px 4px; border-radius: 3px; font-weight: 500; width: 100%; font-size: 11px; height: 20px;"
                                           placeholder="식단표명 입력">
                                </div>
                            </td>
                            <td style="border: 1px solid #dee2e6; padding: 3px 6px; text-align: right; font-size: 11px;">
                                <input type="text" id="selling-price-${plan.id}" value="${(plan.selling_price || 0).toLocaleString()}"
                                       onchange="updateMealPlanFieldWithComma(${plan.id}, 'selling_price', this.value)"
                                       style="width: 80px; padding: 2px 4px; border: 1px solid #ddd; border-radius: 3px; text-align: right; font-size: 11px; height: 20px;"
                                       placeholder="0">
                            </td>
                            <td style="border: 1px solid #dee2e6; padding: 3px 6px; text-align: right; font-size: 11px;">
                                <input type="text" id="target-cost-${plan.id}" value="${(plan.target_material_cost || 0).toLocaleString()}"
                                       onchange="updateMealPlanFieldWithComma(${plan.id}, 'target_material_cost', this.value)"
                                       style="width: 80px; padding: 2px 4px; border: 1px solid #ddd; border-radius: 3px; text-align: right; font-size: 11px; height: 20px;"
                                       placeholder="0">
                            </td>
                            <td style="border: 1px solid #dee2e6; padding: 3px 6px; text-align: center;">
                                <span id="cost-ratio-${plan.id}" style="color: ${ratioColor}; font-weight: bold; font-size: 11px;">
                                    ${costRatio}%
                                </span>
                                ${isOverLimit ? '<span style="font-size: 9px; color: #dc3545;"> ⚠️</span>' : ''}
                            </td>
                            <td style="border: 1px solid #dee2e6; padding: 3px 6px; text-align: center;">
                                <div style="display: flex; gap: 3px; justify-content: center;">
                                    <button onclick="duplicateMealPlan(${plan.id})"
                                            style="padding: 2px 6px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 10px; height: 20px;">
                                        복사
                                    </button>
                                    <button onclick="deleteMealPlan(${plan.id})"
                                            style="padding: 2px 6px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 10px; height: 20px; ${mealPlans.length <= 1 ? 'opacity: 0.5; cursor: not-allowed;' : ''}">
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
async function updateMealPlanField(planId, field, value) {
    const plan = window.mealPlans.find(p => p.id === planId);
    if (plan) {
        if (field === 'name' || field === 'meal_time') {
            plan[field] = value;
        } else {
            plan[field] = parseInt(value) || 0;
        }
        console.log(`식단표 ${planId}의 ${field}이 ${value}로 업데이트됨`);

        // 가격이나 재료비가 변경되면 비율 업데이트
        if (field === 'selling_price' || field === 'target_material_cost') {
            updateCostRatio(planId);
        }

        // meal_time(운영타입) 변경시 즉시 저장 (임시 ID가 아닌 경우에만)
        const isTemporaryId = plan.id > 1000000000; // Date.now()는 13자리 이상
        if (field === 'meal_time' && plan.id && !isTemporaryId) {
            try {
                const apiBase = window.CONFIG?.API?.BASE_URL || 'http://127.0.0.1:8010';
                const mealData = {
                    location_id: plan.location_id,
                    location_name: plan.location_name || window.currentLocationName,
                    meal_plan_type: value, // 변경된 운영타입
                    meal_type: '급식',
                    plan_name: plan.name,
                    apply_date_start: '2025-01-01',
                    apply_date_end: '2025-12-31',
                    selling_price: plan.selling_price,
                    material_cost_guideline: plan.target_material_cost,
                    cost_ratio: plan.selling_price > 0 ?
                        ((plan.target_material_cost / plan.selling_price) * 100).toFixed(1) : 0,
                    is_active: 1
                };

                const response = await fetch(`${apiBase}/api/admin/meal-pricing/${plan.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(mealData)
                });
                const result = await response.json();

                if (result.success) {
                    console.log('운영타입 변경 저장 완료');
                } else {
                    console.error('운영타입 변경 저장 실패:', result.error);
                    alert('운영타입 변경 저장에 실패했습니다.');
                }
            } catch (error) {
                console.error('운영타입 변경 저장 중 오류:', error);
            }
        }
    }
}

// 쉼표가 있는 금액 필드 업데이트
function updateMealPlanFieldWithComma(planId, field, value) {
    // 쉼표 제거하고 숫자로 변환
    const numericValue = parseInt(value.replace(/,/g, '')) || 0;
    updateMealPlanField(planId, field, numericValue);

    // 입력 필드에 쉼표 추가된 값으로 다시 표시
    const inputElement = document.getElementById(`${field === 'selling_price' ? 'selling-price' : 'target-cost'}-${planId}`);
    if (inputElement) {
        inputElement.value = numericValue.toLocaleString();
    }
}

// 재료비 비율 업데이트
function updateCostRatio(planId) {
    const plan = window.mealPlans.find(p => p.id === planId);
    if (!plan) return;

    const costRatioElement = document.getElementById(`cost-ratio-${planId}`);
    if (!costRatioElement) return;

    const costRatio = plan.selling_price > 0 ? ((plan.target_material_cost / plan.selling_price) * 100).toFixed(1) : 0;
    const isOverLimit = parseFloat(costRatio) > 40;
    const ratioColor = isOverLimit ? '#dc3545' : '#28a745';

    costRatioElement.style.color = ratioColor;
    costRatioElement.innerHTML = `${costRatio}%`;

    // 목표 초과 경고 업데이트
    const parentCell = costRatioElement.parentElement;
    const warningDiv = parentCell.querySelector('div');

    if (isOverLimit && !warningDiv) {
        const warning = document.createElement('div');
        warning.style.cssText = 'font-size: 10px; color: #dc3545;';
        warning.innerHTML = '⚠️ 목표 초과';
        parentCell.appendChild(warning);
    } else if (!isOverLimit && warningDiv) {
        warningDiv.remove();
    }
}

// 새 식단표 추가
function addNewMealPlan() {
    // 먼저 사업장이 선택되었는지 확인
    if (!window.currentLocationId || window.currentLocationId === 'all') {
        // 사업장 선택 드롭다운 생성
        let locationOptions = '<select id="tempLocationSelect" style="padding: 5px; margin: 5px;">';
        locationOptions += '<option value="">사업장을 선택하세요</option>';

        window.businessLocations.forEach(loc => {
            locationOptions += `<option value="${loc.id}">${loc.name} - ${loc.type}</option>`;
        });
        locationOptions += '</select>';

        // 모달 형태로 사업장 선택
        const modalHtml = `
            <div id="locationSelectModal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;">
                <div style="background: white; padding: 20px; border-radius: 8px; min-width: 400px;">
                    <h3>새 식단표 추가</h3>
                    <div style="margin: 15px 0;">
                        <label>사업장 선택:</label><br>
                        ${locationOptions}
                    </div>
                    <div style="margin: 15px 0;">
                        <label>식단표 이름:</label><br>
                        <input type="text" id="tempPlanName" value="새 식단표" style="width: 100%; padding: 5px;">
                    </div>
                    <div style="margin: 15px 0;">
                        <label>끼니 구분:</label><br>
                        <select id="tempMealTime" style="width: 100%; padding: 5px;">
                            <option value="조식">조식</option>
                            <option value="중식" selected>중식</option>
                            <option value="석식">석식</option>
                            <option value="간식">간식</option>
                        </select>
                    </div>
                    <div style="text-align: right;">
                        <button onclick="document.getElementById('locationSelectModal').remove()" style="padding: 8px 16px; margin: 0 5px;">취소</button>
                        <button onclick="window.confirmNewMealPlan()" style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px;">추가</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // 확인 함수 정의
        window.confirmNewMealPlan = function() {
            const selectedLocationId = document.getElementById('tempLocationSelect').value;
            const planName = document.getElementById('tempPlanName').value;
            const mealTime = document.getElementById('tempMealTime').value;

            if (!selectedLocationId) {
                alert('사업장을 선택해주세요.');
                return;
            }

            if (!planName || planName.trim() === '') {
                alert('식단표 이름을 입력해주세요.');
                return;
            }

            // 선택한 사업장으로 변경
            const selectElement = document.getElementById('businessLocationSelect');
            selectElement.value = selectedLocationId;
            window.currentLocationId = parseInt(selectedLocationId);

            // 선택한 사업장명 가져오기
            const selectedOption = selectElement.options[selectElement.selectedIndex];
            window.currentLocationName = selectedOption ? selectedOption.text : '';

            // 모달 닫기
            document.getElementById('locationSelectModal').remove();

            // 먼저 기존 데이터 로드 후 새 식단표 추가
            loadMealPlansForLocation().then(() => {
                // 새 식단표 추가
                const newPlan = {
                    id: Date.now(), // 임시 ID
                    name: planName.trim(),
                    meal_time: mealTime,
                    selling_price: 0,
                    target_material_cost: 0,
                    location_id: window.currentLocationId,
                    location_name: window.currentLocationName
                };

                // 배열이 비어있거나 기본값만 있는 경우 초기화
                if (!window.mealPlans || window.mealPlans.length === 0 ||
                    (window.mealPlans.length === 1 && window.mealPlans[0].name === '기본 식단표')) {
                    window.mealPlans = [];
                }

                window.mealPlans.push(newPlan);
                console.log('새 식단표 추가:', newPlan);
                console.log('현재 식단표 목록:', window.mealPlans);

                // 화면 갱신
                displayMealPlans();

                // 버튼 표시
                const addMealPlanBtn = document.getElementById('addMealPlanBtn');
                const saveMealPricingBtn = document.getElementById('saveMealPricingBtn');
                if (addMealPlanBtn) addMealPlanBtn.style.display = 'inline-block';
                if (saveMealPricingBtn) saveMealPricingBtn.style.display = 'inline-block';
            });
        };

        return;
    }

    // 이미 사업장이 선택된 경우 기존 방식으로 처리
    const name = prompt('새 식단표 이름을 입력하세요:', '새 식단표');
    if (!name || name.trim() === '') return;

    const newPlan = {
        id: Date.now(), // 임시 ID
        name: name.trim(),
        meal_time: '중식', // 기본값: 중식
        selling_price: 0,
        target_material_cost: 0,
        location_id: window.currentLocationId
    };

    window.mealPlans.push(newPlan);
    displayMealPlans();

    console.log('새 식단표 추가:', newPlan);
}

// 식단표 복사
function duplicateMealPlan(planId) {
    const plan = window.mealPlans.find(p => p.id === planId);
    if (!plan) return;

    const newPlan = {
        id: Date.now(), // 임시 ID
        name: plan.name + ' (복사)',
        meal_time: plan.meal_time, // 기존 시간대 복사
        selling_price: plan.selling_price,
        target_material_cost: plan.target_material_cost,
        location_id: currentLocationId
    };

    window.mealPlans.push(newPlan);
    displayMealPlans();

    console.log('식단표 복사:', newPlan);
}


// 식단표 삭제
async function deleteMealPlan(planId) {
    if (window.mealPlans.length <= 1) {
        alert('최소 1개의 식단표는 유지해야 합니다.');
        return;
    }

    if (!confirm('이 식단표를 삭제하시겠습니까?')) return;

    try {
        // 실제 ID인 경우 DB에서 삭제 (임시 ID가 아닌 경우)
        const isTemporaryId = planId > 1000000000; // Date.now()는 13자리 이상
        if (planId && !isTemporaryId) {
            const apiBase = window.CONFIG?.API?.BASE_URL || 'http://127.0.0.1:8010';
            const response = await fetch(`${apiBase}/api/admin/meal-pricing/${planId}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            if (!result.success) {
                console.error('삭제 실패:', result.error);
                alert('삭제 중 오류가 발생했습니다.');
                return;
            }
        }

        // 로컬 배열에서 제거
        window.mealPlans = window.mealPlans.filter(p => p.id !== planId);
        displayMealPlans();

        console.log('식단표 삭제 완료, 남은 식단표:', window.mealPlans);
    } catch (error) {
        console.error('식단표 삭제 실패:', error);
        alert('삭제 중 오류가 발생했습니다.');
    }
}

// 식단가 정보 저장
async function saveMealPricing() {
    if (!window.currentLocationId) {
        alert('사업장을 먼저 선택해주세요.');
        return;
    }

    if (!window.mealPlans || window.mealPlans.length === 0) {
        alert('저장할 식단표가 없습니다.');
        return;
    }

    try {
        const apiBase = window.CONFIG?.API?.BASE_URL || 'http://127.0.0.1:8010';

        // 각 식단표를 개별적으로 저장/업데이트
        for (const plan of window.mealPlans) {
            // 전체 선택 시에는 저장하지 않음 (샘플 데이터이므로)
            if (window.currentLocationId === 'all') {
                console.log('전체 선택 상태이므로 저장하지 않음');
                continue;
            }

            const mealData = {
                location_id: parseInt(window.currentLocationId),
                location_name: window.currentLocationName || plan.location_name,
                meal_plan_type: plan.meal_time, // 조식/중식/석식/야식
                meal_type: '급식', // 기본값
                plan_name: plan.name,
                apply_date_start: '2025-01-01',
                apply_date_end: '2025-12-31',
                selling_price: plan.selling_price,
                material_cost_guideline: plan.target_material_cost,
                cost_ratio: plan.selling_price > 0 ?
                    ((plan.target_material_cost / plan.selling_price) * 100).toFixed(1) : 0,
                is_active: 1
            };

            // Date.now()로 생성된 임시 ID는 매우 큰 숫자이므로 이를 체크
            const isTemporaryId = plan.id > 1000000000; // Date.now()는 13자리 이상

            if (plan.id && !isTemporaryId) {
                // 기존 데이터 업데이트 (실제 DB ID를 가진 경우)
                console.log(`기존 식단표 업데이트: ID=${plan.id}`);
                const response = await fetch(`${apiBase}/api/admin/meal-pricing/${plan.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(mealData)
                });
                const result = await response.json();
                if (!result.success) {
                    console.error('업데이트 실패:', result.error);
                }
            } else {
                // 새 데이터 추가 (임시 ID를 가진 경우)
                console.log(`새 식단표 추가: 임시ID=${plan.id}`);
                const response = await fetch(`${apiBase}/api/admin/meal-pricing`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(mealData)
                });
                const result = await response.json();
                if (result.success && result.id) {
                    plan.id = result.id; // 새로 생성된 ID 할당
                    console.log(`새 식단표 저장 완료: 새ID=${result.id}`);
                } else {
                    console.error('추가 실패:', result.error);
                }
            }
        }

        alert('식단가 정보가 저장되었습니다.');

        // 저장 후 다시 로드하여 최신 데이터 표시
        await loadMealPlansForLocation();

    } catch (error) {
        console.error('식단가 저장 실패:', error);
        alert('저장 중 오류가 발생했습니다.');
    }
}

// 식단가 관리 페이지 초기화
function initializeMealPricingPage() {
    console.log('식단가 관리 페이지 초기화 시작');
    loadBusinessLocationsForMealPricing();
}

// 전역 함수로 내보내기
window.loadBusinessLocationsForMealPricing = loadBusinessLocationsForMealPricing;
window.loadMealPlansForLocation = loadMealPlansForLocation;
window.displayMealPlans = displayMealPlans;
window.updateMealPlanField = updateMealPlanField;
window.updateMealPlanFieldWithComma = updateMealPlanFieldWithComma;
window.updateCostRatio = updateCostRatio;
window.addNewMealPlan = addNewMealPlan;
window.duplicateMealPlan = duplicateMealPlan;
window.deleteMealPlan = deleteMealPlan;
window.saveMealPricing = saveMealPricing;
window.initializeMealPricingPage = initializeMealPricingPage;

// 호환성을 위한 별칭 추가
window.MealPricingManagement = window.MealPricingModule;

})(); // IIFE 종료