// 식단가 관리 - 향상된 버전 v2
(function() {
    'use strict';

    console.log('💰 Enhanced Meal Pricing V2 Module Loading...');

    // 전역 변수
    let allMealPricing = [];
    let businessLocations = [];
    let editingCell = null;

    async function initEnhancedMealPricingV2() {
        console.log('🚀 Enhanced Meal Pricing V2 초기화 시작');

        const container = document.getElementById('meal-pricing-content');
        if (!container) {
            console.error('❌ meal-pricing-content 컨테이너를 찾을 수 없음');
            return;
        }

        // display 설정
        container.style.display = 'block';

        // HTML 구조 생성
        container.innerHTML = `
            <div class="meal-pricing-container">
                <!-- 헤더 -->
                <div class="page-header">
                    <h2>식단가 관리</h2>
                    <p class="page-description">사업장별 세부식단표를 관리하고 끼니별 매출가, 목표식재료비, 달성율을 설정합니다.</p>
                </div>

                <!-- 통계 박스 -->
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-icon">📊</div>
                        <div class="stat-content">
                            <div class="stat-value" id="total-meal-plans">0</div>
                            <div class="stat-label">전체 식단표</div>
                        </div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-icon">✅</div>
                        <div class="stat-content">
                            <div class="stat-value" id="active-meal-plans">0</div>
                            <div class="stat-label">활성 식단표</div>
                        </div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-icon">🏢</div>
                        <div class="stat-content">
                            <div class="stat-value" id="locations-count">0</div>
                            <div class="stat-label">관리 사업장</div>
                        </div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-icon">💵</div>
                        <div class="stat-content">
                            <div class="stat-value" id="avg-selling-price">0</div>
                            <div class="stat-label">평균 매출가</div>
                        </div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-icon">📈</div>
                        <div class="stat-content">
                            <div class="stat-value" id="avg-cost-ratio">0%</div>
                            <div class="stat-label">평균 달성율</div>
                        </div>
                    </div>
                </div>

                <!-- 액션 바 -->
                <div class="action-bar">
                    <div class="filter-container">
                        <!-- 사업장 선택 -->
                        <select id="location-filter" class="filter-select">
                            <option value="">전체 사업장</option>
                        </select>

                        <!-- 식단계획 선택 -->
                        <select id="meal-plan-filter" class="filter-select">
                            <option value="">전체 식단계획</option>
                            <option value="조식">조식</option>
                            <option value="중식">중식</option>
                            <option value="석식">석식</option>
                            <option value="야식">야식</option>
                        </select>

                        <!-- 운영 타입 선택 -->
                        <select id="operation-filter" class="filter-select">
                            <option value="">전체 운영</option>
                            <option value="도시락">도시락</option>
                            <option value="운반">운반</option>
                            <option value="위탁급식">위탁급식</option>
                            <option value="행사">행사</option>
                            <option value="기타">기타</option>
                        </select>
                    </div>

                    <button class="btn btn-primary" onclick="openAddMealPricingModal()">
                        <span>+ 새 식단표 추가</span>
                    </button>
                </div>

                <!-- 테이블 -->
                <div class="table-container">
                    <table class="data-table compact-table">
                        <thead>
                            <tr>
                                <th style="width: 15%;">사업장</th>
                                <th style="width: 10%;">식단계획</th>
                                <th style="width: 10%;">운영</th>
                                <th style="width: 15%;">식단명</th>
                                <th style="width: 10%;">적용기간</th>
                                <th style="width: 10%; text-align: right;">매출가</th>
                                <th style="width: 10%; text-align: right;">목표식재료비</th>
                                <th style="width: 8%; text-align: center;">달성율</th>
                                <th style="width: 6%; text-align: center;">상태</th>
                                <th style="width: 6%; text-align: center;">관리</th>
                            </tr>
                        </thead>
                        <tbody id="meal-pricing-tbody">
                            <tr>
                                <td colspan="10" class="text-center">데이터 로딩 중...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        // 스타일 추가
        addMealPricingStyles();

        // 사업장 목록 로드
        await loadBusinessLocations();

        // 데이터 로드
        await loadMealPricingData();

        // 이벤트 리스너 설정
        setupEventListeners();
    }

    // 스타일 추가
    function addMealPricingStyles() {
        if (document.getElementById('meal-pricing-styles-v2')) return;

        const style = document.createElement('style');
        style.id = 'meal-pricing-styles-v2';
        style.textContent = `
            .meal-pricing-container {
                padding: 20px;
            }

            .page-header {
                margin-bottom: 20px;
            }

            .page-header h2 {
                margin: 0 0 10px 0;
                color: #333;
                font-size: 24px;
            }

            .page-description {
                color: #666;
                margin: 0;
            }

            /* 통계 박스 */
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }

            .stat-box {
                background: white;
                border-radius: 8px;
                padding: 15px;
                display: flex;
                align-items: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: transform 0.2s;
            }

            .stat-box:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }

            .stat-icon {
                font-size: 28px;
                margin-right: 15px;
            }

            .stat-content {
                flex: 1;
            }

            .stat-value {
                font-size: 20px;
                font-weight: bold;
                color: #333;
            }

            .stat-label {
                font-size: 12px;
                color: #666;
                margin-top: 4px;
            }

            /* 액션 바 */
            .action-bar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                background: white;
                padding: 15px;
                border-radius: 8px;
            }

            .filter-container {
                display: flex;
                gap: 10px;
                flex: 1;
            }

            .filter-select {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                background: white;
                cursor: pointer;
            }

            .filter-select:hover {
                border-color: #007bff;
            }

            /* 컴팩트 테이블 */
            .compact-table {
                width: 100%;
                background: white;
                border-collapse: collapse;
            }

            .compact-table th {
                background: #f8f9fa;
                padding: 8px 10px;
                font-size: 13px;
                font-weight: 600;
                border: 1px solid #dee2e6;
                text-align: left;
            }

            .compact-table td {
                padding: 6px 10px;
                font-size: 13px;
                border: 1px solid #dee2e6;
                line-height: 1.3;
            }

            .compact-table tbody tr {
                transition: background-color 0.2s;
            }

            .compact-table tbody tr:hover {
                background-color: #f8f9fa;
            }

            /* 편집 가능한 셀 */
            .editable-cell {
                cursor: pointer;
                position: relative;
            }

            .editable-cell:hover {
                background-color: #e7f3ff;
            }

            .editing-input {
                width: 100%;
                padding: 4px;
                border: 2px solid #007bff;
                border-radius: 3px;
                font-size: 13px;
            }

            /* 버튼 */
            .btn {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s;
            }

            .btn-primary {
                background: #007bff;
                color: white;
            }

            .btn-primary:hover {
                background: #0056b3;
            }

            .btn-small {
                padding: 4px 8px;
                font-size: 12px;
            }

            .btn-edit {
                background: #28a745;
                color: white;
                margin-right: 4px;
            }

            .btn-delete {
                background: #dc3545;
                color: white;
            }

            /* 상태 뱃지 */
            .badge {
                display: inline-block;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
            }

            .badge-active {
                background: #d4edda;
                color: #155724;
            }

            .badge-inactive {
                background: #f8d7da;
                color: #721c24;
            }

            /* 달성율 표시 - 40% 기준 */
            .ratio-good {
                color: #28a745;
                font-weight: 600;
            }

            .ratio-danger {
                color: #dc3545;
                font-weight: 600;
            }

            .text-center {
                text-align: center;
            }

            .text-right {
                text-align: right;
            }
        `;
        document.head.appendChild(style);
    }

    // 사업장 목록 로드
    async function loadBusinessLocations() {
        try {
            const response = await fetch('http://127.0.0.1:8010/api/admin/business-locations');
            const data = await response.json();

            if (data.success && data.locations) {
                businessLocations = data.locations;

                // 드롭다운 채우기
                const select = document.getElementById('location-filter');
                businessLocations.forEach(loc => {
                    const option = document.createElement('option');
                    option.value = loc.name;
                    option.textContent = loc.name;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('사업장 목록 로드 실패:', error);
        }
    }

    // 데이터 로드
    async function loadMealPricingData() {
        console.log('📊 식단가 데이터 로드 시작');

        try {
            const response = await fetch('http://127.0.0.1:8010/api/admin/meal-pricing');
            const data = await response.json();

            console.log('✅ 데이터 로드 성공:', data);

            if (data.success && data.meal_pricing) {
                allMealPricing = data.meal_pricing;
                updateStatistics(data.statistics || {});
                displayMealPricing(allMealPricing);
            } else {
                displayError();
            }
        } catch (error) {
            console.error('❌ 데이터 로드 실패:', error);
            displayError();
        }
    }

    // 통계 업데이트
    function updateStatistics(stats) {
        document.getElementById('total-meal-plans').textContent = stats.total || '0';
        document.getElementById('active-meal-plans').textContent = stats.active || '0';
        document.getElementById('locations-count').textContent = stats.locations || '0';

        // 원화 기호 제거
        const avgPrice = stats.avg_selling_price || 0;
        document.getElementById('avg-selling-price').textContent =
            Number(avgPrice).toLocaleString();

        const avgRatio = stats.avg_cost_ratio || 0;
        document.getElementById('avg-cost-ratio').textContent =
            avgRatio.toFixed(1) + '%';
    }

    // 식단가 데이터 표시
    function displayMealPricing(mealPricing) {
        console.log(`📝 ${mealPricing.length}개 식단가 표시`);

        const tbody = document.getElementById('meal-pricing-tbody');
        if (!tbody) {
            console.error('❌ tbody를 찾을 수 없음');
            return;
        }

        if (mealPricing.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="10" class="text-center">등록된 식단표가 없습니다</td>
                </tr>
            `;
            return;
        }

        // 사업장명으로 정렬
        const sortedPricing = [...mealPricing].sort((a, b) => {
            const nameA = a.location_name || '';
            const nameB = b.location_name || '';
            return nameA.localeCompare(nameB, 'ko');
        });

        tbody.innerHTML = sortedPricing.map(pricing => {
            const startDate = pricing.apply_date_start ?
                new Date(pricing.apply_date_start).toLocaleDateString('ko-KR') : '-';
            const endDate = pricing.apply_date_end ?
                new Date(pricing.apply_date_end).toLocaleDateString('ko-KR') : '-';

            // 달성율 계산 (목표식재료비 / 매출가 * 100)
            const ratio = pricing.selling_price > 0 ?
                (pricing.material_cost_guideline / pricing.selling_price * 100) : 0;

            // 40% 기준으로 색상 결정
            const ratioClass = ratio >= 40 ? 'ratio-danger' : 'ratio-good';

            // 운영 타입 매핑
            const operationType = mapOperationType(pricing.meal_type);

            return `
                <tr data-id="${pricing.id}">
                    <td>${pricing.location_name || '-'}</td>
                    <td>${pricing.meal_plan_type || '-'}</td>
                    <td>${operationType}</td>
                    <td>${pricing.plan_name || '-'}</td>
                    <td style="font-size: 11px;">${startDate}<br>~${endDate}</td>
                    <td class="text-right editable-cell"
                        data-field="selling_price"
                        data-id="${pricing.id}"
                        onclick="startEdit(this, ${pricing.id}, 'selling_price', ${pricing.selling_price})">
                        ${Number(pricing.selling_price || 0).toLocaleString()}
                    </td>
                    <td class="text-right editable-cell"
                        data-field="material_cost_guideline"
                        data-id="${pricing.id}"
                        onclick="startEdit(this, ${pricing.id}, 'material_cost_guideline', ${pricing.material_cost_guideline})">
                        ${Number(pricing.material_cost_guideline || 0).toLocaleString()}
                    </td>
                    <td class="text-center">
                        <span class="${ratioClass}">${ratio.toFixed(1)}%</span>
                    </td>
                    <td class="text-center">
                        ${pricing.is_active ?
                            '<span class="badge badge-active">활성</span>' :
                            '<span class="badge badge-inactive">비활성</span>'}
                    </td>
                    <td class="text-center">
                        <button class="btn btn-small btn-delete" onclick="deleteMealPricing(${pricing.id})">삭제</button>
                    </td>
                </tr>
            `;
        }).join('');

        console.log('✅ 식단가 표시 완료');
    }

    // 운영 타입 매핑
    function mapOperationType(mealType) {
        const typeMap = {
            '도시락': '도시락',
            '운반': '운반',
            '급식': '위탁급식',
            '케어': '위탁급식',
            '행사': '행사'
        };
        return typeMap[mealType] || '기타';
    }

    // 셀 편집 시작
    window.startEdit = function(cell, id, field, currentValue) {
        // 이미 편집 중인 셀이 있으면 저장
        if (editingCell) {
            saveEdit();
        }

        editingCell = { cell, id, field };

        const input = document.createElement('input');
        input.type = 'number';
        input.className = 'editing-input';
        input.value = currentValue;

        cell.innerHTML = '';
        cell.appendChild(input);
        input.focus();
        input.select();

        // 엔터키로 저장, ESC로 취소
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                saveEdit();
            } else if (e.key === 'Escape') {
                cancelEdit();
            }
        });

        // 포커스 잃으면 저장
        input.addEventListener('blur', () => {
            setTimeout(saveEdit, 100);
        });
    };

    // 편집 저장
    function saveEdit() {
        if (!editingCell) return;

        const { cell, id, field } = editingCell;
        const input = cell.querySelector('input');
        if (!input) return;

        const newValue = parseFloat(input.value) || 0;

        // API 호출하여 저장
        updateMealPricing(id, field, newValue);

        // UI 업데이트
        cell.innerHTML = newValue.toLocaleString();

        // 달성율 재계산
        if (field === 'selling_price' || field === 'material_cost_guideline') {
            recalculateRatio(id);
        }

        editingCell = null;
    }

    // 편집 취소
    function cancelEdit() {
        if (!editingCell) return;

        const { cell, id, field } = editingCell;
        const pricing = allMealPricing.find(p => p.id === id);

        if (pricing) {
            cell.innerHTML = Number(pricing[field] || 0).toLocaleString();
        }

        editingCell = null;
    }

    // 달성율 재계산
    function recalculateRatio(id) {
        const row = document.querySelector(`tr[data-id="${id}"]`);
        if (!row) return;

        const sellingCell = row.querySelector('[data-field="selling_price"]');
        const materialCell = row.querySelector('[data-field="material_cost_guideline"]');
        const ratioCell = row.cells[7];

        const selling = parseFloat(sellingCell.textContent.replace(/,/g, '')) || 0;
        const material = parseFloat(materialCell.textContent.replace(/,/g, '')) || 0;

        const ratio = selling > 0 ? (material / selling * 100) : 0;
        const ratioClass = ratio >= 40 ? 'ratio-danger' : 'ratio-good';

        ratioCell.innerHTML = `<span class="${ratioClass}">${ratio.toFixed(1)}%</span>`;
    }

    // API 호출하여 업데이트
    async function updateMealPricing(id, field, value) {
        try {
            const pricing = allMealPricing.find(p => p.id === id);
            if (!pricing) return;

            pricing[field] = value;

            const response = await fetch(`http://127.0.0.1:8010/api/admin/meal-pricing/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(pricing)
            });

            const result = await response.json();
            if (result.success) {
                console.log('✅ 업데이트 성공');
            } else {
                console.error('❌ 업데이트 실패:', result.error);
            }
        } catch (error) {
            console.error('❌ API 호출 실패:', error);
        }
    }

    // 이벤트 리스너 설정
    function setupEventListeners() {
        // 필터 이벤트
        document.getElementById('location-filter')?.addEventListener('change', filterData);
        document.getElementById('meal-plan-filter')?.addEventListener('change', filterData);
        document.getElementById('operation-filter')?.addEventListener('change', filterData);
    }

    // 데이터 필터링
    function filterData() {
        const locationFilter = document.getElementById('location-filter').value;
        const mealPlanFilter = document.getElementById('meal-plan-filter').value;
        const operationFilter = document.getElementById('operation-filter').value;

        let filtered = [...allMealPricing];

        if (locationFilter) {
            filtered = filtered.filter(p => p.location_name === locationFilter);
        }

        if (mealPlanFilter) {
            filtered = filtered.filter(p => p.meal_plan_type === mealPlanFilter);
        }

        if (operationFilter) {
            const operationTypes = {
                '도시락': ['도시락'],
                '운반': ['운반'],
                '위탁급식': ['급식', '케어'],
                '행사': ['행사'],
                '기타': []
            };

            const types = operationTypes[operationFilter];
            if (types && types.length > 0) {
                filtered = filtered.filter(p => types.includes(p.meal_type));
            }
        }

        displayMealPricing(filtered);
    }

    // 에러 표시
    function displayError() {
        const tbody = document.getElementById('meal-pricing-tbody');
        if (!tbody) return;

        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="text-center" style="color: #dc3545;">
                    데이터를 불러올 수 없습니다. 서버 연결을 확인해주세요.
                </td>
            </tr>
        `;
    }

    // 전역 함수들
    window.initEnhancedMealPricingV2 = initEnhancedMealPricingV2;

    window.openAddMealPricingModal = function() {
        console.log('새 식단표 추가 모달 열기');
        alert('새 식단표 추가 기능은 준비 중입니다.');
    };

    window.deleteMealPricing = async function(id) {
        if (!confirm('정말로 이 식단표를 삭제하시겠습니까?')) return;

        try {
            const response = await fetch(`http://127.0.0.1:8010/api/admin/meal-pricing/${id}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            if (result.success) {
                console.log('✅ 삭제 성공');
                loadMealPricingData(); // 데이터 새로고침
            } else {
                alert('삭제 실패: ' + result.error);
            }
        } catch (error) {
            console.error('❌ 삭제 실패:', error);
            alert('삭제 중 오류가 발생했습니다.');
        }
    };

    console.log('✅ Enhanced Meal Pricing V2 Module 로드 완료');
})();