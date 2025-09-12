/**
 * Fortress Ingredients Module
 * AI-resistant ingredients management system
 */

// 모듈 정의
define('ingredients-fortress', ['navigation'], (deps) => {
    
    return {
        name: 'ingredients-fortress',
        version: '1.0.0',
        protected: true,
        
        // 내부 상태
        state: {
            ingredients: [],
            currentPage: 1,
            totalCount: 0,
            filters: {
                excludeUnpublished: false,
                excludeNoPrice: false,
                searchTerm: '',
                supplier: ''
            },
            loading: false
        },

        // 초기화
        async init() {
            console.log('🥬 Fortress Ingredients module initializing...');
            
            // 이벤트 리스너 등록
            window.Fortress.eventBus.addEventListener('moduleMessage', (e) => {
                if (e.detail.to === 'ingredients' && e.detail.message === 'activate') {
                    this.render();
                }
            });

            // API 엔드포인트 등록
            this.registerAPIEndpoints();
            
            console.log('✅ Fortress Ingredients module ready');
        },

        // API 엔드포인트 등록
        registerAPIEndpoints() {
            const gateway = window.APIGateway;
            
            // 식자재 목록 조회
            gateway.registerEndpoint('/api/admin/ingredients', async (context) => {
                const params = new URLSearchParams(context.options.body || '');
                const page = params.get('page') || 1;
                const limit = params.get('limit') || 50;
                const excludeUnpublished = params.get('exclude_unpublished') === 'true';
                const excludeNoPrice = params.get('exclude_no_price') === 'true';
                
                // 실제 API 호출
                const response = await window._originalFetch('/api/admin/ingredients?' + 
                    new URLSearchParams({
                        page,
                        limit,
                        exclude_unpublished: excludeUnpublished,
                        exclude_no_price: excludeNoPrice
                    }).toString());
                
                return await response.json();
            }, {
                method: 'GET',
                cache: true,
                cacheTTL: 30000 // 30초 캐시
            });
        },

        // 메인 렌더링
        async render() {
            const container = document.getElementById('fortress-module-container');
            
            container.innerHTML = `
                <div class="ingredients-fortress-container">
                    <div class="ingredients-header">
                        <h1>🥬 식자재 관리 (Fortress)</h1>
                        <div class="ingredients-stats">
                            <span id="ingredients-total-count">로딩 중...</span>
                        </div>
                    </div>

                    <div class="ingredients-controls">
                        <div class="ingredients-filters">
                            <div class="filter-group">
                                <label>
                                    <input type="checkbox" id="excludeUnpublished" ${this.state.filters.excludeUnpublished ? 'checked' : ''}>
                                    미게시 식자재 제외
                                </label>
                            </div>
                            <div class="filter-group">
                                <label>
                                    <input type="checkbox" id="excludeNoPrice" ${this.state.filters.excludeNoPrice ? 'checked' : ''}>
                                    입고가 없는 식자재 제외  
                                </label>
                            </div>
                            <div class="filter-group">
                                <input type="text" id="searchInput" placeholder="식자재명 검색..." 
                                       value="${this.state.filters.searchTerm}">
                            </div>
                            <div class="filter-group">
                                <button id="refreshBtn" class="btn-primary">🔄 새로고침</button>
                            </div>
                        </div>
                    </div>

                    <div class="ingredients-content">
                        <div id="ingredients-loading" class="loading-indicator" style="display: none;">
                            <div class="spinner"></div>
                            <span>데이터 로딩 중...</span>
                        </div>
                        
                        <div id="ingredients-table-container">
                            <!-- 테이블이 여기에 생성됩니다 -->
                        </div>
                        
                        <div id="ingredients-pagination">
                            <!-- 페이지네이션이 여기에 생성됩니다 -->
                        </div>
                    </div>
                </div>
            `;

            // CSS 스타일 추가
            this.injectStyles();
            
            // 이벤트 리스너 추가
            this.bindEvents();
            
            // 데이터 로드
            await this.loadIngredients();
        },

        // CSS 스타일 주입
        injectStyles() {
            if (document.getElementById('ingredients-fortress-styles')) return;
            
            const style = document.createElement('style');
            style.id = 'ingredients-fortress-styles';
            style.textContent = `
                .ingredients-fortress-container {
                    padding: 20px;
                    height: 100vh;
                    overflow-y: auto;
                    background: #f8f9fa;
                }

                .ingredients-header {
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .ingredients-header h1 {
                    margin: 0;
                    color: #333;
                }

                .ingredients-stats {
                    font-size: 1.1rem;
                    color: #666;
                }

                .ingredients-controls {
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }

                .ingredients-filters {
                    display: flex;
                    gap: 20px;
                    align-items: center;
                    flex-wrap: wrap;
                }

                .filter-group {
                    display: flex;
                    align-items: center;
                }

                .filter-group label {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    cursor: pointer;
                }

                .filter-group input[type="text"] {
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    width: 200px;
                }

                .btn-primary {
                    background: #007bff;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    cursor: pointer;
                    transition: background 0.2s;
                }

                .btn-primary:hover {
                    background: #0056b3;
                }

                .ingredients-content {
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow: hidden;
                }

                .loading-indicator {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 40px;
                    gap: 10px;
                }

                .spinner {
                    width: 20px;
                    height: 20px;
                    border: 2px solid #f3f3f3;
                    border-top: 2px solid #007bff;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }

                .ingredients-table {
                    width: 100%;
                    border-collapse: collapse;
                }

                .ingredients-table th,
                .ingredients-table td {
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #eee;
                }

                .ingredients-table th {
                    background: #f8f9fa;
                    font-weight: 600;
                    position: sticky;
                    top: 0;
                }

                .ingredients-table tr:hover {
                    background: #f8f9fa;
                }

                .fortress-protected-badge {
                    background: #ffd700;
                    color: #333;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: bold;
                }
            `;
            
            document.head.appendChild(style);
        },

        // 이벤트 바인딩
        bindEvents() {
            // 필터 변경
            document.getElementById('excludeUnpublished').addEventListener('change', (e) => {
                this.state.filters.excludeUnpublished = e.target.checked;
                this.loadIngredients();
            });

            document.getElementById('excludeNoPrice').addEventListener('change', (e) => {
                this.state.filters.excludeNoPrice = e.target.checked;
                this.loadIngredients();
            });

            document.getElementById('searchInput').addEventListener('input', (e) => {
                this.state.filters.searchTerm = e.target.value;
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => this.loadIngredients(), 500);
            });

            document.getElementById('refreshBtn').addEventListener('click', () => {
                window.APIGateway.clearCache();
                this.loadIngredients();
            });
        },

        // 식자재 데이터 로드
        async loadIngredients() {
            if (this.state.loading) return;
            
            this.state.loading = true;
            document.getElementById('ingredients-loading').style.display = 'flex';
            
            try {
                const params = new URLSearchParams({
                    page: this.state.currentPage,
                    limit: 200000, // 대용량 데이터 로드
                    exclude_unpublished: this.state.filters.excludeUnpublished,
                    exclude_no_price: this.state.filters.excludeNoPrice
                });

                const response = await window._originalFetch('/api/admin/ingredients?' + params.toString());
                const data = await response.json();
                
                if (data.status === 'success') {
                    this.state.ingredients = data.ingredients;
                    this.state.totalCount = data.total_count;
                    
                    this.renderTable();
                    this.updateStats();
                } else {
                    throw new Error(data.message || 'Failed to load ingredients');
                }
                
            } catch (error) {
                console.error('❌ Failed to load ingredients:', error);
                this.showError('식자재 데이터를 불러올 수 없습니다: ' + error.message);
            } finally {
                this.state.loading = false;
                document.getElementById('ingredients-loading').style.display = 'none';
            }
        },

        // 테이블 렌더링
        renderTable() {
            const container = document.getElementById('ingredients-table-container');
            
            if (!this.state.ingredients.length) {
                container.innerHTML = '<div style="padding: 40px; text-align: center; color: #666;">표시할 식자재가 없습니다.</div>';
                return;
            }

            // 검색 필터 적용
            let filteredIngredients = this.state.ingredients;
            if (this.state.filters.searchTerm) {
                const term = this.state.filters.searchTerm.toLowerCase();
                filteredIngredients = this.state.ingredients.filter(item => 
                    item.ingredient_name?.toLowerCase().includes(term) ||
                    item.specification?.toLowerCase().includes(term) ||
                    item.supplier_name?.toLowerCase().includes(term)
                );
            }

            const tableHTML = `
                <div style="overflow-x: auto;">
                    <table class="ingredients-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>식자재명</th>
                                <th>규격</th>
                                <th>단위</th>
                                <th>협력업체</th>
                                <th>입고단가</th>
                                <th>게시상태</th>
                                <th>등록일</th>
                                <th>보호</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${filteredIngredients.slice(0, 1000).map(item => `
                                <tr data-id="${item.id}">
                                    <td>${item.id}</td>
                                    <td><strong>${this.escapeHtml(item.ingredient_name || '')}</strong></td>
                                    <td>${this.escapeHtml(item.specification || '')}</td>
                                    <td>${this.escapeHtml(item.unit || '')}</td>
                                    <td>${this.escapeHtml(item.supplier_name || '')}</td>
                                    <td>${item.purchase_price ? '₩' + Number(item.purchase_price).toLocaleString() : '-'}</td>
                                    <td>
                                        ${item.posting_status ? 
                                            '<span style="color: green;">✅ 게시</span>' : 
                                            '<span style="color: orange;">⏳ 미게시</span>'
                                        }
                                    </td>
                                    <td>${item.created_at ? new Date(item.created_at).toLocaleDateString() : '-'}</td>
                                    <td><span class="fortress-protected-badge">🛡️ 보호됨</span></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                
                ${filteredIngredients.length > 1000 ? 
                    `<div style="padding: 20px; text-align: center; background: #fff3cd; color: #856404; border-top: 1px solid #eee;">
                        ⚠️ 성능상 상위 1,000개만 표시됩니다. (전체: ${filteredIngredients.length.toLocaleString()}개)
                    </div>` : ''
                }
            `;
            
            container.innerHTML = tableHTML;
        },

        // 통계 업데이트
        updateStats() {
            const statsElement = document.getElementById('ingredients-total-count');
            statsElement.textContent = `총 ${this.state.totalCount.toLocaleString()}개 식자재`;
        },

        // HTML 이스케이프
        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        // 오류 표시
        showError(message) {
            const container = document.getElementById('ingredients-table-container');
            container.innerHTML = `
                <div style="padding: 40px; text-align: center; color: #dc3545;">
                    <h3>❌ 오류 발생</h3>
                    <p>${message}</p>
                    <button onclick="require('ingredients-fortress').loadIngredients()" class="btn-primary">
                        다시 시도
                    </button>
                </div>
            `;
        },

        // 모듈 정리
        destroy() {
            // 스타일 제거
            const style = document.getElementById('ingredients-fortress-styles');
            if (style) style.remove();
            
            // 타이머 정리
            if (this.searchTimeout) {
                clearTimeout(this.searchTimeout);
            }
            
            console.log('🥬 Fortress Ingredients module destroyed');
        }
    };
});

console.log('🥬 Fortress Ingredients Module Loaded');