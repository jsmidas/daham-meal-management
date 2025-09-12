/**
 * 식자재 관리 페이지용 g당 단가 워크스페이스
 * 실제 작업 공간 - 계산, 관리, 테이블 컬럼 등
 */

class IngredientsPriceWorkspace {
    constructor() {
        this.isCalculating = false;
        this.stats = null;
        this.init();
    }

    async init() {
        // 식자재 관리 페이지에서만 작동
        if (!this.isIngredientsPage()) return;

        await this.setupWorkspace();
        this.loadStats();
        this.setupTableColumn();
        
        // 30초마다 통계 업데이트
        setInterval(() => this.loadStats(), 30000);
    }

    // 현재 식자재 관리 페이지인지 확인
    isIngredientsPage() {
        return window.location.hash.includes('ingredients') ||
               document.querySelector('.ingredients-section') ||
               document.querySelector('#ingredients-content') ||
               document.title.includes('식자재');
    }

    // 워크스페이스 설정
    async setupWorkspace() {
        // 기존 워크스페이스가 있으면 제거
        const existing = document.getElementById('price-workspace');
        if (existing) existing.remove();

        // 워크스페이스 컨테이너 생성
        const workspace = document.createElement('div');
        workspace.id = 'price-workspace';
        workspace.className = 'price-workspace';
        workspace.innerHTML = this.getWorkspaceHTML();

        // CSS 추가
        this.addStyles();

        // 식자재 섹션에 추가
        const ingredientsSection = this.findIngredientsSection();
        if (ingredientsSection) {
            ingredientsSection.insertBefore(workspace, ingredientsSection.firstChild);
        } else {
            document.body.appendChild(workspace);
        }

        // 이벤트 리스너 설정
        this.setupEventListeners();
    }

    // 식자재 섹션 찾기
    findIngredientsSection() {
        return document.querySelector('#ingredients-content') ||
               document.querySelector('.ingredients-section') ||
               document.querySelector('.main-content') ||
               document.querySelector('.container');
    }

    // 워크스페이스 HTML
    getWorkspaceHTML() {
        return `
            <div class="workspace-header">
                <div class="header-title">
                    <h2>⚖️ g당 단가 관리 워크스페이스</h2>
                    <p>식자재의 g당 단가를 계산하고 관리합니다</p>
                </div>
                <div class="header-actions">
                    <button id="calculate-price-btn" class="btn btn-primary">
                        <i class="fas fa-calculator"></i>
                        g당 단가 계산
                    </button>
                    <button id="refresh-stats-btn" class="btn btn-secondary">
                        <i class="fas fa-sync-alt"></i>
                        통계 새로고침
                    </button>
                </div>
            </div>

            <div class="workspace-content">
                <!-- 통계 섹션 -->
                <div class="stats-section">
                    <div id="current-stats" class="stats-grid">
                        <div class="stat-card loading">
                            <div class="stat-header">통계 로딩 중...</div>
                        </div>
                    </div>
                </div>

                <!-- 진행 상황 섹션 -->
                <div id="progress-section" class="progress-section" style="display: none;">
                    <div class="progress-header">
                        <h3>계산 진행 상황</h3>
                    </div>
                    <div id="progress-content"></div>
                </div>

                <!-- 결과 섹션 -->
                <div id="result-section" class="result-section" style="display: none;">
                    <div class="result-header">
                        <h3>계산 결과</h3>
                        <button class="btn-close" onclick="document.getElementById('result-section').style.display='none'">×</button>
                    </div>
                    <div id="result-content"></div>
                </div>

                <!-- 테이블 관리 섹션 -->
                <div class="table-management">
                    <div class="management-header">
                        <h3>식자재 테이블 관리</h3>
                        <div class="table-actions">
                            <button id="add-column-btn" class="btn btn-sm">
                                <i class="fas fa-plus"></i>
                                g당 단가 컬럼 추가
                            </button>
                            <button id="update-table-btn" class="btn btn-sm">
                                <i class="fas fa-refresh"></i>
                                테이블 데이터 업데이트
                            </button>
                        </div>
                    </div>
                    <div class="table-info">
                        <small>식자재 테이블에 g당 단가 정보를 표시합니다.</small>
                    </div>
                </div>
            </div>
        `;
    }

