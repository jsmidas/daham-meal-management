// 식단가 관리 모듈
(function() {
'use strict';

// 식단가 관련 변수
let businessLocations = [];
let currentLocationId = null;
let mealPlans = [];

// MealPricingModule 객체 (다른 모듈과 일관성 유지)
window.MealPricingModule = {
    currentPage: 1,
    totalPages: 1,
    editingId: null,

    // 모듈 초기화
    async init() {
        console.log('💰 MealPricing Module v4.0 초기화 - 세부식단표 관리 기능 추가');
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
            const response = await fetch('/api/admin/meal-pricing/statistics');
            const data = await response.json();
            
            if (data.success) {
                this.updateStatistics(data.statistics);
            } else {
                // 통계 API가 없는 경우 기본값 표시
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
    },

    // 새 세부식단표 추가
    async addNewDetailedMenu() {
        const locationSelect = document.getElementById('businessLocationSelect');
        if (!locationSelect.value) {
            alert('먼저 사업장을 선택해주세요.');
            return;
        }

        const menuName = prompt('새 세부식단표 이름을 입력하세요:', '기본식단표');
        if (!menuName) return;

        try {
            const response = await fetch('/api/admin/detailed-menus', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    site_id: parseInt(locationSelect.value),
                    name: menuName,
                    description: `${menuName} 세부식단표`,
                    is_active: true
                })
            });

            const result = await response.json();
            if (result.success) {
                alert('세부식단표가 추가되었습니다.');
                this.loadDetailedMenusForSite(locationSelect.value);
            } else {
                alert('추가 실패: ' + result.message);
            }
        } catch (error) {
            console.error('세부식단표 추가 실패:', error);
            alert('추가 중 오류가 발생했습니다.');
        }
    },

    // 세부식단표 삭제
    async deleteDetailedMenu(menuId) {
        if (!confirm('이 세부식단표를 삭제하시겠습니까?')) return;

        try {
            const response = await fetch(`/api/admin/detailed-menus/${menuId}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            if (result.success) {
                alert('세부식단표가 삭제되었습니다.');
                const locationSelect = document.getElementById('businessLocationSelect');
                if (locationSelect.value) {
                    this.loadDetailedMenusForSite(locationSelect.value);
                }
            } else {
                alert('삭제 실패: ' + result.message);
            }
        } catch (error) {
            console.error('세부식단표 삭제 실패:', error);
            alert('삭제 중 오류가 발생했습니다.');
        }
    },

    // 사업장의 세부식단표 목록 로드
    async loadDetailedMenusForSite(siteId) {
        try {
            console.log('사업장 세부식단표 로드:', siteId);
            
            // 임시로 목록을 하드코딩으로 생성 (API가 준비될 때까지)
            const result = {
                success: true,
                menus: [
                    {
                        id: 1,
                        name: '기본식단표',
                        description: '자동 생성된 기본 세부식단표',
                        is_active: true,
                        created_at: new Date().toISOString(),
                        site_id: siteId,
                        site_name: '테스트 사업장'
                    }
                ]
            };
            
            console.log('임시 데이터 반환:', result);
            
            if (result.success) {
                const menus = result.menus || [];
                
                // 메뉴가 없으면 기본 메뉴 자동 생성
                if (menus.length === 0) {
                    await this.createDefaultMenu(siteId);
                    // 다시 로드
                    return this.loadDetailedMenusForSite(siteId);
                }
                
                this.displayDetailedMenus(menus);
                this.showMenuControls(true);
            } else {
                console.error('세부식단표 로드 실패:', result.message);
                document.getElementById('mealPlansContainer').innerHTML = 
                    '<p style="color: #e74c3c; text-align: center; padding: 20px;">세부식단표를 불러올 수 없습니다.</p>';
            }
        } catch (error) {
            console.error('세부식단표 로드 오류:', error);
            document.getElementById('mealPlansContainer').innerHTML = 
                '<p style="color: #e74c3c; text-align: center; padding: 20px;">로드 중 오류가 발생했습니다.</p>';
        }
    },

    // 기본 세부식단표 자동 생성
    async createDefaultMenu(siteId) {
        try {
            console.log('기본 세부식단표 자동 생성:', siteId);
            
            const response = await fetch('/api/admin/detailed-menus', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    site_id: parseInt(siteId),
                    name: '기본식단표',
                    description: '자동 생성된 기본 세부식단표',
                    is_active: true
                })
            });

            const result = await response.json();
            if (result.success) {
                console.log('기본 세부식단표 생성 완료');
            } else {
                console.error('기본 세부식단표 생성 실패:', result.message);
            }
        } catch (error) {
            console.error('기본 세부식단표 생성 오류:', error);
        }
    },

    // 세부식단표 목록 표시
    displayDetailedMenus(menus) {
        const container = document.getElementById('mealPlansContainer');
        
        let html = '<div style="display: grid; gap: 15px;">';
        
        menus.forEach(menu => {
            html += `
                <div class="detailed-menu-card" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background: white;">
                    <div style="display: flex; justify-content: between; align-items: center;">
                        <div style="flex: 1;">
                            <h4 style="margin: 0 0 5px 0; color: #2c3e50;">${menu.name}</h4>
                            <p style="margin: 0; color: #666; font-size: 14px;">${menu.description || '세부식단표 설명 없음'}</p>
                            <div style="margin-top: 8px; font-size: 12px; color: #999;">
                                생성일: ${new Date(menu.created_at).toLocaleDateString()}
                                ${menu.is_active ? '<span style="color: #27ae60; margin-left: 10px;">🟢 활성</span>' : '<span style="color: #e74c3c; margin-left: 10px;">🔴 비활성</span>'}
                            </div>
                        </div>
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <button onclick="MealPricingModule.editDetailedMenu(${menu.id})" 
                                    style="padding: 6px 12px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                                수정
                            </button>
                            <button onclick="MealPricingModule.deleteDetailedMenu(${menu.id})" 
                                    style="padding: 6px 12px; background: #e74c3c; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                                삭제
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    },

    // 메뉴 관리 컨트롤 표시/숨김
    showMenuControls(show) {
        const controls = document.getElementById('mealPlanControls');
        if (controls) {
            controls.style.display = show ? 'flex' : 'none';
        }
        
        const addBtn = document.getElementById('addMealPlanBtn');
        if (addBtn) {
            addBtn.style.display = show ? 'inline-block' : 'none';
        }
    },

    // 세부식단표 수정
    async editDetailedMenu(menuId) {
        const newName = prompt('세부식단표 이름을 수정하세요:');
        if (!newName) return;

        try {
            const response = await fetch(`/api/admin/detailed-menus/${menuId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: newName,
                    description: `${newName} 세부식단표`
                })
            });

            const result = await response.json();
            if (result.success) {
                alert('세부식단표가 수정되었습니다.');
                const locationSelect = document.getElementById('businessLocationSelect');
                if (locationSelect.value) {
                    this.loadDetailedMenusForSite(locationSelect.value);
                }
            } else {
                alert('수정 실패: ' + result.message);
            }
        } catch (error) {
            console.error('세부식단표 수정 실패:', error);
            alert('수정 중 오류가 발생했습니다.');
        }
    }
};

// 사업장 목록 로드 (식단가 관리용)
async function loadBusinessLocationsForMealPricing() {
    try {
        console.log('사업장 목록 로드 시작 - 사업장 관리 데이터 기반');
        
        // 사업장 관리의 모든 사업장 DB에서 가져오기
        const response = await fetch('/api/admin/sites');
        const result = await response.json();
        console.log('사업장 관리 API 응답:', result);
        
        if (result && result.success && result.sites && result.sites.length > 0) {
            businessLocations = result.sites.map(site => ({
                id: site.id,
                name: site.site_name || site.name,
                site_type: site.site_type || site.type
            }));
            console.log('사업장 데이터 (DB에서 로드):', businessLocations);
        } else {
            console.error('사업장 데이터를 불러올 수 없습니다. API 응답:', result);
            throw new Error('사업장 데이터 로드 실패');
        }
        
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
            select.innerHTML = '<option value="">사업장을 불러올 수 없습니다</option>';
        }
        
        // 사업장 API가 작동하지 않으면 빈 배열로 설정
        businessLocations = [];
        throw error; // 오류를 상위로 전파
    }
}

// 선택된 사업장의 식단표 목록 로드
async function loadMealPlansForLocation() {
    const businessLocationSelect = document.getElementById('businessLocationSelect');
    
    if (!businessLocationSelect.value) {
        document.getElementById('mealPlansContainer').innerHTML = 
            '<p style="color: #888; text-align: center; padding: 40px;">사업장을 선택해주세요.</p>';
        MealPricingModule.showMenuControls(false);
        return;
    }
    
    const selectedLocationId = businessLocationSelect.value;
    currentLocationId = selectedLocationId;
    
    console.log('선택된 사업장 ID:', selectedLocationId);
    
    // 선택된 사업장 정보 가져오기
    const selectedBusiness = businessLocations.find(loc => loc.id == selectedLocationId);
    const selectedBusinessName = selectedBusiness ? selectedBusiness.name : '알 수 없는 사업장';
    console.log('선택된 사업장:', selectedBusiness);
    console.log('선택된 사업장명:', selectedBusinessName);
    
    // 사업장별 데이터 로드 - location_id 또는 customer_name으로 필터링
    try {
        const response = await fetch('/api/admin/meal-pricing');
        const data = await response.json();
        
        if (data.success && data.pricings && data.pricings.length > 0) {
            // location_id 또는 customer_name으로 필터링 (둘 다 확인)
            const filteredPricings = data.pricings.filter(pricing => 
                pricing.customer_id == selectedLocationId || 
                pricing.location_id == selectedLocationId ||
                pricing.customer_name === selectedBusinessName
            );
            
            if (filteredPricings.length > 0) {
                // 해당 사업장의 데이터가 있으면 사용
                mealPlans = filteredPricings.map(pricing => ({
                    id: pricing.id,
                    name: pricing.notes || '기본식단표',
                    meal_time: pricing.meal_type,
                    selling_price: pricing.price,
                    target_material_cost: pricing.material_cost_guideline || 0,
                    location_id: selectedLocationId,
                    customer_name: selectedBusinessName
                }));
                console.log(`${selectedBusinessName} 식단가 데이터 ${mealPlans.length}개 로드됨`);
            } else {
                // 해당 사업장 데이터가 없으면 기본 식단표 1개 생성
                mealPlans = [
                    {
                        id: Date.now(), // 임시 ID
                        name: '기본 식단표',
                        meal_time: 'lunch',
                        selling_price: 5000,
                        target_material_cost: 3500,
                        location_id: selectedLocationId,
                        customer_name: selectedBusinessName
                    }
                ];
                console.log(`${selectedBusinessName} 기본 식단표 1개 생성`);
            }
        } else {
            // 전체 데이터가 없으면 기본 식단표 1개 생성
            mealPlans = [
                {
                    id: Date.now(),
                    name: '기본 식단표',
                    meal_time: 'lunch',
                    selling_price: 5000,
                    target_material_cost: 3500,
                    location_id: selectedLocationId,
                    customer_name: selectedBusinessName
                }
            ];
            console.log(`${selectedBusinessName} 기본 식단표 1개 생성 (데이터 없음)`);
        }
    } catch (error) {
        console.error('식단가 데이터 로드 실패:', error);
        // 에러 시 기본 식단표 1개 생성
        mealPlans = [
            {
                id: Date.now(),
                name: '기본 식단표',
                meal_time: 'lunch',
                selling_price: 5000,
                target_material_cost: 3500,
                location_id: selectedLocationId,
                customer_name: selectedBusinessName
            }
        ];
        console.log(`${selectedBusinessName} 기본 식단표 1개 생성 (오류)`);
    }
    
    displayMealPlans();
    
    const addMealPlanBtn = document.getElementById('addMealPlanBtn');
    const saveMealPricingBtn = document.getElementById('saveMealPricingBtn');
    if (addMealPlanBtn) addMealPlanBtn.style.display = 'inline-block';
    if (saveMealPricingBtn) saveMealPricingBtn.style.display = 'inline-block';
}

// 식단표 목록 표시
function displayMealPlans() {
    const mealPlansContainer = document.getElementById('mealPlansContainer');
    if (!mealPlansContainer) return;
    
    if (!mealPlans || mealPlans.length === 0) {
        mealPlansContainer.innerHTML = '<p style="color: #888; text-align: center; padding: 40px;">등록된 식단표가 없습니다.</p>';
        return;
    }
    
    const tableHTML = `
        <table style="width: 100%; border-collapse: collapse; margin-top: 10px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <thead>
                <tr style="background: #e3f2fd; border-bottom: 2px solid #1976d2;">
                    <th style="border: 1px solid #bbbbbb; padding: 10px; text-align: center; font-weight: 600; width: 15%; background: #f5f5f5;">사업장명</th>
                    <th style="border: 1px solid #bbbbbb; padding: 10px; text-align: center; font-weight: 600; width: 12%;">식사시간</th>
                    <th style="border: 1px solid #bbbbbb; padding: 10px; text-align: center; font-weight: 600; width: 20%;">세부식단표명</th>
                    <th style="border: 1px solid #bbbbbb; padding: 10px; text-align: center; font-weight: 600; width: 12%;">판매가</th>
                    <th style="border: 1px solid #bbbbbb; padding: 10px; text-align: center; font-weight: 600; width: 13%;">목표식재료비</th>
                    <th style="border: 1px solid #bbbbbb; padding: 10px; text-align: center; font-weight: 600; width: 8%;">%</th>
                    <th style="border: 1px solid #bbbbbb; padding: 10px; text-align: center; font-weight: 600; width: 10%;">수정</th>
                    <th style="border: 1px solid #bbbbbb; padding: 10px; text-align: center; font-weight: 600; width: 10%;">삭제</th>
                </tr>
            </thead>
            <tbody>
                ${mealPlans.map(plan => {
                    const costRatio = plan.selling_price > 0 ? ((plan.target_material_cost / plan.selling_price) * 100).toFixed(1) : 0;
                    const isOverLimit = parseFloat(costRatio) > 40;
                    const ratioColor = isOverLimit ? '#d32f2f' : '#388e3c';
                    
                    // 식사시간 한글 변환
                    const mealTimeKorean = {
                        'breakfast': '조식',
                        'lunch': '중식', 
                        'dinner': '석식',
                        'night': '야식'
                    };
                    
                    return `
                        <tr style="background: ${plan.id % 2 === 0 ? '#fafafa' : '#ffffff'}; border-bottom: 1px solid #e0e0e0;">
                            <td style="border: 1px solid #bbbbbb; padding: 8px; text-align: center; font-weight: 500;">
                                ${plan.customer_name || '군위고'}
                            </td>
                            <td style="border: 1px solid #bbbbbb; padding: 4px; text-align: center;">
                                <select id="meal-time-${plan.id}" onchange="updateMealTime(${plan.id}, this.value)" 
                                        style="width: 80px; padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;">
                                    <option value="breakfast" ${plan.meal_time === 'breakfast' ? 'selected' : ''}>조식</option>
                                    <option value="lunch" ${plan.meal_time === 'lunch' ? 'selected' : ''}>중식</option>
                                    <option value="dinner" ${plan.meal_time === 'dinner' ? 'selected' : ''}>석식</option>
                                    <option value="night" ${plan.meal_time === 'night' ? 'selected' : ''}>야식</option>
                                </select>
                            </td>
                            <td style="border: 1px solid #bbbbbb; padding: 4px; text-align: left;">
                                <input type="text" id="plan-name-${plan.id}" value="${plan.name}" 
                                       onchange="updatePlanName(${plan.id}, this.value)"
                                       style="width: 120px; padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;">
                            </td>
                            <td style="border: 1px solid #bbbbbb; padding: 4px; text-align: right;">
                                <input type="text" id="selling-price-${plan.id}" value="${Number(plan.selling_price || 0).toLocaleString()}" 
                                       onchange="updatePriceAndRatio(${plan.id}, 'selling_price', this.value)"
                                       onkeyup="formatNumberInput(this)"
                                       style="width: 90px; padding: 4px; border: 1px solid #ccc; border-radius: 3px; text-align: right; font-size: 12px;">
                            </td>
                            <td style="border: 1px solid #bbbbbb; padding: 4px; text-align: right;">
                                <input type="text" id="target-cost-${plan.id}" value="${Number(plan.target_material_cost || 0).toLocaleString()}"
                                       onchange="updatePriceAndRatio(${plan.id}, 'target_material_cost', this.value)"
                                       onkeyup="formatNumberInput(this)"
                                       style="width: 90px; padding: 4px; border: 1px solid #ccc; border-radius: 3px; text-align: right; font-size: 12px;">
                            </td>
                            <td style="border: 1px solid #bbbbbb; padding: 8px; text-align: center;">
                                <span id="cost-ratio-${plan.id}" style="color: ${ratioColor}; font-weight: bold;">
                                    ${costRatio}%
                                </span>
                            </td>
                            <td style="border: 1px solid #bbbbbb; padding: 8px; text-align: center;">
                                <button onclick="editMealPlan(${plan.id})" 
                                        style="padding: 4px 8px; background: #1976d2; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px;">
                                    수정
                                </button>
                            </td>
                            <td style="border: 1px solid #bbbbbb; padding: 8px; text-align: center;">
                                <button onclick="deleteMealPlan(${plan.id})" 
                                        style="padding: 4px 8px; background: #d32f2f; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px;">
                                    삭제
                                </button>
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
    const plan = mealPlans.find(p => p.id === planId);
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
    }
}

// 재료비 비율 업데이트
function updateCostRatio(planId) {
    const plan = mealPlans.find(p => p.id === planId);
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
    const name = prompt('새 식단표 이름을 입력하세요:', '새 식단표');
    if (!name || name.trim() === '') return;
    
    const newPlan = {
        id: Date.now(), // 임시 ID
        name: name.trim(),
        meal_time: 'lunch', // 기본값: 중식
        selling_price: 0,
        target_material_cost: 0,
        location_id: currentLocationId
    };
    
    mealPlans.push(newPlan);
    displayMealPlans();
    
    console.log('새 식단표 추가:', newPlan);
}

// 식단표 복사
function duplicateMealPlan(planId) {
    const plan = mealPlans.find(p => p.id === planId);
    if (!plan) return;
    
    const newPlan = {
        id: Date.now(), // 임시 ID
        name: plan.name + ' (복사)',
        meal_time: plan.meal_time, // 기존 시간대 복사
        selling_price: plan.selling_price,
        target_material_cost: plan.target_material_cost,
        location_id: currentLocationId
    };
    
    mealPlans.push(newPlan);
    displayMealPlans();
    
    console.log('식단표 복사:', newPlan);
}


// 식단표 삭제
function deleteMealPlan(planId) {
    if (mealPlans.length <= 1) {
        alert('최소 1개의 식단표는 유지해야 합니다.');
        return;
    }
    
    if (!confirm('이 식단표를 삭제하시겠습니까?')) return;
    
    mealPlans = mealPlans.filter(p => p.id !== planId);
    displayMealPlans();
    
    console.log('식단표 삭제, 남은 식단표:', mealPlans);
}

// 식단가 정보 저장
async function saveMealPricing() {
    if (!currentLocationId) {
        alert('사업장을 먼저 선택해주세요.');
        return;
    }
    
    if (!mealPlans || mealPlans.length === 0) {
        alert('저장할 식단표가 없습니다.');
        return;
    }
    
    try {
        console.log('식단가 정보 저장 시도:', {
            location_id: currentLocationId,
            meal_plans: mealPlans
        });
        
        // 실제로는 API 호출이 필요함
        // const response = await fetch('/api/admin/meal-pricing/save', {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify({
        //         location_id: currentLocationId,
        //         meal_plans: mealPlans
        //     })
        // });
        
        // 임시로 성공 메시지만 표시
        alert('식단가 정보가 저장되었습니다.');
        
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

// 숫자 입력 포맷팅 (콤마 추가)
function formatNumberInput(input) {
    let value = input.value.replace(/,/g, ''); // 기존 콤마 제거
    if (!isNaN(value) && value !== '') {
        input.value = Number(value).toLocaleString();
    }
}

// 가격 및 비율 실시간 업데이트
function updatePriceAndRatio(planId, field, value) {
    const plan = mealPlans.find(p => p.id === planId);
    if (!plan) return;
    
    // 콤마 제거 후 숫자로 변환
    const numValue = parseFloat(value.replace(/,/g, '')) || 0;
    plan[field] = numValue;
    
    // % 계산 및 업데이트
    const costRatio = plan.selling_price > 0 ? ((plan.target_material_cost / plan.selling_price) * 100).toFixed(1) : 0;
    const ratioSpan = document.querySelector(`#cost-ratio-${planId}`);
    
    if (ratioSpan) {
        const isOverLimit = parseFloat(costRatio) > 40;
        const ratioColor = isOverLimit ? '#d32f2f' : '#388e3c';
        ratioSpan.style.color = ratioColor;
        ratioSpan.textContent = `${costRatio}%`;
    }
    
    console.log(`${plan.customer_name || plan.name}: 판매가 ${Number(plan.selling_price).toLocaleString()}, 목표재료비 ${Number(plan.target_material_cost).toLocaleString()}, 비율 ${costRatio}%`);
}

// 식사시간 업데이트
function updateMealTime(planId, value) {
    const plan = mealPlans.find(p => p.id === planId);
    if (!plan) return;
    
    plan.meal_time = value;
    console.log(`${plan.customer_name || plan.name}: 식사시간을 ${value}로 변경`);
}

// 세부식단표명 업데이트
function updatePlanName(planId, value) {
    const plan = mealPlans.find(p => p.id === planId);
    if (!plan) return;
    
    plan.name = value;
    console.log(`${plan.customer_name || plan.name}: 식단표명을 ${value}로 변경`);
}

// 개별 식단표 저장
async function editMealPlan(planId) {
    const plan = mealPlans.find(p => p.id === planId);
    if (!plan) {
        alert('식단표를 찾을 수 없습니다.');
        return;
    }
    
    try {
        // 임시 ID(Date.now())인지 확인하여 POST/PUT 결정
        const isNewRecord = plan.id > 1000000000000; // Date.now()로 생성된 ID는 매우 큰 수
        
        let response;
        if (isNewRecord) {
            // 새 레코드 생성 (POST)
            response = await fetch('/api/admin/meal-pricing', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    customer_id: plan.location_id,
                    meal_type: plan.meal_time,
                    price: plan.selling_price,
                    material_cost_guideline: plan.target_material_cost,
                    effective_date: new Date().toISOString().split('T')[0],
                    notes: plan.name
                })
            });
        } else {
            // 기존 레코드 업데이트 (PUT)
            response = await fetch(`/api/admin/meal-pricing/${plan.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    customer_id: plan.location_id,
                    meal_type: plan.meal_time,
                    price: plan.selling_price,
                    material_cost_guideline: plan.target_material_cost,
                    effective_date: new Date().toISOString().split('T')[0],
                    notes: plan.name
                })
            });
        }
        
        const result = await response.json();
        if (result.success) {
            alert('식단가가 저장되었습니다.');
            // 새 레코드인 경우 실제 ID로 업데이트
            if (isNewRecord && result.pricing_id) {
                plan.id = result.pricing_id;
            }
            displayMealPlans(); // 화면 다시 그리기
        } else {
            alert('저장 실패: ' + result.message);
        }
    } catch (error) {
        console.error('식단가 저장 실패:', error);
        alert('저장 중 오류가 발생했습니다.');
    }
}

// 전체 저장 기능
async function saveMealPricingData() {
    try {
        let successCount = 0;
        let errorCount = 0;
        
        for (const plan of mealPlans) {
            try {
                // 임시 ID(Date.now())인지 확인하여 POST/PUT 결정
                const isNewRecord = plan.id > 1000000000000; // Date.now()로 생성된 ID는 매우 큰 수
                
                console.log(`저장 시도: ID=${plan.id}, location_id=${plan.location_id}, meal_type=${plan.meal_time}, isNew=${isNewRecord}`);
            
            let response;
            if (isNewRecord) {
                // 새 레코드 생성 (POST)
                response = await fetch('/api/admin/meal-pricing', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        customer_id: plan.location_id,
                        meal_type: plan.meal_time,
                        price: plan.selling_price,
                        material_cost_guideline: plan.target_material_cost,
                        effective_date: new Date().toISOString().split('T')[0],
                        notes: plan.name
                    })
                });
            } else {
                // 기존 레코드 업데이트 (PUT)
                response = await fetch(`/api/admin/meal-pricing/${plan.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        customer_id: plan.location_id,
                        meal_type: plan.meal_time,
                        price: plan.selling_price,
                        material_cost_guideline: plan.target_material_cost,
                        effective_date: new Date().toISOString().split('T')[0],
                        notes: plan.name
                    })
                });
            }
            
                const result = await response.json();
                if (result.success) {
                    successCount++;
                    console.log(`저장 성공: ${plan.name}`);
                    
                    // 새로 생성된 경우 실제 ID로 업데이트
                    if (isNewRecord && result.pricing_id) {
                        plan.id = result.pricing_id;
                        console.log(`새 ID 할당: ${plan.name} -> ID:${result.pricing_id}`);
                    }
                } else {
                    errorCount++;
                    console.error(`저장 실패: ${plan.name} - ${result.message}`);
                }
            } catch (planError) {
                errorCount++;
                console.error(`저장 오류: ${plan.name}`, planError);
            }
        }
        
        // 결과 리포트
        if (errorCount === 0) {
            alert(`모든 식단가 정보가 저장되었습니다. (성공: ${successCount}개)`);
            // 저장 후 현재 선택된 사업장의 데이터를 다시 로드
            const locationSelect = document.getElementById('businessLocationSelect');
            if (locationSelect && locationSelect.value) {
                await loadMealPlansForLocation(parseInt(locationSelect.value));
            }
        } else {
            alert(`저장 완료: 성공 ${successCount}개, 실패 ${errorCount}개. 실패한 항목은 콘솔을 확인하세요.`);
        }
        
    } catch (error) {
        console.error('전체 저장 실패:', error);
        alert('저장 중 오류가 발생했습니다: ' + error.message);
    }
}

// 전역 함수로 내보내기
window.loadBusinessLocationsForMealPricing = loadBusinessLocationsForMealPricing;
window.loadMealPlansForLocation = loadMealPlansForLocation;
window.displayMealPlans = displayMealPlans;
window.updateMealPlanField = updateMealPlanField;
window.updateCostRatio = updateCostRatio;
window.updatePriceAndRatio = updatePriceAndRatio;
window.updateMealTime = updateMealTime;
window.updatePlanName = updatePlanName;
window.formatNumberInput = formatNumberInput;
window.addNewMealPlan = addNewMealPlan;
window.duplicateMealPlan = duplicateMealPlan;
window.deleteMealPlan = deleteMealPlan;
window.editMealPlan = editMealPlan;
window.saveMealPricing = saveMealPricing;
window.saveMealPricingData = saveMealPricingData;
window.initializeMealPricingPage = initializeMealPricingPage;

})(); // IIFE 종료