// 식단가 관리 - 향상된 버전 v3 (수정 모달 포함)
(function() {
    'use strict';

    console.log('💰 Enhanced Meal Pricing V3 Module Loading...');

    // 전역 변수
    let allMealPricing = [];
    let businessLocations = [];
    let editingCell = null;
    let currentEditingId = null;

    // 사업장 선택 핸들러를 먼저 정의 (전역 함수) - 가장 먼저 실행
    window.handleLocationChange = function(selectElement) {
        const locationName = selectElement ? selectElement.value : '';
        console.log('=== 사업장 변경 이벤트 발생 ===');
        console.log('선택된 사업장:', locationName);
        console.log('selectElement:', selectElement);

        if (!locationName) {
            console.log('빈 값 선택됨');
            return;
        }

        // 사업장별 기본 식단 유형 설정
        const defaultMealPlans = {
            '학교': '중식',
            '도시락': '중식',
            '운반': '중식',
            '요양원': '조식'
        };

        // 사업장별 기본 운영 유형 설정
        const defaultOperations = {
            '학교': '급식',
            '도시락': '도시락',
            '운반': '운반',
            '요양원': '케어'
        };

        // 식단계획 설정
        const mealPlanSelect = document.getElementById('edit-meal-plan');
        if (mealPlanSelect && defaultMealPlans[locationName]) {
            console.log('설정 전 식단계획 값:', mealPlanSelect.value);
            console.log('설정할 값:', defaultMealPlans[locationName]);

            // 모든 옵션의 selected 속성 초기화
            for (let i = 0; i < mealPlanSelect.options.length; i++) {
                mealPlanSelect.options[i].selected = false;
            }

            // 직접 selectedIndex 설정
            let targetIndex = -1;
            for (let i = 0; i < mealPlanSelect.options.length; i++) {
                if (mealPlanSelect.options[i].value === defaultMealPlans[locationName]) {
                    targetIndex = i;
                    break;
                }
            }

            if (targetIndex !== -1) {
                // 직접 인덱스 설정
                mealPlanSelect.selectedIndex = targetIndex;
                console.log(`인덱스 ${targetIndex}로 직접 설정: ${mealPlanSelect.options[targetIndex].text}`);

                // 값도 명시적으로 설정
                mealPlanSelect.value = defaultMealPlans[locationName];

                // change 이벤트 발생
                const changeEvent = new Event('change', { bubbles: true });
                mealPlanSelect.dispatchEvent(changeEvent);
            }

            console.log('설정 후 식단계획 값:', mealPlanSelect.value);
            console.log('선택된 텍스트:', mealPlanSelect.options[mealPlanSelect.selectedIndex]?.text);

            // 시각적 피드백
            mealPlanSelect.style.backgroundColor = '#e8f5e9';
            mealPlanSelect.style.border = '2px solid #4CAF50';
            setTimeout(() => {
                mealPlanSelect.style.backgroundColor = '';
                mealPlanSelect.style.border = '';
            }, 1500);
        }

        // 운영타입 설정
        const operationSelect = document.getElementById('edit-operation');
        if (operationSelect && defaultOperations[locationName]) {
            console.log('설정 전 운영타입 값:', operationSelect.value);
            console.log('설정할 값:', defaultOperations[locationName]);

            // 모든 옵션의 selected 속성 초기화
            for (let i = 0; i < operationSelect.options.length; i++) {
                operationSelect.options[i].selected = false;
            }

            // 직접 selectedIndex 설정
            let targetIndex = -1;
            for (let i = 0; i < operationSelect.options.length; i++) {
                if (operationSelect.options[i].value === defaultOperations[locationName]) {
                    targetIndex = i;
                    break;
                }
            }

            if (targetIndex !== -1) {
                // 직접 인덱스 설정
                operationSelect.selectedIndex = targetIndex;
                console.log(`인덱스 ${targetIndex}로 직접 설정: ${operationSelect.options[targetIndex].text}`);

                // 값도 명시적으로 설정
                operationSelect.value = defaultOperations[locationName];

                // change 이벤트 발생
                const changeEvent = new Event('change', { bubbles: true });
                operationSelect.dispatchEvent(changeEvent);
            }

            console.log('설정 후 운영타입 값:', operationSelect.value);
            console.log('선택된 텍스트:', operationSelect.options[operationSelect.selectedIndex]?.text);

            // 시각적 피드백
            operationSelect.style.backgroundColor = '#e8f5e9';
            operationSelect.style.border = '2px solid #4CAF50';
            setTimeout(() => {
                operationSelect.style.backgroundColor = '';
                operationSelect.style.border = '';
            }, 1500);
        }

        // 식단명 생성
        const planNameInput = document.getElementById('edit-plan-name');
        if (planNameInput) {
            const today = new Date().toISOString().slice(0, 10);
            const operationType = defaultOperations[locationName] || '';
            planNameInput.value = `${locationName} ${operationType} ${today}`;
            console.log('식단명 생성:', planNameInput.value);
        }

        console.log('=== 사업장 변경 처리 완료 ===');
    };

    async function initEnhancedMealPricingV3() {
        console.log('🚀 Enhanced Meal Pricing V3 초기화 시작');

        const container = document.getElementById('meal-pricing-content');
        if (!container) {
            console.error('❌ meal-pricing-content 컨테이너를 찾을 수 없음');
            return;
        }

        console.log('📦 컨테이너 상태:', {
            id: container.id,
            display: container.style.display,
            classList: container.className,
            innerHTML길이: container.innerHTML.length
        });

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

            <!-- 수정 모달 -->
            <div id="meal-pricing-modal" class="modal-overlay" style="display: none;">
                <div class="modal-dialog">
                    <div class="modal-header">
                        <h3 id="modal-title">식단표 수정</h3>
                        <button class="modal-close" onclick="closeMealPricingModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>사업장</label>
                            <select id="edit-location" class="form-control" onchange="window.handleLocationChange(this)">
                                <option value="">선택하세요</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label>식단계획</label>
                            <select id="edit-meal-plan" class="form-control">
                                <option value="">선택하세요</option>
                                <option value="조식">조식</option>
                                <option value="중식">중식</option>
                                <option value="석식">석식</option>
                                <option value="야식">야식</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label>운영 타입</label>
                            <select id="edit-operation" class="form-control">
                                <option value="">선택하세요</option>
                                <option value="도시락">도시락</option>
                                <option value="운반">운반</option>
                                <option value="급식">위탁급식</option>
                                <option value="케어">케어</option>
                                <option value="행사">행사</option>
                                <option value="기타">기타</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label>식단명</label>
                            <input type="text" id="edit-plan-name" class="form-control" placeholder="식단명 입력">
                        </div>

                        <div class="form-row">
                            <div class="form-group half">
                                <label>시작일</label>
                                <input type="date" id="edit-start-date" class="form-control">
                            </div>
                            <div class="form-group half">
                                <label>종료일</label>
                                <input type="date" id="edit-end-date" class="form-control">
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group half">
                                <label>매출가</label>
                                <input type="number" id="edit-selling-price" class="form-control" placeholder="0">
                            </div>
                            <div class="form-group half">
                                <label>목표식재료비</label>
                                <input type="number" id="edit-material-cost" class="form-control" placeholder="0">
                            </div>
                        </div>

                        <div class="form-group">
                            <label>달성율</label>
                            <div id="edit-ratio" class="ratio-display">0%</div>
                        </div>

                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="edit-is-active"> 활성 상태
                            </label>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="closeMealPricingModal()">취소</button>
                        <button class="btn btn-primary" onclick="saveMealPricing()">저장</button>
                    </div>
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
        if (document.getElementById('meal-pricing-styles-v3')) return;

        const style = document.createElement('style');
        style.id = 'meal-pricing-styles-v3';
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
                cursor: pointer;
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

            /* 버튼 - 컴팩트 */
            .btn {
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                cursor: pointer;
                transition: all 0.2s;
                height: 30px;
            }

            .btn-primary {
                background: #007bff;
                color: white;
            }

            .btn-primary:hover {
                background: #0056b3;
            }

            .btn-secondary {
                background: #6c757d;
                color: white;
            }

            .btn-secondary:hover {
                background: #5a6268;
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

            /* 모달 스타일 */
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 9999;
            }

            .modal-overlay[style*="flex"] {
                display: flex !important;
            }

            .modal-dialog {
                background: white;
                border-radius: 8px;
                width: 90%;
                max-width: 550px;
                max-height: 90vh;
                overflow-y: auto;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                position: relative;
            }

            .modal-header {
                padding: 12px 16px;
                border-bottom: 1px solid #dee2e6;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .modal-header h3 {
                margin: 0;
                font-size: 18px;
                color: #333;
            }

            .modal-close {
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #999;
                padding: 0;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                line-height: 1;
            }

            .modal-close:hover {
                color: #333;
            }

            .modal-body {
                padding: 12px 16px;
            }

            .modal-footer {
                padding: 10px 16px;
                border-top: 1px solid #dee2e6;
                display: flex;
                justify-content: flex-end;
                gap: 8px;
            }

            /* 폼 스타일 - 컴팩트 */
            .form-group {
                margin-bottom: 8px;
            }

            .form-group label {
                display: block;
                margin-bottom: 3px;
                font-weight: 600;
                font-size: 13px;
                color: #333;
            }

            .form-control {
                width: 100%;
                padding: 5px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
                height: 28px;
                color: #333 !important;
                background-color: #fff !important;
            }

            select.form-control {
                height: 30px;
                color: #333 !important;
                background-color: #fff !important;
            }

            select.form-control option {
                color: #333 !important;
                background-color: #fff !important;
            }

            .form-control:focus {
                outline: none;
                border-color: #007bff;
                box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
            }

            .form-row {
                display: flex;
                gap: 10px;
            }

            .form-group.half {
                flex: 1;
            }

            .ratio-display {
                padding: 6px 8px;
                background: #f8f9fa;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
                text-align: center;
                height: 28px;
                line-height: 16px;
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
                // 중복 제거 - 이름 기준으로 unique한 사업장만 선택
                const uniqueLocations = [];
                const seenNames = new Set();

                for (const loc of data.locations) {
                    if (!seenNames.has(loc.name)) {
                        seenNames.add(loc.name);
                        uniqueLocations.push(loc);
                    }
                }

                businessLocations = uniqueLocations;

                // 필터 드롭다운 채우기
                const filterSelect = document.getElementById('location-filter');
                const editSelect = document.getElementById('edit-location');

                // 기존 옵션 제거 (첫 번째 기본 옵션 제외)
                while (filterSelect.options.length > 1) {
                    filterSelect.remove(1);
                }
                while (editSelect.options.length > 1) {
                    editSelect.remove(1);
                }

                // 중복 제거된 사업장 추가
                businessLocations.forEach(loc => {
                    // 필터용
                    const filterOption = document.createElement('option');
                    filterOption.value = loc.name;
                    filterOption.textContent = loc.name;
                    filterSelect.appendChild(filterOption);

                    // 수정 모달용
                    const editOption = document.createElement('option');
                    editOption.value = loc.name;
                    editOption.textContent = loc.name;
                    editSelect.appendChild(editOption);
                });

                console.log('✅ 사업장 목록 로드 완료:', businessLocations.map(l => l.name).join(', '));
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
            console.log('📋 식단가 데이터 개수:', data.meal_pricing ? data.meal_pricing.length : 0);

            if (data.success && data.meal_pricing) {
                allMealPricing = data.meal_pricing;
                updateStatistics(data.statistics || {});
                displayMealPricing(allMealPricing);
            } else {
                console.error('❌ 데이터 로드 실패 - success false 또는 데이터 없음');
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
                <tr data-id="${pricing.id}" onclick="openEditMealPricingModal(${pricing.id})">
                    <td>${pricing.location_name || '-'}</td>
                    <td>${pricing.meal_plan_type || '-'}</td>
                    <td>${operationType}</td>
                    <td>${pricing.plan_name || '-'}</td>
                    <td style="font-size: 11px;">${startDate}<br>~${endDate}</td>
                    <td class="text-right editable-cell"
                        data-field="selling_price"
                        data-id="${pricing.id}"
                        onclick="event.stopPropagation(); startEdit(this, ${pricing.id}, 'selling_price', ${pricing.selling_price})">
                        ${Number(pricing.selling_price || 0).toLocaleString()}
                    </td>
                    <td class="text-right editable-cell"
                        data-field="material_cost_guideline"
                        data-id="${pricing.id}"
                        onclick="event.stopPropagation(); startEdit(this, ${pricing.id}, 'material_cost_guideline', ${pricing.material_cost_guideline})">
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
                    <td class="text-center" onclick="event.stopPropagation()">
                        <button class="btn btn-small btn-edit" onclick="openEditMealPricingModal(${pricing.id})">수정</button>
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

    // 수정 모달 열기
    window.openEditMealPricingModal = function(id) {
        console.log('=== 수정 모달 열기 ===');
        console.log('ID:', id);

        const pricing = allMealPricing.find(p => p.id === id);
        if (!pricing) {
            console.log('데이터를 찾을 수 없음');
            return;
        }
        console.log('수정할 데이터:', pricing);

        currentEditingId = id;

        // 모달 제목 설정
        const modalTitle = document.getElementById('modal-title');
        if (modalTitle) modalTitle.textContent = '식단표 수정';

        // 데이터 채우기
        const location = document.getElementById('edit-location');
        const mealPlan = document.getElementById('edit-meal-plan');
        const operation = document.getElementById('edit-operation');
        const planName = document.getElementById('edit-plan-name');
        const startDate = document.getElementById('edit-start-date');
        const endDate = document.getElementById('edit-end-date');
        const sellingPrice = document.getElementById('edit-selling-price');
        const materialCost = document.getElementById('edit-material-cost');
        const isActive = document.getElementById('edit-is-active');

        console.log('필드 요소들:', {
            location: location ? '있음' : '없음',
            mealPlan: mealPlan ? '있음' : '없음',
            operation: operation ? '있음' : '없음'
        });

        if (location) {
            // 옵션 순회하며 텍스트 매칭
            const targetValue = pricing.location_name || '';
            console.log('사업장 찾기:', targetValue, '옵션 수:', location.options.length);

            let found = false;
            for (let i = 0; i < location.options.length; i++) {
                console.log(`옵션 ${i}: text="${location.options[i].text}", value="${location.options[i].value}"`);
                if (location.options[i].text === targetValue || location.options[i].value === targetValue) {
                    location.selectedIndex = i;
                    location.value = location.options[i].value;
                    console.log('사업장 선택됨:', i, location.options[i].text);
                    console.log('실제 설정된 값:', location.value, '선택된 인덱스:', location.selectedIndex);

                    // 강제로 UI 업데이트 - handleLocationChange를 트리거하지 않도록 수정
                    // location.dispatchEvent(new Event('change', { bubbles: true }));

                    // 확인
                    setTimeout(() => {
                        console.log('100ms 후 확인 - 값:', location.value, '인덱스:', location.selectedIndex);
                        console.log('드롭다운 HTML:', location.outerHTML);
                    }, 100);
                    found = true;
                    break;
                }
            }

            if (!found) {
                console.warn('⚠️ 사업장 매칭 실패:', targetValue);
                console.log('현재 선택된 값:', location.value);
            }
        }
        if (mealPlan) {
            const targetValue = pricing.meal_plan_type || '';
            console.log('식단계획 찾기:', targetValue, '옵션 수:', mealPlan.options.length);

            for (let i = 0; i < mealPlan.options.length; i++) {
                console.log(`옵션 ${i}: text="${mealPlan.options[i].text}", value="${mealPlan.options[i].value}"`);
                if (mealPlan.options[i].text === targetValue || mealPlan.options[i].value === targetValue) {
                    mealPlan.selectedIndex = i;
                    mealPlan.value = mealPlan.options[i].value;
                    console.log('식단계획 선택됨:', i, mealPlan.options[i].text);
                    console.log('실제 설정된 값:', mealPlan.value, '선택된 인덱스:', mealPlan.selectedIndex);

                    // 강제로 UI 업데이트 - 비활성화
                    // mealPlan.dispatchEvent(new Event('change', { bubbles: true }));

                    // 확인
                    setTimeout(() => {
                        console.log('100ms 후 확인 - 값:', mealPlan.value, '인덱스:', mealPlan.selectedIndex);
                    }, 100);
                    break;
                }
            }
        }
        if (operation) {
            const targetValue = pricing.meal_type || '';
            console.log('운영타입 찾기:', targetValue, '옵션 수:', operation.options.length);

            for (let i = 0; i < operation.options.length; i++) {
                console.log(`옵션 ${i}: text="${operation.options[i].text}", value="${operation.options[i].value}"`);
                if (operation.options[i].text === targetValue || operation.options[i].value === targetValue) {
                    operation.selectedIndex = i;
                    operation.value = operation.options[i].value;
                    console.log('운영타입 선택됨:', i, operation.options[i].text);
                    console.log('실제 설정된 값:', operation.value, '선택된 인덱스:', operation.selectedIndex);

                    // 강제로 UI 업데이트 - 비활성화
                    // operation.dispatchEvent(new Event('change', { bubbles: true }));

                    // 확인
                    setTimeout(() => {
                        console.log('100ms 후 확인 - 값:', operation.value, '인덱스:', operation.selectedIndex);
                    }, 100);
                    break;
                }
            }
        }
        if (planName) planName.value = pricing.plan_name || '';
        if (startDate) startDate.value = pricing.apply_date_start || '';
        if (endDate) endDate.value = pricing.apply_date_end || '';
        if (sellingPrice) sellingPrice.value = pricing.selling_price || 0;
        if (materialCost) materialCost.value = pricing.material_cost_guideline || 0;
        if (isActive) isActive.checked = pricing.is_active;

        // 달성율 계산
        calculateEditRatio();

        // 모달 표시
        const modal = document.getElementById('meal-pricing-modal');
        if (modal) {
            modal.style.display = 'flex';
        }

        // 모달 이벤트 리스너 재바인딩
        setupModalEventListeners();
    };

    // 새 식단표 추가 모달
    window.openAddMealPricingModal = function() {
        currentEditingId = null;

        // 모달 제목 설정
        const modalTitle = document.getElementById('modal-title');
        if (modalTitle) modalTitle.textContent = '새 식단표 추가';

        // 폼 초기화
        const elements = {
            'edit-location': '',
            'edit-meal-plan': '',
            'edit-operation': '',
            'edit-plan-name': '',
            'edit-start-date': '',
            'edit-end-date': '',
            'edit-selling-price': '',
            'edit-material-cost': ''
        };

        for (const [id, value] of Object.entries(elements)) {
            const element = document.getElementById(id);
            if (element) element.value = value;
        }

        const isActive = document.getElementById('edit-is-active');
        if (isActive) isActive.checked = true;

        const ratio = document.getElementById('edit-ratio');
        if (ratio) {
            ratio.textContent = '0%';
            ratio.style.color = '#28a745';
        }

        // 모달 표시
        const modal = document.getElementById('meal-pricing-modal');
        if (modal) {
            modal.style.display = 'flex';
        }

        // 모달 이벤트 리스너 재바인딩
        setupModalEventListeners();
    };

    // 모달 닫기
    window.closeMealPricingModal = function() {
        const modal = document.getElementById('meal-pricing-modal');
        if (modal) {
            modal.style.display = 'none';
            currentEditingId = null;
        }
    };


    // 달성율 계산 (모달용)
    function calculateEditRatio() {
        const selling = parseFloat(document.getElementById('edit-selling-price').value) || 0;
        const material = parseFloat(document.getElementById('edit-material-cost').value) || 0;

        const ratio = selling > 0 ? (material / selling * 100) : 0;
        const ratioDisplay = document.getElementById('edit-ratio');

        ratioDisplay.textContent = ratio.toFixed(1) + '%';
        ratioDisplay.style.color = ratio >= 40 ? '#dc3545' : '#28a745';
    }

    // 저장
    window.saveMealPricing = async function() {
        const locationName = document.getElementById('edit-location').value;
        const location = businessLocations.find(loc => loc.name === locationName);

        const data = {
            location_id: location ? location.id : null,
            location_name: locationName,
            meal_plan_type: document.getElementById('edit-meal-plan').value,
            meal_type: document.getElementById('edit-operation').value,
            plan_name: document.getElementById('edit-plan-name').value,
            apply_date_start: document.getElementById('edit-start-date').value,
            apply_date_end: document.getElementById('edit-end-date').value,
            selling_price: parseFloat(document.getElementById('edit-selling-price').value) || 0,
            material_cost_guideline: parseFloat(document.getElementById('edit-material-cost').value) || 0,
            cost_ratio: 0, // 서버에서 계산
            is_active: document.getElementById('edit-is-active').checked ? 1 : 0
        };

        // 달성율 계산
        if (data.selling_price > 0) {
            data.cost_ratio = (data.material_cost_guideline / data.selling_price * 100);
        }

        try {
            let url, method;
            if (currentEditingId) {
                // 수정
                url = `http://127.0.0.1:8010/api/admin/meal-pricing/${currentEditingId}`;
                method = 'PUT';
            } else {
                // 추가
                url = 'http://127.0.0.1:8010/api/admin/meal-pricing';
                method = 'POST';
            }

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            if (result.success) {
                console.log('✅ 저장 성공');
                closeMealPricingModal();
                loadMealPricingData(); // 데이터 새로고침
            } else {
                alert('저장 실패: ' + result.error);
            }
        } catch (error) {
            console.error('❌ 저장 실패:', error);
            alert('저장 중 오류가 발생했습니다.');
        }
    };

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

        // 모달 외부 클릭으로 닫기
        document.getElementById('meal-pricing-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'meal-pricing-modal') {
                closeMealPricingModal();
            }
        });
    }

    // 모달 이벤트 리스너 설정 (모달이 열릴 때마다 호출)
    function setupModalEventListeners() {
        // 가격 입력 시 달성율 계산
        const sellingPriceInput = document.getElementById('edit-selling-price');
        const materialCostInput = document.getElementById('edit-material-cost');

        if (sellingPriceInput) {
            sellingPriceInput.oninput = calculateEditRatio;
        }

        if (materialCostInput) {
            materialCostInput.oninput = calculateEditRatio;
        }

        // onchange는 이미 HTML에 인라인으로 설정되어 있음
        console.log('모달 이벤트 리스너 설정 완료');
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

    // 삭제
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
    window.initEnhancedMealPricingV3 = initEnhancedMealPricingV3;

    console.log('✅ Enhanced Meal Pricing V3 Module 로드 완료');
})();