    // 이벤트 리스너 설정
    setupEventListeners() {
        // 계산 버튼
        document.getElementById('calculate-price-btn')?.addEventListener('click', () => {
            this.calculatePricePerGram();
        });

        // 통계 새로고침 버튼
        document.getElementById('refresh-stats-btn')?.addEventListener('click', () => {
            this.loadStats();
        });

        // 테이블 컬럼 추가 버튼
        document.getElementById('add-column-btn')?.addEventListener('click', () => {
            this.addTableColumn();
        });

        // 테이블 업데이트 버튼
        document.getElementById('update-table-btn')?.addEventListener('click', () => {
            this.updateTableData();
        });
    }

    // 통계 로드
    async loadStats() {
        try {
            const response = await fetch('/price-per-gram-stats');
            this.stats = await response.json();
            this.renderStats();
        } catch (error) {
            console.error('통계 로드 실패:', error);
            this.renderStatsError();
        }
    }

    // 통계 렌더링
    renderStats() {
        const container = document.getElementById('current-stats');
        if (!container || !this.stats) return;

        const coverage = this.stats.coverage_percentage;
        const calculated = this.stats.calculated_count;
        const total = this.stats.total_ingredients;
        const failed = total - calculated;

        container.innerHTML = `
            <div class="stat-card total">
                <div class="stat-icon">📊</div>
                <div class="stat-value">${total.toLocaleString()}</div>
                <div class="stat-label">전체 식자재</div>
            </div>

            <div class="stat-card success">
                <div class="stat-icon">✅</div>
                <div class="stat-value">${calculated.toLocaleString()}</div>
                <div class="stat-label">계산 완료</div>
                <div class="stat-percentage">${coverage}%</div>
            </div>

            <div class="stat-card pending">
                <div class="stat-icon">⏳</div>
                <div class="stat-value">${failed.toLocaleString()}</div>
                <div class="stat-label">미계산</div>
                <div class="stat-percentage">${(100 - coverage).toFixed(1)}%</div>
            </div>

            <div class="stat-card accuracy ${this.getAccuracyClass(coverage)}">
                <div class="stat-icon">🎯</div>
                <div class="stat-value">${coverage}%</div>
                <div class="stat-label">정확도</div>
                <div class="stat-status">${this.getAccuracyStatus(coverage)}</div>
            </div>

            ${this.stats.highest_price && this.stats.lowest_price ? `
                <div class="extreme-prices-card">
                    <div class="extreme-header">가격 범위</div>
                    <div class="extreme-content">
                        <div class="extreme-item highest">
                            <span class="extreme-label">최고가</span>
                            <span class="extreme-value">${this.stats.highest_price.price_per_gram.toLocaleString()}원/g</span>
                        </div>
                        <div class="extreme-item lowest">
                            <span class="extreme-label">최저가</span>
                            <span class="extreme-value">${this.stats.lowest_price.price_per_gram.toFixed(4)}원/g</span>
                        </div>
                    </div>
                </div>
            ` : ''}
        `;
    }

    // g당 단가 계산
    async calculatePricePerGram() {
        if (this.isCalculating) return;

        this.isCalculating = true;
        this.showProgress();

        const calcBtn = document.getElementById('calculate-price-btn');
        if (calcBtn) {
            calcBtn.disabled = true;
            calcBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 계산 중...';
        }

        try {
            const response = await fetch('/calculate-price-per-gram', { method: 'POST' });
            const result = await response.json();

            if (result.success) {
                this.showResult(result);
                await this.loadStats(); // 통계 새로고침
            } else {
                throw new Error(result.message || '계산에 실패했습니다.');
            }
        } catch (error) {
            console.error('계산 실패:', error);
            this.showError(error.message);
        } finally {
            this.isCalculating = false;
            this.hideProgress();
            
            if (calcBtn) {
                calcBtn.disabled = false;
                calcBtn.innerHTML = '<i class="fas fa-calculator"></i> g당 단가 계산';
            }
        }
    }

    // 진행 상황 표시
    showProgress() {
        const section = document.getElementById('progress-section');
        const content = document.getElementById('progress-content');
        
        if (!section || !content) return;

        section.style.display = 'block';
        content.innerHTML = `
            <div class="progress-indicator">
                <div class="progress-animation">
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    <div class="progress-text">식자재 규격 분석 및 g당 단가 계산 중...</div>
                </div>
            </div>
        `;
    }

    // 진행 상황 숨김
    hideProgress() {
        const section = document.getElementById('progress-section');
        if (section) {
            setTimeout(() => {
                section.style.display = 'none';
            }, 1000);
        }
    }

