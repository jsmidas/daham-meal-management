/**
 * 식재료 관리 모듈
 * - 식재료 CRUD 작업
 * - 식재료 검색 및 필터링
 * - 식재료 재고 관리
 */

window.IngredientsModule = {
    currentPage: 1,
    pageSize: 20,
    totalPages: 0,
    editingIngredientId: null,

    async load() {
        console.log('🥬 Ingredients Module 로딩 시작...');
        await this.render();
        await this.loadIngredients();
        this.setupEventListeners();
        console.log('🥬 Ingredients Module 로드됨');
    },

    async render() {
        const container = document.getElementById('ingredients-module');
        if (!container) return;

        container.innerHTML = `
            <style>
            .ingredients-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }

            .ingredients-header {
                background: white;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                margin-bottom: 25px;
            }

            .ingredients-header h1 {
                margin: 0 0 10px 0;
                color: #2c3e50;
                font-size: 28px;
                font-weight: 600;
            }

            .ingredients-header p {
                margin: 0;
                color: #7f8c8d;
                font-size: 16px;
            }

            .ingredients-toolbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                gap: 15px;
                flex-wrap: wrap;
            }

            .search-box {
                display: flex;
                align-items: center;
                gap: 10px;
                flex: 1;
                max-width: 400px;
            }

            .search-box input {
                flex: 1;
                padding: 12px 15px;
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                font-size: 14px;
                transition: border-color 0.3s;
            }

            .search-box input:focus {
                outline: none;
                border-color: #667eea;
            }

            .ingredients-content {
                background: white;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                overflow: hidden;
            }

            .ingredients-table {
                width: 100%;
                border-collapse: collapse;
                margin: 0;
            }

            .ingredients-table th,
            .ingredients-table td {
                padding: 15px;
                text-align: left;
                border-bottom: 1px solid #f1f3f4;
                vertical-align: middle;
            }

            .ingredients-table th {
                background: #f8f9fa;
                font-weight: 600;
                color: #333;
            }

            .ingredients-table tr:hover {
                background: #f8f9fa;
            }

            .loading-cell {
                text-align: center;
                color: #666;
                font-style: italic;
            }

            .btn {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 500;
                text-decoration: none;
                display: inline-block;
            }

            .btn-primary {
                background: #667eea;
                color: white;
            }

            .btn-secondary {
                background: #6c757d;
                color: white;
            }

            .btn-danger {
                background: #dc3545;
                color: white;
            }

            .btn-warning {
                background: #ffc107;
                color: #333;
            }

            .btn:hover {
                opacity: 0.9;
            }

            .btn-sm {
                padding: 4px 8px;
                font-size: 12px;
            }

            .stock-badge {
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
            }

            .stock-high {
                background: #d4edda;
                color: #155724;
            }

            .stock-medium {
                background: #fff3cd;
                color: #856404;
            }

            .stock-low {
                background: #f8d7da;
                color: #721c24;
            }

            .modal {
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
            }

            .modal-content {
                background: white;
                margin: 5% auto;
                padding: 0;
                border-radius: 8px;
                width: 90%;
                max-width: 600px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }

            .modal-header {
                padding: 20px;
                border-bottom: 1px solid #eee;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .modal-close {
                font-size: 28px;
                font-weight: bold;
                color: #aaa;
                cursor: pointer;
            }

            .modal-close:hover {
                color: #000;
            }

            .modal-body {
                padding: 20px;
            }

            .form-row {
                display: flex;
                gap: 15px;
                align-items: flex-end;
            }

            .form-group {
                margin-bottom: 15px;
                flex: 1;
            }

            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: 500;
                color: #333;
            }

            .form-group input,
            .form-group select,
            .form-group textarea {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }

            .form-group textarea {
                height: 80px;
                resize: vertical;
            }

            .form-actions {
                display: flex;
                justify-content: flex-end;
                gap: 10px;
                margin-top: 20px;
            }

            .pagination {
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
                gap: 10px;
            }

            .pagination button {
                padding: 8px 12px;
                border: 1px solid #ddd;
                background: white;
                cursor: pointer;
                border-radius: 4px;
            }

            .pagination button:hover {
                background: #f8f9fa;
            }

            .pagination button.active {
                background: #667eea;
                color: white;
                border-color: #667eea;
            }

            .pagination button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }

            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }

            .stat-card h3 {
                margin: 0 0 10px 0;
                font-size: 24px;
                color: #667eea;
            }

            .stat-card p {
                margin: 0;
                color: #666;
                font-size: 14px;
            }

            .price-cell {
                text-align: right;
                font-weight: 500;
            }

            .quantity-cell {
                text-align: center;
            }
            </style>

            <div class="ingredients-container">
                <!-- 헤더 -->
                <div class="ingredients-header">
                    <h1>🥬 식재료 관리</h1>
                    <p>식재료 정보를 등록하고 재고를 관리합니다</p>
                </div>

                <!-- 통계 -->
                <div class="stats-grid" id="ingredients-stats">
                    <div class="stat-card">
                        <h3 id="total-ingredients">-</h3>
                        <p>전체 식재료</p>
                    </div>
                    <div class="stat-card">
                        <h3 id="low-stock-ingredients">-</h3>
                        <p>재고 부족</p>
                    </div>
                    <div class="stat-card">
                        <h3 id="total-value">-</h3>
                        <p>총 재고 가치</p>
                    </div>
                </div>

                <!-- 툴바 -->
                <div class="ingredients-toolbar">
                    <div class="search-box">
                        <input type="text" id="ingredient-search" placeholder="식재료명, 분류로 검색...">
                        <button class="btn btn-secondary" onclick="IngredientsModule.searchIngredients()">🔍</button>
                    </div>
                    <button class="btn btn-primary" onclick="IngredientsModule.showCreateModal()">+ 새 식재료</button>
                </div>

                <!-- 식재료 목록 -->
                <div class="ingredients-content">
                    <table class="ingredients-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>식재료명</th>
                                <th>분류</th>
                                <th>단위</th>
                                <th>현재고</th>
                                <th>단가</th>
                                <th>총가치</th>
                                <th>재고상태</th>
                                <th>작업</th>
                            </tr>
                        </thead>
                        <tbody id="ingredients-table-body">
                            <tr>
                                <td colspan="9" class="loading-cell">식재료 목록을 불러오는 중...</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <!-- 페이지네이션 -->
                    <div class="pagination" id="ingredients-pagination">
                        <!-- 페이지네이션 버튼들이 여기에 동적으로 생성됩니다 -->
                    </div>
                </div>
            </div>

            <!-- 식재료 생성/수정 모달 -->
            <div id="ingredient-modal" class="modal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 id="modal-title">새 식재료</h3>
                        <span class="modal-close" onclick="IngredientsModule.closeModal()">&times;</span>
                    </div>
                    <div class="modal-body">
                        <form id="ingredient-form" onsubmit="IngredientsModule.saveIngredient(event)">
                            <div class="form-group">
                                <label for="name">식재료명 *</label>
                                <input type="text" id="name" name="name" required>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="category">분류</label>
                                    <select id="category" name="category">
                                        <option value="채소류">채소류</option>
                                        <option value="육류">육류</option>
                                        <option value="수산물">수산물</option>
                                        <option value="곡물류">곡물류</option>
                                        <option value="조미료">조미료</option>
                                        <option value="유제품">유제품</option>
                                        <option value="기타">기타</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label for="unit">단위</label>
                                    <select id="unit" name="unit">
                                        <option value="kg">kg</option>
                                        <option value="g">g</option>
                                        <option value="개">개</option>
                                        <option value="포">포</option>
                                        <option value="박스">박스</option>
                                        <option value="L">L</option>
                                        <option value="ml">ml</option>
                                    </select>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="current_stock">현재고</label>
                                    <input type="number" id="current_stock" name="current_stock" step="0.1" min="0" value="0">
                                </div>
                                <div class="form-group">
                                    <label for="unit_price">단가 (원)</label>
                                    <input type="number" id="unit_price" name="unit_price" step="0.01" min="0" value="0">
                                </div>
                                <div class="form-group">
                                    <label for="minimum_stock">최소 재고</label>
                                    <input type="number" id="minimum_stock" name="minimum_stock" step="0.1" min="0" value="0">
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="supplier_info">공급업체</label>
                                <input type="text" id="supplier_info" name="supplier_info" placeholder="공급업체 정보">
                            </div>
                            <div class="form-group">
                                <label for="notes">메모</label>
                                <textarea id="notes" name="notes" placeholder="추가 메모..."></textarea>
                            </div>
                            <div class="form-actions">
                                <button type="submit" class="btn btn-primary">저장</button>
                                <button type="button" class="btn btn-secondary" onclick="IngredientsModule.closeModal()">취소</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;
    },

    setupEventListeners() {
        // 검색 엔터키 처리
        const searchInput = document.getElementById('ingredient-search');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchIngredients();
                }
            });
        }

        // 모달 외부 클릭시 닫기
        const modal = document.getElementById('ingredient-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal();
                }
            });
        }
    },

    async loadIngredients() {
        try {
            const search = document.getElementById('ingredient-search')?.value || '';
            
            console.log(`Loading ingredients - page: ${this.currentPage}, search: "${search}"`);
            
            const response = await apiGet(`/api/admin/ingredients?page=${this.currentPage}&limit=${this.pageSize}&search=${encodeURIComponent(search)}`);
            
            console.log('Ingredients response:', response);
            
            if (response.success) {
                this.renderIngredients(response.ingredients || []);
                this.updatePagination(response.total, response.page, response.limit);
                await this.loadIngredientStats();
            } else {
                showMessage('식재료 목록을 불러올 수 없습니다.', 'error');
                this.renderIngredients([]);
            }
        } catch (error) {
            console.error('식재료 로드 중 오류:', error);
            console.error('Error message:', error.message);
            console.error('Error stack:', error.stack);
            showMessage('식재료 목록을 불러오는 중 오류가 발생했습니다.', 'error');
            this.renderIngredients([]);
        }
    },

    async loadIngredientStats() {
        try {
            const response = await apiGet('/api/admin/ingredient-stats');
            if (response.success) {
                const stats = response.stats;
                document.getElementById('total-ingredients').textContent = stats.total_ingredients || 0;
                document.getElementById('low-stock-ingredients').textContent = stats.low_stock_ingredients || 0;
                document.getElementById('total-value').textContent = 
                    stats.total_value ? `₩${Number(stats.total_value).toLocaleString()}` : '₩0';
            }
        } catch (error) {
            console.error('식재료 통계 로드 중 오류:', error);
        }
    },

    renderIngredients(ingredients) {
        const tbody = document.getElementById('ingredients-table-body');
        if (!tbody) return;

        if (ingredients.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="loading-cell">등록된 식재료가 없습니다.</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = ingredients.map(ingredient => {
            const totalValue = (ingredient.current_stock || 0) * (ingredient.unit_price || 0);
            const stockLevel = this.getStockLevel(ingredient.current_stock, ingredient.minimum_stock);
            
            return `
                <tr>
                    <td>${ingredient.id}</td>
                    <td><strong>${ingredient.name}</strong></td>
                    <td>${ingredient.category || '-'}</td>
                    <td>${ingredient.unit || '-'}</td>
                    <td class="quantity-cell">${ingredient.current_stock || 0}</td>
                    <td class="price-cell">₩${Number(ingredient.unit_price || 0).toLocaleString()}</td>
                    <td class="price-cell">₩${Number(totalValue).toLocaleString()}</td>
                    <td>
                        <span class="stock-badge ${stockLevel.class}">${stockLevel.text}</span>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-warning" onclick="IngredientsModule.editIngredient(${ingredient.id})">수정</button>
                        <button class="btn btn-sm btn-danger" onclick="IngredientsModule.deleteIngredient(${ingredient.id})">삭제</button>
                    </td>
                </tr>
            `;
        }).join('');
    },

    getStockLevel(currentStock, minimumStock) {
        const current = Number(currentStock || 0);
        const minimum = Number(minimumStock || 0);
        
        if (minimum === 0) {
            return { class: 'stock-high', text: '정상' };
        }
        
        if (current <= minimum) {
            return { class: 'stock-low', text: '부족' };
        } else if (current <= minimum * 2) {
            return { class: 'stock-medium', text: '보통' };
        } else {
            return { class: 'stock-high', text: '충분' };
        }
    },

    updatePagination(total, page, limit) {
        this.totalPages = Math.ceil(total / limit);
        this.currentPage = page;

        const paginationContainer = document.getElementById('ingredients-pagination');
        if (!paginationContainer) return;

        let paginationHTML = '';

        // 이전 페이지
        paginationHTML += `
            <button ${this.currentPage <= 1 ? 'disabled' : ''} onclick="IngredientsModule.goToPage(${this.currentPage - 1})">
                이전
            </button>
        `;

        // 페이지 번호들
        for (let i = Math.max(1, this.currentPage - 2); i <= Math.min(this.totalPages, this.currentPage + 2); i++) {
            paginationHTML += `
                <button class="${i === this.currentPage ? 'active' : ''}" onclick="IngredientsModule.goToPage(${i})">
                    ${i}
                </button>
            `;
        }

        // 다음 페이지
        paginationHTML += `
            <button ${this.currentPage >= this.totalPages ? 'disabled' : ''} onclick="IngredientsModule.goToPage(${this.currentPage + 1})">
                다음
            </button>
        `;

        paginationContainer.innerHTML = paginationHTML;
    },

    goToPage(page) {
        if (page >= 1 && page <= this.totalPages) {
            this.currentPage = page;
            this.loadIngredients();
        }
    },

    searchIngredients() {
        this.currentPage = 1;
        this.loadIngredients();
    },

    showCreateModal() {
        document.getElementById('modal-title').textContent = '새 식재료';
        document.getElementById('ingredient-form').reset();
        
        // 기본값 설정
        document.getElementById('category').value = '채소류';
        document.getElementById('unit').value = 'kg';
        
        document.getElementById('ingredient-modal').style.display = 'block';
        this.editingIngredientId = null;
    },

    closeModal() {
        document.getElementById('ingredient-modal').style.display = 'none';
        document.getElementById('ingredient-form').reset();
        this.editingIngredientId = null;
    },

    async saveIngredient(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const ingredientData = {
            name: formData.get('name'),
            category: formData.get('category'),
            unit: formData.get('unit'),
            current_stock: parseFloat(formData.get('current_stock')) || 0,
            unit_price: parseFloat(formData.get('unit_price')) || 0,
            minimum_stock: parseFloat(formData.get('minimum_stock')) || 0,
            supplier_info: formData.get('supplier_info'),
            notes: formData.get('notes')
        };

        try {
            let response;
            if (this.editingIngredientId) {
                response = await apiPut(`/api/admin/ingredients/${this.editingIngredientId}`, ingredientData);
            } else {
                console.log('Sending ingredient data:', ingredientData);
                response = await apiPost('/api/admin/ingredients', ingredientData);
            }

            if (response.success !== false) {
                showMessage(this.editingIngredientId ? '식재료가 수정되었습니다.' : '식재료가 추가되었습니다.', 'success');
                this.closeModal();
                this.loadIngredients();
            } else {
                showMessage(response.message || '저장 중 오류가 발생했습니다.', 'error');
            }
        } catch (error) {
            console.error('식재료 저장 중 오류:', error);
            
            if (error.message.includes('422')) {
                showMessage('입력 데이터를 확인해 주세요.', 'error');
            } else if (error.message.includes('400')) {
                showMessage('이미 존재하는 식재료명입니다.', 'error');
            } else {
                showMessage('식재료 저장 중 오류가 발생했습니다.', 'error');
            }
        }
    },

    async editIngredient(ingredientId) {
        try {
            const response = await apiGet(`/api/admin/ingredients/${ingredientId}`);
            
            if (response.success !== false) {
                const ingredient = response.ingredient || response;
                
                document.getElementById('modal-title').textContent = '식재료 수정';
                document.getElementById('name').value = ingredient.name;
                document.getElementById('category').value = ingredient.category || '채소류';
                document.getElementById('unit').value = ingredient.unit || 'kg';
                document.getElementById('current_stock').value = ingredient.current_stock || 0;
                document.getElementById('unit_price').value = ingredient.unit_price || 0;
                document.getElementById('minimum_stock').value = ingredient.minimum_stock || 0;
                document.getElementById('supplier_info').value = ingredient.supplier_info || '';
                document.getElementById('notes').value = ingredient.notes || '';
                
                this.editingIngredientId = ingredientId;
                document.getElementById('ingredient-modal').style.display = 'block';
            } else {
                showMessage('식재료 정보를 불러올 수 없습니다.', 'error');
            }
        } catch (error) {
            console.error('식재료 로드 중 오류:', error);
            showMessage('식재료 정보를 불러오는 중 오류가 발생했습니다.', 'error');
        }
    },

    async deleteIngredient(ingredientId) {
        if (!confirm('정말로 이 식재료를 삭제하시겠습니까?')) {
            return;
        }

        try {
            const response = await apiDelete(`/api/admin/ingredients/${ingredientId}`);
            
            if (response.success !== false) {
                showMessage('식재료가 삭제되었습니다.', 'success');
                this.loadIngredients();
            } else {
                showMessage('식재료 삭제 중 오류가 발생했습니다.', 'error');
            }
        } catch (error) {
            console.error('식재료 삭제 중 오류:', error);
            showMessage('식재료 삭제 중 오류가 발생했습니다.', 'error');
        }
    }
};

console.log('🥬 Ingredients Module 정의됨');
    uploadSection.style.display = isVisible ? 'none' : 'block';
    
    if (!isVisible) {
        showNotification('📁 파일 업로드 섹션이 열렸습니다.', 'info');
    }
}

// 양식 다운로드
function downloadTemplate() {
    try {
        // 샘플 Excel 파일 다운로드 로직
        const link = document.createElement('a');
        link.href = '/static/sample data/food_sample.xls';
        link.download = '식자재_업로드_양식_샘플.xls';
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // 다운로드 성공 메시지
        showNotification('📋 양식 다운로드가 시작되었습니다.', 'success');
    } catch (error) {
        console.error('양식 다운로드 실패:', error);
        showNotification('❌ 양식 다운로드에 실패했습니다.', 'error');
    }
}

// 업로드 결과 조회 표시
function showUploadHistory() {
    const historySection = document.getElementById('upload-history-section');
    const uploadSection = document.getElementById('upload-section');
    
    if (!historySection) return;
    
    // 다른 섹션 숨기기
    if (uploadSection && uploadSection.style.display !== 'none') {
        uploadSection.style.display = 'none';
    }
    
    historySection.style.display = 'block';
    loadUploadHistory();
    showNotification('📊 업로드 결과를 조회합니다.', 'info');
}

// 업로드 결과 조회 숨기기
function hideUploadHistory() {
    const historySection = document.getElementById('upload-history-section');
    const detailsSection = document.getElementById('upload-details-section');
    
    if (historySection) historySection.style.display = 'none';
    if (detailsSection) detailsSection.style.display = 'none';
}

// 파일 선택 처리
function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    processSelectedFiles(files);
}

// 드래그 오버 처리
function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.style.borderColor = '#007bff';
    event.currentTarget.style.backgroundColor = '#e7f3ff';
}

// 드래그 떠남 처리
function handleDragLeave(event) {
    event.preventDefault();
    event.currentTarget.style.borderColor = '#4a90e2';
    event.currentTarget.style.backgroundColor = '#f8f9fa';
}

// 파일 드롭 처리
function handleFileDrop(event) {
    event.preventDefault();
    event.currentTarget.style.borderColor = '#4a90e2';
    event.currentTarget.style.backgroundColor = '#f8f9fa';
    
    const files = Array.from(event.dataTransfer.files);
    processSelectedFiles(files);
}

// 선택된 파일 처리
function processSelectedFiles(files) {
    const validFiles = files.filter(file => {
        const isExcel = file.type === 'application/vnd.ms-excel' || 
                       file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                       file.name.endsWith('.xls') || file.name.endsWith('.xlsx');
        const isValidSize = file.size <= 10 * 1024 * 1024; // 10MB
        
        if (!isExcel) {
            showNotification(`❌ ${file.name}: Excel 파일만 업로드 가능합니다.`, 'error');
            return false;
        }
        
        if (!isValidSize) {
            showNotification(`❌ ${file.name}: 파일 크기는 10MB 이하여야 합니다.`, 'error');
            return false;
        }
        
        return true;
    });
    
    if (validFiles.length > 0) {
        uploadedFiles = validFiles;
        updateFileList();
        enableUploadButton();
        showNotification(`✅ ${validFiles.length}개 파일이 선택되었습니다.`, 'success');
    }
}

// 파일 선택 처리 (input change 이벤트용)
function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    processSelectedFiles(files);
}

// 파일 초기화
function clearFiles() {
    uploadedFiles = [];
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.value = '';
    }
    updateFileList();
    disableUploadButton();
    showNotification('📁 선택된 파일이 초기화되었습니다.', 'info');
}

// 파일 목록 업데이트
function updateFileList() {
    const fileListDiv = document.getElementById('selected-files-list');
    if (!fileListDiv) {
        console.log('선택된 파일들:', uploadedFiles.map(f => f.name));
        return;
    }
    
    if (uploadedFiles.length === 0) {
        fileListDiv.innerHTML = '<p style="color: #666; text-align: center; padding: 20px;">선택된 파일이 없습니다.</p>';
        return;
    }
    
    const listHTML = uploadedFiles.map((file, index) => `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 8px; background: #f8f9fa;">
            <div>
                <strong>${file.name}</strong>
                <small style="color: #666; margin-left: 10px;">(${(file.size / 1024 / 1024).toFixed(2)} MB)</small>
            </div>
            <button onclick="removeFile(${index})" style="background: #dc3545; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 12px;">
                삭제
            </button>
        </div>
    `).join('');
    
    fileListDiv.innerHTML = listHTML;
}

// 개별 파일 삭제
function removeFile(index) {
    uploadedFiles.splice(index, 1);
    updateFileList();
    if (uploadedFiles.length === 0) {
        disableUploadButton();
    } else {
        enableUploadButton();
    }
}

// 업로드 버튼 활성화
function enableUploadButton() {
    const uploadBtn = document.getElementById('upload-btn');
    if (uploadBtn) {
        uploadBtn.disabled = false;
        uploadBtn.style.opacity = '1';
    }
}

// 업로드 버튼 비활성화
function disableUploadButton() {
    const uploadBtn = document.getElementById('upload-btn');
    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.style.opacity = '0.5';
    }
}

// 파일 업로드 실행
async function uploadFiles() {
    console.log('★★★ MODULAR uploadFiles 함수 호출됨 - 실제 서버 업로드 시작 ★★★');
    if (uploadedFiles.length === 0) {
        showNotification('❌ 업로드할 파일을 선택해주세요.', 'error');
        return;
    }
    
    const progressSection = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    
    try {
        // 진행률 표시
        if (progressSection) progressSection.style.display = 'block';
        
        let totalProcessedRows = 0;
        let totalSuccessRows = 0;
        let totalFailedRows = 0;
        const uploadResults = [];
        
        for (let i = 0; i < uploadedFiles.length; i++) {
            const file = uploadedFiles[i];
            const progress = ((i + 1) / uploadedFiles.length) * 100;
            
            if (progressFill) progressFill.style.width = progress + '%';
            if (progressText) progressText.textContent = `업로드 중... ${file.name} (${i + 1}/${uploadedFiles.length})`;
            
            // 실제 서버 업로드
            const result = await uploadFileToServer(file);
            
            // 결과 누적
            totalProcessedRows += result.processedRows;
            totalSuccessRows += result.successRows;
            totalFailedRows += result.failedRows;
            uploadResults.push({
                fileName: file.name,
                success: true,
                processedRows: result.processedRows,
                successRows: result.successRows,
                failedRows: result.failedRows
            });
        }
        
        // 업로드 완료 처리
        if (progressText) {
            progressText.textContent = `업로드 완료! 총 ${totalProcessedRows.toLocaleString()}개 식자재 데이터 처리됨 (성공: ${totalSuccessRows.toLocaleString()})`;
        }
        
        // 대량 업로드 결과 표시
        displayBulkUploadResults(uploadResults, uploadedFiles.length, totalSuccessRows, 0);
        
        showNotification(`✅ ${uploadedFiles.length}개 파일 업로드 완료! 총 ${totalProcessedRows.toLocaleString()}개 식자재 데이터가 처리되었습니다.`, 'success');
        
        // 초기화 (3초 후)
        setTimeout(() => {
            uploadedFiles = [];
            updateFileList();
            disableUploadButton();
            if (progressSection) progressSection.style.display = 'none';
        }, 3000);
        
        // 업로드 히스토리 갱신
        loadUploadHistory();
        
    } catch (error) {
        console.error('업로드 실패:', error);
        showNotification('❌ 파일 업로드 중 오류가 발생했습니다.', 'error');
        
        if (progressSection) progressSection.style.display = 'none';
    }
}

// 대용량 업로드 결과 표시 (18,000개 이상 식자재 데이터 처리용)
function displayBulkUploadResults(uploadResults, totalProcessed, totalSuccess, totalFailed) {
    // 상세 결과 섹션이 있는지 확인하고 없으면 생성
    let resultsSection = document.getElementById('bulk-upload-results');
    if (!resultsSection) {
        resultsSection = document.createElement('div');
        resultsSection.id = 'bulk-upload-results';
        resultsSection.style.cssText = 'margin-top: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);';
        
        const uploadSection = document.getElementById('upload-section');
        if (uploadSection) {
            uploadSection.appendChild(resultsSection);
        }
    }
    
    // 요약 통계
    const summaryHTML = `
        <div style="padding: 20px; border-bottom: 1px solid #eee;">
            <h3 style="margin: 0 0 15px 0; color: #007bff;">📊 대용량 업로드 결과</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
                <div style="background: #e7f3ff; padding: 15px; border-radius: 5px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #007bff;">${totalProcessed}</div>
                    <div style="font-size: 14px; color: #666;">처리된 파일</div>
                </div>
                <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #28a745;">${totalSuccess.toLocaleString()}</div>
                    <div style="font-size: 14px; color: #666;">성공한 식자재</div>
                </div>
                <div style="background: ${totalFailed > 0 ? '#ffe6e6' : '#f8f9fa'}; padding: 15px; border-radius: 5px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: ${totalFailed > 0 ? '#dc3545' : '#666'};">${totalFailed}</div>
                    <div style="font-size: 14px; color: #666;">실패한 파일</div>
                </div>
            </div>
        </div>
    `;
    
    // 파일별 상세 결과
    let detailsHTML = '';
    if (uploadResults.length > 0) {
        detailsHTML = `
            <div style="padding: 20px;">
                <h4 style="margin: 0 0 15px 0;">📋 파일별 처리 결과</h4>
                <div style="max-height: 300px; overflow-y: auto;">
                    ${uploadResults.map(result => {
                        const isSuccess = result.success;
                        const statusColor = isSuccess ? '#28a745' : '#dc3545';
                        const statusIcon = isSuccess ? '✅' : '❌';
                        
                        return `
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border: 1px solid #eee; border-radius: 4px; margin-bottom: 8px; background: ${isSuccess ? '#f8fff8' : '#fff8f8'};">
                                <div style="flex: 1;">
                                    <div style="font-weight: 500;">${statusIcon} ${result.fileName}</div>
                                    ${isSuccess 
                                        ? `<small style="color: #666;">성공: ${(result.successRows || 0).toLocaleString()}개, 실패: ${(result.failedRows || 0).toLocaleString()}개</small>`
                                        : `<small style="color: #dc3545;">${result.error}</small>`
                                    }
                                </div>
                                <div style="text-align: right;">
                                    <div style="color: ${statusColor}; font-weight: bold;">
                                        ${isSuccess ? `${(result.processedRows || 0).toLocaleString()}개 처리됨` : '처리 실패'}
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
                ${uploadResults.length > 10 ? `<div style="text-align: center; padding-top: 10px; color: #666; font-size: 12px;">총 ${uploadResults.length}개 파일 중 처리 완료</div>` : ''}
            </div>
        `;
    }
    
    resultsSection.innerHTML = summaryHTML + detailsHTML;
    
    // 결과 섹션으로 스크롤
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// 파일 업로드 시뮬레이션 (대량 데이터 처리 시뮬레이션)
// 실제 서버 업로드 함수
async function uploadFileToServer(file) {
    console.log('🚀 uploadFileToServer 함수 시작 - 파일:', file.name);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        console.log('🌐 서버 요청 시작 - /api/admin/upload-ingredients');
        const response = await fetch('/api/admin/upload-ingredients', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            console.log(`파일 업로드 완료: ${file.name} - ${result.details.total_rows}행 처리됨 (신규: ${result.details.new_count}, 업데이트: ${result.details.updated_count}, 실패: ${result.details.error_count})`);
            return {
                processedRows: result.details.total_rows,
                successRows: result.details.new_count + result.details.updated_count,
                failedRows: result.details.error_count
            };
        } else {
            throw new Error(result.message || '업로드 실패');
        }
    } catch (error) {
        console.error('업로드 오류:', error);
        throw error;
    }
}

// simulateFileUpload 함수가 제거됨 - 실제 서버 업로드만 사용

// 업로드 히스토리 로드
function loadUploadHistory() {
    // 실제 구현에서는 API에서 데이터를 가져옴
    console.log('업로드 히스토리 로드됨');
}

// 업체별 필터링
function filterUploadHistory() {
    const supplierFilter = document.getElementById('supplier-filter')?.value;
    console.log('업체별 필터:', supplierFilter);
    showNotification('업체별 필터가 적용되었습니다.', 'info');
}

// 업로드 이력 검색
function searchUploadHistory() {
    const supplierFilter = document.getElementById('supplier-filter')?.value;
    const dateFrom = document.getElementById('date-from')?.value;
    const dateTo = document.getElementById('date-to')?.value;
    
    console.log('업로드 이력 검색:', { supplierFilter, dateFrom, dateTo });
    showNotification('업로드 이력을 조회했습니다.', 'success');
}

// 업로드 상세 결과 표시
function showUploadDetails(uploadId) {
    const detailsSection = document.getElementById('upload-details-section');
    const detailsContent = document.getElementById('upload-details-content');
    
    if (!detailsSection || !detailsContent) return;
    
    // 샘플 상세 데이터
    const sampleDetails = {
        1: {
            fileName: 'food_sample_20241210.xls',
            supplier: '웰스토리',
            uploadDate: '2024-12-10',
            totalRows: 150,
            successRows: 148,
            failedRows: 2,
            validationErrors: [
                { row: 15, column: 'C', field: '고유코드', error: '영문+숫자만 허용됨', value: '한글코드123' },
                { row: 67, column: 'N', field: '비고', error: 'N열 범위 초과', value: '매우 긴 비고 내용...' }
            ],
            outOfRangeData: [
                { row: 67, column: 'O', value: '범위초과데이터' },
                { row: 67, column: 'P', value: '추가데이터' }
            ]
        },
        2: {
            fileName: 'samsung_ingredients.xlsx',
            supplier: '삼성웰스토리',
            uploadDate: '2024-12-08',
            totalRows: 200,
            successRows: 195,
            failedRows: 5,
            validationErrors: [
                { row: 23, column: 'E', field: '원산지', error: '특수문자 사용불가', value: '한국@#$' },
                { row: 45, column: 'I', field: '면세', error: '허용값: Full tax, No tax', value: '부가세있음' },
                { row: 78, column: 'J', field: '선발주일', error: '형식 오류', value: 'D+5일' },
                { row: 123, column: 'K', field: '입고가', error: '숫자만 입력', value: '천원' },
                { row: 156, column: 'L', field: '판매가', error: '음수 불가', value: '-1500' }
            ],
            outOfRangeData: []
        }
    };
    
    const details = sampleDetails[uploadId];
    if (!details) return;
    
    let detailsHTML = generateUploadDetailsHTML(details);
    
    detailsContent.innerHTML = detailsHTML;
    detailsSection.style.display = 'block';
    
    // 상세 결과 섹션으로 스크롤
    detailsSection.scrollIntoView({ behavior: 'smooth' });
}

// 업로드 상세 HTML 생성
function generateUploadDetailsHTML(details) {
    let html = `
        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
            <div style="flex: 1; background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;">
                <h5 style="margin-top: 0; color: #007bff;">📊 업로드 요약</h5>
                <p><strong>파일명:</strong> ${details.fileName}</p>
                <p><strong>거래처:</strong> ${details.supplier}</p>
                <p><strong>업로드일:</strong> ${details.uploadDate}</p>
                <p><strong>총 항목수:</strong> ${details.totalRows}개</p>
                <p><strong>성공:</strong> <span style="color: #28a745; font-weight: bold;">${details.successRows}개</span></p>
                <p><strong>실패:</strong> <span style="color: #dc3545; font-weight: bold;">${details.failedRows}개</span></p>
            </div>
        </div>
    `;
    
    if (details.validationErrors.length > 0) {
        html += generateValidationErrorsTable(details.validationErrors);
    }
    
    if (details.outOfRangeData.length > 0) {
        html += generateOutOfRangeDataTable(details.outOfRangeData);
    }
    
    return html;
}

// 검증 실패 테이블 생성
function generateValidationErrorsTable(errors) {
    return `
        <div style="margin-bottom: 20px;">
            <h5 style="color: #dc3545;">❌ 검증 실패 항목 (${errors.length}개)</h5>
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    <thead>
                        <tr style="background: #f8d7da;">
                            <th style="border: 1px solid #f5c6cb; padding: 8px;">행</th>
                            <th style="border: 1px solid #f5c6cb; padding: 8px;">열</th>
                            <th style="border: 1px solid #f5c6cb; padding: 8px;">필드명</th>
                            <th style="border: 1px solid #f5c6cb; padding: 8px;">오류내용</th>
                            <th style="border: 1px solid #f5c6cb; padding: 8px;">입력값</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${errors.map(error => `
                            <tr>
                                <td style="border: 1px solid #f5c6cb; padding: 8px; text-align: center;">${error.row}</td>
                                <td style="border: 1px solid #f5c6cb; padding: 8px; text-align: center;">${error.column}</td>
                                <td style="border: 1px solid #f5c6cb; padding: 8px;">${error.field}</td>
                                <td style="border: 1px solid #f5c6cb; padding: 8px; color: #721c24;">${error.error}</td>
                                <td style="border: 1px solid #f5c6cb; padding: 8px; font-family: monospace; background: #f8f9fa;">${error.value}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// 범위 초과 데이터 테이블 생성
function generateOutOfRangeDataTable(outOfRangeData) {
    return `
        <div style="margin-bottom: 20px;">
            <h5 style="color: #856404;">⚠️ N열 범위 초과 데이터 (${outOfRangeData.length}개)</h5>
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    <thead>
                        <tr style="background: #fff3cd;">
                            <th style="border: 1px solid #ffeaa7; padding: 8px;">행</th>
                            <th style="border: 1px solid #ffeaa7; padding: 8px;">열</th>
                            <th style="border: 1px solid #ffeaa7; padding: 8px;">범위초과 데이터</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${outOfRangeData.map(data => `
                            <tr>
                                <td style="border: 1px solid #ffeaa7; padding: 8px; text-align: center;">${data.row}</td>
                                <td style="border: 1px solid #ffeaa7; padding: 8px; text-align: center;">${data.column}</td>
                                <td style="border: 1px solid #ffeaa7; padding: 8px; font-family: monospace; background: #f8f9fa;">${data.value}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// 알림 메시지 표시
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 10000;
        padding: 15px 20px; border-radius: 5px; color: white; font-weight: 500;
        ${type === 'success' ? 'background: #28a745;' : 
          type === 'error' ? 'background: #dc3545;' : 'background: #007bff;'}
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transition: opacity 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            if (notification.parentNode) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// 전역 함수로 내보내기
window.initializeIngredientsPage = initializeIngredientsPage;
window.showUploadSection = showUploadSection;
window.downloadTemplate = downloadTemplate;
window.showUploadHistory = showUploadHistory;
window.hideUploadHistory = hideUploadHistory;
window.filterUploadHistory = filterUploadHistory;
window.searchUploadHistory = searchUploadHistory;
window.showUploadDetails = showUploadDetails;
window.uploadFiles = uploadFiles;
window.handleFileSelect = handleFileSelect;
window.clearFiles = clearFiles;
window.removeFile = removeFile;
window.processSelectedFiles = processSelectedFiles;
window.displayBulkUploadResults = displayBulkUploadResults;

//  인그리디언트 모듈 래퍼 추가
window.IngredientsModule = {
    async load() {
        const container = document.getElementById('ingredients-module');
        if (!container) return;

        container.innerHTML = `
            <div style="padding: 20px;">
                <h2>🥬 식재료 관리</h2>
                <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <p>식재료 관리 모듈이 로드되었습니다.</p>
                    <p><em>기존 식재료 관리 기능이 통합되어 있습니다.</em></p>
                    <button onclick="initializeIngredientsPage()" 
                            style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        식재료 관리 초기화
                    </button>
                </div>
            </div>
        `;

        console.log('🥬 Ingredients Module 로드됨 (기존 기능 통합)');
    }
};

})(); // IIFE 종료