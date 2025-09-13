// 식단가 관리 - 향상된 버전
(function() {
    'use strict';

    console.log('💰 Enhanced Meal Pricing Module Loading...');

    async function initEnhancedMealPricing() {
        console.log('🚀 Enhanced Meal Pricing 초기화 시작');

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
                            <div class="stat-value" id="avg-selling-price">₩0</div>
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
                    <div class="search-container">
                        <input type="text" id="meal-pricing-search" class="search-input" placeholder="사업장명 또는 식단명으로 검색...">
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
                                <th style="width: 12%;">식단계획</th>
                                <th style="width: 8%;">끼니</th>
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

        // 데이터 로드
        await loadMealPricingData();
    }

    // 스타일 추가
    function addMealPricingStyles() {
        if (document.getElementById('meal-pricing-styles')) return;

        const style = document.createElement('style');
        style.id = 'meal-pricing-styles';
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

            .search-container {
                flex: 1;
                max-width: 400px;
            }

            .search-input {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
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

            /* 달성율 표시 */
            .ratio-good {
                color: #28a745;
                font-weight: 600;
            }

            .ratio-warning {
                color: #ffc107;
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

    // 데이터 로드
    async function loadMealPricingData() {
        console.log('📊 식단가 데이터 로드 시작');

        try {
            const response = await fetch('http://127.0.0.1:8010/api/admin/meal-pricing');
            const data = await response.json();

            console.log('✅ 데이터 로드 성공:', data);

            if (data.success && data.meal_pricing) {
                updateStatistics(data.statistics || {});
                displayMealPricing(data.meal_pricing);
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

        const avgPrice = stats.avg_selling_price || 0;
        document.getElementById('avg-selling-price').textContent =
            '₩' + Number(avgPrice).toLocaleString();

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

            const ratio = pricing.cost_ratio || 0;
            let ratioClass = 'ratio-good';
            if (ratio > 55) ratioClass = 'ratio-danger';
            else if (ratio > 50) ratioClass = 'ratio-warning';

            return `
                <tr onclick="openEditMealPricingModal(${pricing.id})" data-id="${pricing.id}">
                    <td>${pricing.location_name || '-'}</td>
                    <td>${pricing.meal_plan_type || '-'}</td>
                    <td>${pricing.meal_type || '-'}</td>
                    <td>${pricing.plan_name || '-'}</td>
                    <td style="font-size: 11px;">${startDate}<br>~${endDate}</td>
                    <td class="text-right">₩${Number(pricing.selling_price || 0).toLocaleString()}</td>
                    <td class="text-right">₩${Number(pricing.material_cost_guideline || 0).toLocaleString()}</td>
                    <td class="text-center">
                        <span class="${ratioClass}">${ratio.toFixed(1)}%</span>
                    </td>
                    <td class="text-center">
                        ${pricing.is_active ?
                            '<span class="badge badge-active">활성</span>' :
                            '<span class="badge badge-inactive">비활성</span>'}
                    </td>
                    <td class="text-center" onclick="event.stopPropagation()">
                        <button class="btn btn-small btn-edit" onclick="editMealPricing(${pricing.id})">수정</button>
                        <button class="btn btn-small btn-delete" onclick="deleteMealPricing(${pricing.id})">삭제</button>
                    </td>
                </tr>
            `;
        }).join('');

        console.log('✅ 식단가 표시 완료');
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
    window.initEnhancedMealPricing = initEnhancedMealPricing;

    window.openAddMealPricingModal = function() {
        console.log('새 식단표 추가 모달 열기');
        // TODO: 모달 구현
        alert('새 식단표 추가 기능은 준비 중입니다.');
    };

    window.openEditMealPricingModal = function(id) {
        console.log('식단표 수정 모달 열기:', id);
        // TODO: 모달 구현
        alert(`식단표 수정 기능은 준비 중입니다. (ID: ${id})`);
    };

    window.editMealPricing = function(id) {
        openEditMealPricingModal(id);
    };

    window.deleteMealPricing = function(id) {
        if (confirm('정말로 이 식단표를 삭제하시겠습니까?')) {
            console.log('식단표 삭제:', id);
            // TODO: 삭제 API 호출
            alert(`식단표 삭제 기능은 준비 중입니다. (ID: ${id})`);
        }
    };

    console.log('✅ Enhanced Meal Pricing Module 로드 완료');
})();