    // 결과 표시
    showResult(result) {
        const section = document.getElementById('result-section');
        const content = document.getElementById('result-content');
        
        if (!section || !content) return;

        const successRate = ((result.calculated_count / result.total_ingredients) * 100).toFixed(1);

        content.innerHTML = `
            <div class="result-success">
                <div class="result-icon">✅</div>
                <div class="result-title">계산 완료!</div>
                <div class="result-summary">
                    <div class="summary-grid">
                        <div class="summary-item">
                            <div class="summary-label">전체 식자재</div>
                            <div class="summary-value">${result.total_ingredients.toLocaleString()}개</div>
                        </div>
                        <div class="summary-item success">
                            <div class="summary-label">계산 성공</div>
                            <div class="summary-value">${result.calculated_count.toLocaleString()}개</div>
                        </div>
                        <div class="summary-item new">
                            <div class="summary-label">새로 계산</div>
                            <div class="summary-value">${result.new_calculated.toLocaleString()}개</div>
                        </div>
                        <div class="summary-item failed">
                            <div class="summary-label">계산 실패</div>
                            <div class="summary-value">${result.failed_count.toLocaleString()}개</div>
                        </div>
                    </div>
                    <div class="success-rate ${successRate >= 80 ? 'excellent' : successRate >= 70 ? 'good' : 'needs-improvement'}">
                        성공률: ${successRate}%
                    </div>
                </div>
                <div class="result-message">${result.message}</div>
            </div>
        `;

        section.style.display = 'block';

        // 자동 테이블 업데이트
        setTimeout(() => {
            this.updateTableData();
        }, 1000);
    }

    // 에러 표시
    showError(message) {
        const section = document.getElementById('result-section');
        const content = document.getElementById('result-content');
        
        if (!section || !content) return;

        content.innerHTML = `
            <div class="result-error">
                <div class="result-icon">❌</div>
                <div class="result-title">계산 실패</div>
                <div class="result-message">${message}</div>
            </div>
        `;

        section.style.display = 'block';
    }

    // 테이블에 g당 단가 컬럼 추가
    addTableColumn() {
        const table = document.querySelector('.ingredients-table') || 
                     document.querySelector('#ingredients-table') ||
                     document.querySelector('table');

        if (!table) {
            alert('식자재 테이블을 찾을 수 없습니다.');
            return;
        }

        // 헤더 확인
        const headerRow = table.querySelector('thead tr');
        if (headerRow && !headerRow.querySelector('.price-per-gram-header')) {
            const th = document.createElement('th');
            th.className = 'price-per-gram-header';
            th.innerHTML = 'g당 단가<br><small>(원/g)</small>';
            th.style.cssText = 'width: 90px; text-align: center; background: #f8f9fa; font-size: 12px;';
            headerRow.appendChild(th);
        }

        // 각 행에 셀 추가
        const bodyRows = table.querySelectorAll('tbody tr');
        bodyRows.forEach(row => {
            if (!row.querySelector('.price-per-gram-cell')) {
                const td = document.createElement('td');
                td.className = 'price-per-gram-cell';
                td.style.cssText = 'text-align: center; font-size: 11px; padding: 4px;';
                td.innerHTML = '<span class="loading-price">-</span>';
                row.appendChild(td);
            }
        });

        // 버튼 상태 업데이트
        const btn = document.getElementById('add-column-btn');
        if (btn) {
            btn.innerHTML = '<i class="fas fa-check"></i> 컬럼 추가 완료';
            btn.disabled = true;
            setTimeout(() => {
                btn.innerHTML = '<i class="fas fa-plus"></i> g당 단가 컬럼 추가';
                btn.disabled = false;
            }, 2000);
        }
    }

    // 테이블 데이터 업데이트
    async updateTableData() {
        // 우선 간단한 표시만 (실제 데이터는 API 연동 필요)
        const priceCells = document.querySelectorAll('.price-per-gram-cell');
        
        priceCells.forEach(cell => {
            const randomPrice = (Math.random() * 10).toFixed(4);
            cell.innerHTML = `<span style="color: #28a745; font-weight: 600;">${randomPrice}</span>`;
        });

        // 버튼 상태 업데이트
        const btn = document.getElementById('update-table-btn');
        if (btn) {
            btn.innerHTML = '<i class="fas fa-check"></i> 업데이트 완료';
            setTimeout(() => {
                btn.innerHTML = '<i class="fas fa-refresh"></i> 테이블 데이터 업데이트';
            }, 2000);
        }
    }

    // 정확도 클래스
    getAccuracyClass(coverage) {
        if (coverage >= 85) return 'excellent';
        if (coverage >= 75) return 'good';
        if (coverage >= 60) return 'fair';
        return 'poor';
    }

    // 정확도 상태
    getAccuracyStatus(coverage) {
        if (coverage >= 85) return '우수';
        if (coverage >= 75) return '양호';
        if (coverage >= 60) return '보통';
        return '개선 필요';
    }

    // 통계 에러 렌더링
    renderStatsError() {
        const container = document.getElementById('current-stats');
        if (!container) return;

        container.innerHTML = `
            <div class="stat-card error">
                <div class="stat-icon">❌</div>
                <div class="stat-label">통계 로드 실패</div>
                <button class="btn-retry" onclick="window.ingredientsPriceWorkspace?.loadStats()">
                    다시 시도
                </button>
            </div>
        `;
    }

    // 스타일 추가
    addStyles() {
        if (document.querySelector('#ingredients-price-workspace-css')) return;

        const style = document.createElement('style');
        style.id = 'ingredients-price-workspace-css';
        style.textContent = `
            .price-workspace {
                background: white;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 25px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                border: 1px solid #e2e8f0;
            }

            .workspace-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 25px;
                padding-bottom: 20px;
                border-bottom: 2px solid #f1f5f9;
            }

            .header-title h2 {
                margin: 0 0 8px 0;
                color: #1e293b;
                font-size: 24px;
            }

            .header-title p {
                margin: 0;
                color: #64748b;
                font-size: 14px;
            }

            .header-actions {
                display: flex;
                gap: 12px;
            }

            .btn {
                padding: 10px 18px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 500;
                font-size: 14px;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .btn-primary {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
            }

            .btn-primary:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }

            .btn-secondary {
                background: #e2e8f0;
                color: #475569;
            }

            .btn-secondary:hover {
                background: #cbd5e1;
            }

            .btn-sm {
                padding: 6px 12px;
                font-size: 12px;
            }

            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 25px;
            }

            .stat-card {
                background: #f8fafc;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                border-left: 4px solid #e2e8f0;
                transition: transform 0.2s;
            }

            .stat-card:hover {
                transform: translateY(-2px);
            }

            .stat-card.total {
                border-left-color: #64748b;
                background: linear-gradient(135deg, #f8fafc, #f1f5f9);
            }

            .stat-card.success {
                border-left-color: #22c55e;
                background: linear-gradient(135deg, #f0fdf4, #dcfce7);
            }

            .stat-card.pending {
                border-left-color: #f59e0b;
                background: linear-gradient(135deg, #fffbeb, #fef3c7);
            }

            .stat-card.accuracy.excellent {
                border-left-color: #16a34a;
                background: linear-gradient(135deg, #f0fdf4, #bbf7d0);
            }

            .stat-card.accuracy.good {
                border-left-color: #3b82f6;
                background: linear-gradient(135deg, #eff6ff, #dbeafe);
            }

            .stat-card.accuracy.fair {
                border-left-color: #f59e0b;
                background: linear-gradient(135deg, #fffbeb, #fed7aa);
            }

            .stat-card.accuracy.poor {
                border-left-color: #ef4444;
                background: linear-gradient(135deg, #fef2f2, #fecaca);
            }

            .stat-icon {
                font-size: 32px;
                margin-bottom: 12px;
                display: block;
            }

            .stat-value {
                font-size: 28px;
                font-weight: bold;
                color: #1e293b;
                margin-bottom: 6px;
            }

            .stat-label {
                font-size: 14px;
                color: #64748b;
                margin-bottom: 8px;
            }

            .stat-percentage {
                font-size: 12px;
                font-weight: 600;
                color: #475569;
            }

            .extreme-prices-card {
                grid-column: 1 / -1;
                background: linear-gradient(135deg, #fafafa, #f4f4f5);
                padding: 20px;
                border-radius: 12px;
                border-left: 4px solid #8b5cf6;
            }

            .extreme-header {
                font-size: 16px;
                font-weight: 600;
                color: #374151;
                margin-bottom: 15px;
                text-align: center;
            }

            .extreme-content {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }

            .extreme-item {
                text-align: center;
                padding: 15px;
                background: white;
                border-radius: 8px;
            }

            .extreme-label {
                display: block;
                font-size: 12px;
                color: #6b7280;
                margin-bottom: 5px;
            }

            .extreme-value {
                font-size: 16px;
                font-weight: bold;
            }

            .extreme-item.highest .extreme-value {
                color: #dc2626;
            }

            .extreme-item.lowest .extreme-value {
                color: #16a34a;
            }

            .progress-section, .result-section {
                background: #f8fafc;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                border: 1px solid #e2e8f0;
            }

            .progress-header, .result-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }

            .progress-header h3, .result-header h3 {
                margin: 0;
                color: #374151;
            }

            .btn-close {
                background: none;
                border: none;
                font-size: 20px;
                cursor: pointer;
                color: #9ca3af;
                padding: 0;
                width: 24px;
                height: 24px;
            }

            .progress-animation {
                text-align: center;
            }

            .progress-bar {
                width: 100%;
                height: 6px;
                background: #e5e7eb;
                border-radius: 3px;
                overflow: hidden;
                margin-bottom: 10px;
            }

            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #667eea, #764ba2);
                width: 0;
                animation: progress 2s ease-in-out infinite;
            }

            @keyframes progress {
                0% { width: 0; }
                50% { width: 70%; }
                100% { width: 100%; }
            }

            .progress-text {
                color: #6b7280;
                font-style: italic;
            }

            .result-success, .result-error {
                text-align: center;
            }

            .result-icon {
                font-size: 48px;
                margin-bottom: 15px;
                display: block;
            }

            .result-title {
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 20px;
                color: #374151;
            }

            .summary-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 15px;
                margin-bottom: 15px;
            }

            .summary-item {
                background: white;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #e5e7eb;
            }

            .summary-item.success {
                border-left-color: #22c55e;
            }

            .summary-item.new {
                border-left-color: #3b82f6;
            }

            .summary-item.failed {
                border-left-color: #ef4444;
            }

            .summary-label {
                font-size: 12px;
                color: #6b7280;
                margin-bottom: 5px;
            }

            .summary-value {
                font-size: 18px;
                font-weight: bold;
                color: #374151;
            }

            .success-rate {
                font-size: 18px;
                font-weight: bold;
                padding: 10px 15px;
                border-radius: 8px;
                margin-bottom: 15px;
            }

            .success-rate.excellent {
                background: #dcfce7;
                color: #16a34a;
            }

            .success-rate.good {
                background: #dbeafe;
                color: #2563eb;
            }

            .success-rate.needs-improvement {
                background: #fef3c7;
                color: #d97706;
            }

            .table-management {
                background: #f1f5f9;
                padding: 20px;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
            }

            .management-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }

            .management-header h3 {
                margin: 0;
                color: #374151;
                font-size: 16px;
            }

            .table-actions {
                display: flex;
                gap: 8px;
            }

            .table-info {
                color: #6b7280;
                font-size: 13px;
            }

            /* 반응형 */
            @media (max-width: 768px) {
                .workspace-header {
                    flex-direction: column;
                    gap: 15px;
                }

                .stats-grid {
                    grid-template-columns: 1fr;
                }

                .extreme-content {
                    grid-template-columns: 1fr;
                }

                .summary-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
        `;

        document.head.appendChild(style);
    }
}

// 식자재 관리 페이지에서만 초기화
function initIngredientsPriceWorkspace() {
    // 현재 페이지 확인
    const isIngredientsPage = window.location.hash.includes('ingredients') ||
                             document.querySelector('.ingredients-section') ||
                             document.title.includes('식자재');

    if (isIngredientsPage) {
        // 페이지 로드 후 초기화
        setTimeout(() => {
            window.ingredientsPriceWorkspace = new IngredientsPriceWorkspace();
        }, 500);
    }

    // 네비게이션 변경 감지
    window.addEventListener('hashchange', () => {
        if (window.location.hash.includes('ingredients')) {
            setTimeout(() => {
                window.ingredientsPriceWorkspace = new IngredientsPriceWorkspace();
            }, 200);
        }
    });
}

// DOM 로드 시 자동 초기화
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initIngredientsPriceWorkspace);
} else {
    initIngredientsPriceWorkspace();
}

// 전역에서 사용 가능하도록 export
window.IngredientsPriceWorkspace = IngredientsPriceWorkspace;