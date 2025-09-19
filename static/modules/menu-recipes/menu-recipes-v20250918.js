/**
 * 메뉴/레시피 관리 모듈
 * Handsontable을 사용한 엑셀 스타일 편집기
 */
class MenuRecipeManagement {
    constructor() {
        // CONFIG 기본값 설정
        this.CONFIG = window.CONFIG || {
            API_BASE_URL: 'http://127.0.0.1:8012'
        };

        // 멤버 변수 초기화
        this.hot = null; // Handsontable 인스턴스
        this.currentRow = -1; // 현재 선택된 행
        this.ingredientsData = []; // 전체 식자재 데이터
        this.menus = []; // 메뉴 목록
        this.currentMenuId = null;
        this.recentlyModifiedMenus = new Set(); // 최근 수정/생성된 메뉴 IDs

        // 사진 관련 변수
        this.currentPhotoFile = null;
        this.currentPhotoUrl = null;
        this.currentPhotoType = null; // 'file', 'url', 'existing'

        // 검색 결과 저장
        this.searchResults = null;

        // 이벤트 바인딩
        this.bindEvents();
    }

    /**
     * 모듈 초기화
     */
    init() {
        console.log('[MenuRecipeManagement] 모듈 초기화 시작');

        // Handsontable 라이브러리 확인
        if (typeof Handsontable === 'undefined') {
            console.error('[MenuRecipeManagement] Handsontable 라이브러리가 로드되지 않았습니다.');
            return false;
        }

        // DOM 요소 확인
        if (!document.getElementById('ingredientsGrid')) {
            console.error('[MenuRecipeManagement] ingredientsGrid 요소를 찾을 수 없습니다.');
            return false;
        }

        // 그리드 초기화
        this.initGrid();

        // 메뉴 목록 로드
        this.loadMenus();

        // 전역 함수들을 window에 등록 (기존 코드와의 호환성)
        this.registerGlobalFunctions();

        console.log('[MenuRecipeManagement] 모듈 초기화 완료');
        return true;
    }

    /**
     * 모듈 정리
     */
    destroy() {
        console.log('[MenuRecipeManagement] 모듈 정리 시작');

        // Handsontable 인스턴스 정리
        if (this.hot) {
            this.hot.destroy();
            this.hot = null;
        }

        // 전역 함수들 제거
        this.unregisterGlobalFunctions();

        // 이벤트 리스너 제거
        this.unbindEvents();

        console.log('[MenuRecipeManagement] 모듈 정리 완료');
    }

    /**
     * 이벤트 바인딩
     */
    bindEvents() {
        // DOMContentLoaded 이벤트는 init()에서 처리
        document.addEventListener('DOMContentLoaded', () => {
            if (document.getElementById('ingredientsGrid')) {
                this.init();
            }
        });
    }

    /**
     * 이벤트 언바인딩
     */
    unbindEvents() {
        // 필요시 이벤트 리스너 제거
    }

    /**
     * 전역 함수들을 window에 등록 (기존 코드와의 호환성)
     */
    registerGlobalFunctions() {
        const self = this;

        // 그리드 관련 함수들
        window.addRow = () => self.addRow();
        window.deleteRow = () => self.deleteRow();
        window.resetGrid = (skipConfirm) => self.resetGrid(skipConfirm);
        window.debugGrid = () => self.debugGrid();

        // 모달 관련 함수들
        window.openSearchModal = () => self.openSearchModal();
        window.closeModal = () => self.closeModal();
        window.searchIngredients = () => self.searchIngredients();

        // 메뉴 관련 함수들
        window.saveMenu = () => self.saveMenu();
        window.saveMenuAs = () => self.saveMenuAs();
        window.searchMenus = () => self.searchMenus();
        window.selectMenu = (menuId, element) => self.selectMenu(menuId, element);
        window.createNewMenu = () => self.createNewMenu();
        window.createNewMenuWithName = (menuName) => self.createNewMenuWithName(menuName);

        // 엑셀 관련 함수들
        window.importFromExcel = () => self.importFromExcel();
        window.exportToExcel = () => self.exportToExcel();

        // 사진 관련 함수들
        window.handlePhotoClick = () => self.handlePhotoClick();
        window.handlePhotoUpload = (event) => self.handlePhotoUpload(event);
        window.useExistingPhoto = () => self.useExistingPhoto();
        window.clearPhoto = () => self.clearPhoto();
        window.selectExistingPhoto = (photoPath, menuName) => self.selectExistingPhoto(photoPath, menuName);

        // 검색 결과 선택 함수
        window.selectIngredientByIndex = (index) => self.selectIngredientByIndex(index);
    }

    /**
     * 전역 함수들 제거
     */
    unregisterGlobalFunctions() {
        const functionsToRemove = [
            'addRow', 'deleteRow', 'resetGrid', 'debugGrid',
            'openSearchModal', 'closeModal', 'searchIngredients',
            'saveMenu', 'saveMenuAs', 'searchMenus', 'selectMenu',
            'createNewMenu', 'createNewMenuWithName',
            'importFromExcel', 'exportToExcel',
            'handlePhotoClick', 'handlePhotoUpload', 'useExistingPhoto',
            'clearPhoto', 'selectExistingPhoto', 'selectIngredientByIndex'
        ];

        functionsToRemove.forEach(funcName => {
            if (window[funcName]) {
                delete window[funcName];
            }
        });
    }

    /**
     * Handsontable 초기화
     */
    initGrid() {
        const container = document.getElementById('ingredientsGrid');
        if (!container) {
            console.error('[initGrid] ingredientsGrid 컨테이너를 찾을 수 없습니다.');
            return;
        }

        // 7개 행으로 초기 데이터 설정
        const data = [];
        const today = new Date().toISOString().slice(5, 10).replace(/-/g, '.'); // MM.DD 형식
        for (let i = 0; i < 7; i++) {
            data.push(['', '', '', '', '', 0, 0, 0, 0, '', today]);
        }

        this.hot = new Handsontable(container, {
            data: data,
            colHeaders: [
                '식자재코드', '식자재명', '🔍', '규격', '단위', '선발주일', '판매가', '1인소요량', '1인재료비', '거래처명', '등록일'
            ],
            colWidths: [100, 350, 35, 200, 60, 60, 85, 80, 100, 120, 80],
            rowHeaders: true,
            height: 350,
            licenseKey: 'non-commercial-and-evaluation',
            afterChange: (changes, source) => {
                if (source === 'loadData') return;

                changes?.forEach(([row, prop, oldValue, newValue]) => {
                    // 1인소요량이 변경되면 1인재료비 계산
                    if (prop === 7) { // 1인소요량
                        const price = this.hot.getDataAtCell(row, 6) || 0; // 판매가
                        const quantity = newValue || 0;
                        const cost = Math.round(price * quantity);
                        this.hot.setDataAtCell(row, 8, cost, 'auto');
                    }
                });

                this.calculateTotal();
                this.updateRowCount();
            },
            cells: (row, col) => {
                const cellProperties = {};

                // 검색 버튼 컬럼
                if (col === 2) {
                    cellProperties.renderer = this.searchButtonRenderer.bind(this);
                    cellProperties.readOnly = true;
                }

                // 판매가 컬럼 - 우측정렬, 천원단위 쉼표
                if (col === 6) {
                    cellProperties.type = 'numeric';
                    cellProperties.numericFormat = {
                        pattern: '0,0'
                    };
                    cellProperties.className = 'htRight';
                }

                // 1인소요량 컬럼 - 하늘색 배경, 우측정렬
                if (col === 7) {
                    cellProperties.type = 'numeric';
                    cellProperties.className = 'highlight-blue htRight';
                }

                // 1인재료비 컬럼 - 노란색 배경, 우측정렬
                if (col === 8) {
                    cellProperties.type = 'numeric';
                    cellProperties.numericFormat = {
                        pattern: '0,0'
                    };
                    cellProperties.className = 'highlight-yellow htRight';
                }

                return cellProperties;
            }
        });

        // 검색 버튼 클릭 이벤트
        this.hot.addHook('afterOnCellMouseDown', (event, coords) => {
            console.log('[afterOnCellMouseDown] 클릭 좌표:', coords);
            if (coords.col === 2) { // 검색 버튼 컬럼
                this.currentRow = coords.row;
                console.log('[afterOnCellMouseDown] 검색 버튼 클릭! currentRow 설정:', this.currentRow);
                this.openSearchModal();
            }
        });
    }

    /**
     * 검색 버튼 렌더러
     */
    searchButtonRenderer(instance, td, row, col, prop, value, cellProperties) {
        td.innerHTML = '<button class="search-btn">🔍</button>';
        td.style.padding = '0';
        return td;
    }

    /**
     * 행 추가
     */
    addRow() {
        const today = new Date().toISOString().slice(5, 10).replace(/-/g, '.'); // MM.DD 형식
        const newRow = ['', '', '', '', '', 0, 0, 0, 0, '', today];
        this.hot.alter('insert_row_below', this.hot.countRows() - 1, 1, newRow);
        this.updateRowCount();
    }

    /**
     * 행 내용 지우기
     */
    deleteRow() {
        const selected = this.hot.getSelected();
        if (selected) {
            const row = selected[0][0];
            // 선택된 행의 모든 데이터를 비움 (행은 유지)
            const emptyRow = ['', '', '', '', '', 0, 0, 0, 0, '', ''];
            this.hot.setDataAtRow(row, emptyRow);
        } else {
            alert('지울 행을 먼저 선택해주세요.');
        }
    }

    /**
     * 그리드 데이터 디버깅 함수
     */
    debugGrid() {
        console.log('===== 그리드 디버깅 정보 =====');
        const data = this.hot.getData();
        console.log('전체 행 수:', this.hot.countRows());
        console.log('전체 열 수:', this.hot.countCols());

        // 각 행의 데이터 상세 표시
        data.forEach((row, index) => {
            // 빈 행인지 확인
            const isEmpty = !row[1] || row[1].trim() === '';
            if (!isEmpty) {
                console.log(`[행 ${index}] 데이터 있음:`);
                console.log('  식자재코드:', row[0]);
                console.log('  식자재명:', row[1]);
                console.log('  규격:', row[3]);
                console.log('  단위:', row[4]);
                console.log('  판매가:', row[6]);
                console.log('  1인소요량:', row[7]);
                console.log('  1인재료비:', row[8]);
                console.log('  거래처명:', row[9]);
            } else {
                console.log(`[행 ${index}] 빈 행`);
            }
        });

        // 숨겨진 행이나 열이 있는지 확인
        const hiddenRows = [];
        const hiddenCols = [];

        for (let i = 0; i < this.hot.countRows(); i++) {
            if (this.hot.getRowHeight(i) === 0) {
                hiddenRows.push(i);
            }
        }

        for (let i = 0; i < this.hot.countCols(); i++) {
            if (this.hot.getColWidth(i) === 0) {
                hiddenCols.push(i);
            }
        }

        if (hiddenRows.length > 0) {
            console.log('숨겨진 행:', hiddenRows);
        }
        if (hiddenCols.length > 0) {
            console.log('숨겨진 열:', hiddenCols);
        }

        console.log('===========================');
    }

    /**
     * 그리드 초기화
     */
    resetGrid(skipConfirm = false) {
        // 데이터가 있는지 확인
        const currentData = this.hot.getData();
        let hasData = false;
        for (let row of currentData) {
            if (row[1] && row[1].trim() !== '') {  // 식자재명이 있으면 데이터가 있는 것
                hasData = true;
                break;
            }
        }

        // 데이터가 있을 때만 확인 메시지 표시 (skipConfirm이 false일 때)
        if (!skipConfirm && hasData) {
            if (!confirm('모든 데이터가 삭제됩니다. 계속하시겠습니까?')) {
                return;
            }
        }

        const data = [];
        const today = new Date().toISOString().slice(5, 10).replace(/-/g, '.'); // MM.DD 형식
        for (let i = 0; i < 7; i++) {
            data.push(['', '', '', '', '', 0, 0, 0, 0, '', today]);
        }
        this.hot.loadData(data);
        this.updateRowCount();
        this.calculateTotal();
    }

    /**
     * 행 개수 업데이트
     */
    updateRowCount() {
        const rowCountElement = document.getElementById('rowCount');
        if (rowCountElement) {
            rowCountElement.textContent = this.hot.countRows();
        }
    }

    /**
     * 총 금액 계산
     */
    calculateTotal() {
        let total = 0;
        const data = this.hot.getData();

        data.forEach(row => {
            // 빈 행이 아닌 경우에만 계산 (식자재명이 있는 경우)
            if (row[1] && row[1].trim() !== '') {
                total += parseFloat(row[8]) || 0; // 1인재료비 합계
            }
        });

        const totalAmountElement = document.getElementById('totalAmount');
        if (totalAmountElement) {
            totalAmountElement.textContent = total.toLocaleString() + '원';
        }

        return total;
    }

    /**
     * 검색 모달 열기
     */
    openSearchModal() {
        console.log('식자재 검색 모달 열기 시도');
        const modal = document.getElementById('ingredientModal');
        console.log('모달 요소 찾기:', modal ? '성공' : '실패');

        if (modal) {
            modal.classList.add('active');
            console.log('모달 클래스 추가 완료, loadIngredients 호출');
            this.loadIngredients();
        } else {
            console.error('ingredientModal 요소를 찾을 수 없습니다');
        }
    }

    /**
     * 모달 닫기
     */
    closeModal() {
        const modal = document.getElementById('ingredientModal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    /**
     * 식자재 데이터 로드 - 서버 사이드 검색 사용
     */
    async loadIngredients() {
        this.searchIngredients(); // 초기 로드 시 바로 검색 실행
    }

    /**
     * 식자재 검색 - 서버 사이드 검색으로 변경
     */
    async searchIngredients() {
        console.log('식자재 검색 함수 호출됨');
        const searchTerm = document.getElementById('ingredientSearch')?.value.trim() || '';
        const supplierFilter = document.getElementById('supplierFilter')?.value || '';
        console.log('검색어:', searchTerm, '업체 필터:', supplierFilter);

        const tbody = document.getElementById('searchResultsBody');
        console.log('검색 결과 테이블 찾기:', tbody ? '성공' : '실패');
        if (!tbody) {
            console.error('searchResultsBody 요소를 찾을 수 없습니다');
            return;
        }

        tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 20px;">검색 중...</td></tr>';

        try {
            // 서버에 검색 요청 - search 파라미터 사용
            let url = `${this.CONFIG.API_BASE_URL}/api/admin/ingredients-new?page=1&per_page=500`;
            if (searchTerm) {
                url += `&search=${encodeURIComponent(searchTerm)}`;
            }
            if (supplierFilter) {
                url += `&supplier=${encodeURIComponent(supplierFilter)}`;
            }

            const response = await fetch(url);
            const data = await response.json();

            if (data.success) {
                let filtered = data.ingredients || [];

                // 판매가가 없거나 0인 식자재만 제외
                filtered = filtered.filter(item => item.selling_price && item.selling_price > 0);

                // 단위당 단가 계산 및 정렬
                filtered = filtered.map(item => {
                    const specMatch = item.specification?.match(/(\d+(\.\d+)?)/);
                    const quantity = specMatch ? parseFloat(specMatch[1]) : 1;
                    item.unit_price = (item.selling_price || 0) / quantity;
                    return item;
                }).sort((a, b) => (a.unit_price || 0) - (b.unit_price || 0));

                // 전체 결과 수 저장
                const totalResults = filtered.length;

                // 결과 개수 표시
                if (totalResults > 0) {
                    console.log(`${searchTerm ? searchTerm + ' 검색 결과: ' : ''}${totalResults}개 (단위당 단가 낮은 순)`);
                }

                // 검색 결과를 인스턴스 변수에 저장
                this.searchResults = filtered;

                tbody.innerHTML = filtered.map((item, index) => `
            <tr onclick="window.selectIngredientByIndex(${index})"
                style="cursor: pointer;">
                <td style="padding: 2px;">
                    <div style="width: 40px; height: 40px; background: #f5f5f5; border-radius: 4px; overflow: hidden;">
                        ${item.thumbnail ?
                          `<img src="/${item.thumbnail}" style="width: 100%; height: 100%; object-fit: cover;">` :
                          `<div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #ccc; font-size: 10px;">-</div>`
                        }
                    </div>
                </td>
                <td style="font-weight: 500;" title="${item.ingredient_name || ''}">${item.ingredient_name || ''}</td>
                <td title="${item.specification || ''}">${item.specification || ''}</td>
                <td>${item.unit || ''}</td>
                <td style="text-align: right;">${item.selling_price?.toLocaleString() || '0'}</td>
                <td style="color: #f44336; font-weight: 600; text-align: right;">${item.unit_price ? item.unit_price.toFixed(1) : '-'}</td>
                <td style="text-align: center;">${item.delivery_days || '0'}</td>
                <td style="color: #666;" title="${item.supplier_name || ''}">${item.supplier_name || ''}</td>
                <td style="text-align: center; color: ${item.is_published !== false ? '#4caf50' : '#f44336'};">
                    ${item.is_published !== false ? 'O' : 'X'}
                </td>
                <td style="text-align: center; color: ${item.is_stocked !== false ? '#4caf50' : '#f44336'};">
                    ${item.is_stocked !== false ? 'O' : 'X'}
                </td>
            </tr>
        `).join('');
            } else {
                tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 20px;">검색 결과가 없습니다.</td></tr>';
            }
        } catch (error) {
            console.error('식자재 검색 실패:', error);
            tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 20px; color: red;">검색 중 오류가 발생했습니다.</td></tr>';
        }
    }

    /**
     * 인덱스로 식자재 선택
     */
    selectIngredientByIndex(index) {
        console.log('[selectIngredientByIndex] 인덱스:', index);
        if (this.searchResults && this.searchResults[index]) {
            this.selectIngredient(this.searchResults[index]);
        } else {
            console.error('[selectIngredientByIndex] 검색 결과를 찾을 수 없음');
        }
    }

    /**
     * 식자재 선택
     */
    selectIngredient(item) {
        console.log('[selectIngredient] 시작 - currentRow:', this.currentRow);
        console.log('[selectIngredient] 선택된 아이템:', item);

        if (this.currentRow >= 0) {
            console.log('[selectIngredient] 데이터 설정 시작 - 행:', this.currentRow);

            // 기존 값 가져오기
            const existingQuantity = this.hot.getDataAtCell(this.currentRow, 7) || 0;
            const existingDate = this.hot.getDataAtCell(this.currentRow, 10) || new Date().toISOString().slice(5, 10).replace(/-/g, '.');

            // 새로운 행 데이터 생성
            const newRowData = [
                item.ingredient_code || '',     // 0: 식자재코드
                item.ingredient_name || '',     // 1: 식자재명
                '',                             // 2: 검색버튼
                item.specification || '',       // 3: 규격
                item.unit || '',               // 4: 단위
                item.delivery_days || 0,       // 5: 선발주일
                item.selling_price || 0,       // 6: 판매가
                existingQuantity,               // 7: 1인소요량
                existingQuantity > 0 ? Math.round((item.selling_price || 0) * existingQuantity) : 0, // 8: 1인재료비
                item.supplier_name || '',      // 9: 거래처명
                existingDate                    // 10: 등록일
            ];

            console.log('[selectIngredient] 새 행 데이터:', newRowData);

            // 방법: 전체 데이터를 가져와서 수정 후 다시 로드
            const allData = this.hot.getData();

            // 현재 행 데이터 교체
            for (let i = 0; i < newRowData.length; i++) {
                if (i !== 2) { // 검색 버튼 열은 제외
                    allData[this.currentRow][i] = newRowData[i];
                }
            }

            console.log('[selectIngredient] 전체 데이터 교체 방식');

            // 전체 데이터 다시 로드
            this.hot.loadData(allData);

            // 추가로 강제 렌더링
            setTimeout(() => {
                this.hot.render();
                this.hot.validateCells();
            }, 50);

            // 설정 후 확인
            setTimeout(() => {
                const updatedData = this.hot.getDataAtRow(this.currentRow);
                console.log('[selectIngredient] 업데이트된 행 데이터:', updatedData);

                // 화면에 실제로 보이는지 확인
                const cell = this.hot.getCell(this.currentRow, 1);
                if (cell) {
                    console.log('[selectIngredient] 셀 HTML:', cell.innerHTML);
                    console.log('[selectIngredient] 셀 텍스트:', cell.textContent);
                }

                this.calculateTotal();
                this.updateRowCount();
            }, 200);
        } else {
            console.log('[selectIngredient] currentRow가 유효하지 않음:', this.currentRow);
            alert('선택할 행을 먼저 클릭해주세요.');
        }

        this.closeModal();
    }

    /**
     * 메뉴 저장
     */
    async saveMenu() {
        console.log('[saveMenu] ===== 저장 시작 =====');
        console.log('[saveMenu] 1. 입력값 확인');
        const menuName = document.getElementById('menuName')?.value || '';

        // 라디오 버튼에서 선택된 카테고리 가져오기
        const categoryRadio = document.querySelector('input[name="category"]:checked');
        const category = categoryRadio ? categoryRadio.value : '';

        console.log('[saveMenu] menuName:', menuName);
        console.log('[saveMenu] category:', category);

        if (!menuName) {
            console.log('[saveMenu] 메뉴명 없음 - 종료');
            alert('메뉴명을 입력해주세요.');
            return;
        }

        if (!category) {
            console.log('[saveMenu] 분류 없음 - 종료');
            alert('분류를 선택해주세요.');
            return;
        }

        console.log('[saveMenu] 2. 그리드 데이터 수집');
        const data = this.hot.getData();
        console.log('[saveMenu] 전체 데이터:', data);

        const ingredients = [];
        for (let i = 0; i < data.length; i++) {
            const row = data[i];
            if (row[1] && row[1].toString().trim() !== '') {
                // D-1, D-2 같은 형식을 숫자로 변환
                let deliveryDays = 0;
                if (row[5]) {
                    const deliveryStr = row[5].toString();
                    if (deliveryStr.startsWith('D-')) {
                        deliveryDays = parseInt(deliveryStr.replace('D-', '')) || 0;
                    } else if (deliveryStr.startsWith('D+')) {
                        deliveryDays = parseInt(deliveryStr.replace('D+', '')) || 0;
                    } else {
                        deliveryDays = parseInt(deliveryStr) || 0;
                    }
                }

                const ingredient = {
                    ingredient_code: row[0] || '',
                    ingredient_name: row[1],
                    specification: row[3] || '',
                    unit: row[4] || '',
                    delivery_days: deliveryDays,
                    selling_price: parseFloat(row[6]) || 0,
                    quantity: parseFloat(row[7]) || 0,
                    amount: parseFloat(row[8]) || 0,
                    supplier_name: row[9] || ''
                };
                ingredients.push(ingredient);
                console.log(`[saveMenu] 재료 ${i}:`, ingredient);
            }
        }
        console.log('[saveMenu] 필터링된 재료 개수:', ingredients.length);

        if (ingredients.length === 0) {
            console.log('[saveMenu] 재료 없음 - 종료');
            alert('최소 1개 이상의 식자재를 추가해주세요.');
            return;
        }

        const cookingNote = document.getElementById('cookingNote')?.value || '';

        console.log('[saveMenu] 3. FormData 생성');
        const formData = new FormData();
        formData.append('recipe_name', menuName);
        formData.append('category', category);
        formData.append('cooking_note', cookingNote);

        const ingredientsJson = JSON.stringify(ingredients);
        console.log('[saveMenu] ingredients JSON:', ingredientsJson);
        formData.append('ingredients', ingredientsJson);

        // 사진 처리 - 타입에 따라 다르게 처리
        console.log('[saveMenu] 4. 사진 처리');
        console.log('[saveMenu] currentPhotoType:', this.currentPhotoType);
        console.log('[saveMenu] currentPhotoFile:', this.currentPhotoFile);
        console.log('[saveMenu] currentPhotoUrl:', this.currentPhotoUrl);

        if (this.currentPhotoType === 'file' && this.currentPhotoFile) {
            console.log('[saveMenu] 새 파일 업로드');
            formData.append('image', this.currentPhotoFile);
        } else if (this.currentPhotoType === 'existing' && this.currentPhotoUrl) {
            console.log('[saveMenu] 기존 사진 링크 사용');
            formData.append('image_url', this.currentPhotoUrl);
        } else {
            console.log('[saveMenu] 사진 없음');
        }

        // FormData 내용 확인
        console.log('[saveMenu] 5. FormData 내용 확인');
        for (let pair of formData.entries()) {
            console.log('[saveMenu] FormData:', pair[0], '=',
                pair[1] instanceof File ? `File(${pair[1].name})` : pair[1].substring ? pair[1].substring(0, 100) : pair[1]);
        }

        try {
            console.log('[saveMenu] 6. 서버로 전송 시작');
            console.log('[saveMenu] URL:', `${this.CONFIG.API_BASE_URL}/api/recipe/save`);

            const response = await fetch(`${this.CONFIG.API_BASE_URL}/api/recipe/save`, {
                method: 'POST',
                body: formData
            });

            console.log('[saveMenu] 7. 응답 수신');
            console.log('[saveMenu] 상태 코드:', response.status);
            console.log('[saveMenu] 상태 텍스트:', response.statusText);

            const responseText = await response.text();
            console.log('[saveMenu] 응답 텍스트:', responseText);

            let result;
            try {
                result = JSON.parse(responseText);
                console.log('[saveMenu] 8. JSON 파싱 성공');
                console.log('[saveMenu] 파싱된 결과:', result);
            } catch (parseError) {
                console.error('[saveMenu] JSON 파싱 실패:', parseError);
                console.error('[saveMenu] 응답 원문:', responseText);
                alert('서버 응답을 처리할 수 없습니다.\n응답: ' + responseText.substring(0, 100));
                return;
            }

            if (result.success) {
                console.log('[saveMenu] 9. 저장 성공!');
                console.log('[saveMenu] recipe_id:', result.recipe_id);
                console.log('[saveMenu] recipe_code:', result.recipe_code);

                alert(`"${menuName}" 레시피가 성공적으로 저장되었습니다!`);

                // 새로 저장된 메뉴를 목록에 추가
                const newMenu = {
                    id: result.recipe_id,
                    recipe_code: result.recipe_code,
                    name: menuName,
                    category: category,
                    total_cost: this.calculateTotal(),
                    created_at: new Date().toISOString()
                };

                // 최근 수정 목록에 추가
                this.recentlyModifiedMenus.add(result.recipe_id);

                // 메뉴 목록 앞쪽에 추가
                this.menus.unshift(newMenu);
                this.renderMenuList();

                // 저장 후 초기화 또는 다른 동작
                if (confirm('새 레시피를 작성하시겠습니까?')) {
                    console.log('[saveMenu] 그리드 초기화');
                    this.resetGrid();
                }
            } else {
                console.log('[saveMenu] 9. 저장 실패');
                console.log('[saveMenu] 오류 메시지:', result.detail || result.error || '알 수 없는 오류');
                alert('저장 실패: ' + (result.detail || result.error || '알 수 없는 오류'));
            }
        } catch (error) {
            console.error('[saveMenu] 예외 발생!');
            console.error('[saveMenu] 오류 객체:', error);
            console.error('[saveMenu] 오류 메시지:', error.message);
            console.error('[saveMenu] 스택:', error.stack);
            alert('저장 중 오류가 발생했습니다:\n' + error.message);
        }

        console.log('[saveMenu] ===== 저장 프로세스 종료 =====');
    }

    /**
     * 다른 이름으로 저장
     */
    async saveMenuAs() {
        const menuName = document.getElementById('menuName')?.value || '';

        if (!menuName) {
            alert('메뉴명을 입력해주세요.');
            return;
        }

        // 새 이름 입력 받기
        const newName = prompt('새로운 메뉴명을 입력하세요:', menuName + ' (복사본)');

        if (!newName || newName.trim() === '') {
            return;
        }

        // 원래 메뉴명 임시 보관
        const originalName = menuName;

        // 새 이름으로 변경
        const menuNameElement = document.getElementById('menuName');
        if (menuNameElement) {
            menuNameElement.value = newName;
        }

        // 저장 실행
        await this.saveMenu();
    }

    /**
     * 메뉴 목록 로드 (단계적 로딩)
     */
    async loadMenus() {
        try {
            console.log('새 DB 전용 메뉴 로딩 시작');
            const totalCountElem = document.getElementById('totalMenuCount');

            // 로딩 표시
            if (totalCountElem) {
                totalCountElem.textContent = '로딩...';
            }

            // 새 DB에서 메뉴 로드 (JSON 완전 제거)
            const response = await fetch(`${this.CONFIG.API_BASE_URL}/api/search_recipes`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({keyword: '', limit: 1000})
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // DB 메뉴만 사용
                    this.menus = result.data || [];

                    if (totalCountElem) {
                        totalCountElem.textContent = result.total || this.menus.length;
                    }

                    this.renderMenuList();
                    console.log(`DB 메뉴 로딩 완료: ${this.menus.length}개`);
                } else {
                    console.error('메뉴 로드 실패:', result.error);
                }
            } else {
                console.error('API 호출 실패:', response.status);
            }
        } catch (error) {
            console.error('메뉴 로드 오류:', error);
            if (totalCountElem) {
                totalCountElem.textContent = '오류';
            }
        }
    }

    /**
     * 메뉴 목록 렌더링
     */
    renderMenuList(updateCount = true) {
        const menuList = document.getElementById('menuList');
        const totalCountEl = document.getElementById('totalMenuCount');

        if (!menuList) return;

        // 총 메뉴 개수 업데이트 (필요 시에만)
        if (updateCount && totalCountEl) {
            totalCountEl.textContent = this.menus.length;
        }

        // 최근 수정/생성된 메뉴를 상단으로 정렬
        const sortedMenus = [...this.menus].sort((a, b) => {
            // 1순위: 최근 수정된 메뉴
            const aIsRecent = this.recentlyModifiedMenus.has(a.id);
            const bIsRecent = this.recentlyModifiedMenus.has(b.id);

            if (aIsRecent && !bIsRecent) return -1;
            if (!aIsRecent && bIsRecent) return 1;

            // 2순위: 데이터베이스의 새 메뉴
            const aIsNew = a.is_new === true;
            const bIsNew = b.is_new === true;

            if (aIsNew && !bIsNew) return -1;
            if (!aIsNew && bIsNew) return 1;

            // 3순위: ID 역순 (최신순)
            return (b.id || 0) - (a.id || 0);
        });

        // 검색 결과가 없을 때 안내 메시지 표시
        if (sortedMenus.length === 0) {
            const searchTerm = document.getElementById('menuSearch')?.value.trim() || '';
            if (searchTerm) {
                menuList.innerHTML = `
                    <div style="padding: 20px; text-align: center; color: #6c757d;">
                        <div style="font-size: 48px; margin-bottom: 10px;">🔍</div>
                        <div style="font-size: 14px; margin-bottom: 15px;">
                            "${searchTerm}" 검색 결과가 없습니다.
                        </div>
                        <button class="btn btn-primary" onclick="createNewMenuWithName('${searchTerm}')"
                            style="background: linear-gradient(135deg, #667eea, #764ba2);
                                   color: white; padding: 8px 20px; border: none;
                                   border-radius: 4px; font-size: 13px; font-weight: 600;
                                   cursor: pointer;">
                            "${searchTerm}" 메뉴 만들기
                        </button>
                    </div>
                `;
            } else {
                menuList.innerHTML = `
                    <div style="padding: 20px; text-align: center; color: #6c757d; font-size: 13px;">
                        메뉴를 검색하거나 새로 만들어보세요.
                    </div>
                `;
            }
            return;
        }

        menuList.innerHTML = sortedMenus.map(menu => {
            let bgColor = '';
            let indicator = '';

            if (this.recentlyModifiedMenus.has(menu.id)) {
                bgColor = '#f8f9ff';
                indicator = '<span style="color: #ff6b6b; font-size: 10px;">● </span>';
            } else if (menu.is_new) {
                bgColor = '#f0fff4';
                indicator = '<span style="color: #28a745; font-size: 10px;">● </span>';
            }

            return `
                <div class="menu-item" onclick="selectMenu(${menu.id}, this)" style="display: flex; align-items: center; gap: 10px; padding: 10px; cursor: pointer; border-bottom: 1px solid #eee; ${bgColor ? `background-color: ${bgColor};` : ''}">
                    <div style="width: 50px; height: 50px; flex-shrink: 0; border-radius: 4px; overflow: hidden; background: #f0f0f0;">
                        ${menu.thumbnail ?
                          `<img src="/${menu.thumbnail}" style="width: 100%; height: 100%; object-fit: cover;">` :
                          `<div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #999; font-size: 10px;">🍴</div>`
                        }
                    </div>
                    <div style="flex: 1;">
                        <h4 style="margin: 0; font-size: 14px;">
                            ${indicator}
                            ${menu.name}
                        </h4>
                        <small style="color: #666;">${menu.category || '미분류'}</small>
                    </div>
                </div>
            `;
        }).join('');
    }

    /**
     * 메뉴 검색
     */
    searchMenus() {
        const searchTerm = document.getElementById('menuSearch')?.value.toLowerCase() || '';
        const filtered = this.menus.filter(menu =>
            menu.name.toLowerCase().includes(searchTerm)
        );

        const menuList = document.getElementById('menuList');
        if (!menuList) return;

        menuList.innerHTML = filtered.map(menu => `
            <div class="menu-item" onclick="selectMenu(${menu.id}, this)" style="display: flex; align-items: center; gap: 10px; padding: 10px; cursor: pointer; border-bottom: 1px solid #eee;">
                <div style="width: 50px; height: 50px; flex-shrink: 0; border-radius: 4px; overflow: hidden; background: #f0f0f0;">
                    ${menu.thumbnail ?
                      `<img src="/${menu.thumbnail}" style="width: 100%; height: 100%; object-fit: cover;">` :
                      `<div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #999; font-size: 10px;">🍴</div>`
                    }
                </div>
                <div style="flex: 1;">
                    <h4 style="margin: 0; font-size: 14px;">${menu.name}</h4>
                    <small style="color: #666;">${menu.category || '미분류'}</small>
                </div>
            </div>
        `).join('');
    }

    /**
     * 메뉴 선택
     */
    async selectMenu(menuId, element) {
        console.log('selectMenu 호출, ID:', menuId, '타입:', typeof menuId);
        console.log('현재 메뉴 목록:', this.menus.map(m => ({id: m.id, name: m.name || m.recipe_name})));

        this.currentMenuId = menuId;
        const menu = this.menus.find(m => m.id === menuId);
        console.log('찾은 메뉴:', menu);

        if (menu) {
            console.log('메뉴 정보 설정 시작');
            const menuTitleElement = document.getElementById('menuTitle');
            const menuNameElement = document.getElementById('menuName');

            if (menuTitleElement) menuTitleElement.textContent = menu.name;
            if (menuNameElement) menuNameElement.value = menu.name;

            // 라디오 버튼에서 카테고리 선택
            if (menu.category) {
                const categoryRadio = document.querySelector(`input[name="category"][value="${menu.category}"]`);
                if (categoryRadio) {
                    categoryRadio.checked = true;
                }
            }

            // 선택된 메뉴 표시
            document.querySelectorAll('.menu-item').forEach(item => {
                item.classList.remove('selected');
            });
            // element 파라미터 사용
            if (element) {
                element.classList.add('selected');
            }

            // 기존 메뉴 선택 시 '다른 이름으로 저장' 버튼 표시
            const saveAsButton = document.getElementById('saveAsButton');
            if (saveAsButton) {
                saveAsButton.style.display = 'block';
            }

            // 그리드 초기화
            this.resetGrid(true);

            // 모든 메뉴를 DB 메뉴로 처리 (JSON 로직 완전 제거)
            try {
                const apiUrl = `${this.CONFIG.API_BASE_URL}/api/admin/menu-recipes/${menuId}`;
                console.log('메뉴 상세 정보 로드, ID:', menuId, 'URL:', apiUrl);
                const response = await fetch(apiUrl);

                if (response.ok) {
                    const result = await response.json();
                    console.log('API 응답:', result);

                    if (result.success && result.data) {
                        const recipeDetail = result.data.recipe;
                        const ingredients = result.data.ingredients;

                        console.log('레시피 상세:', recipeDetail);
                        console.log('재료 목록:', ingredients);

                        // 조리법 메모 설정
                        const cookingNoteElem = document.getElementById('cookingNote');
                        if (cookingNoteElem && recipeDetail.cooking_note) {
                            cookingNoteElem.value = recipeDetail.cooking_note;
                            console.log('조리법 설정:', recipeDetail.cooking_note);
                        }

                        // 사진 설정
                        const photoPreview = document.getElementById('photoPreview');
                        const photoPlaceholder = document.getElementById('photoPlaceholder');

                        if (recipeDetail.photo_path && photoPreview && photoPlaceholder) {
                            photoPreview.src = '/' + recipeDetail.photo_path;
                            photoPreview.style.display = 'block';
                            photoPlaceholder.style.display = 'none';
                            console.log('사진 설정:', recipeDetail.photo_path);
                        } else if (photoPreview && photoPlaceholder) {
                            photoPreview.style.display = 'none';
                            photoPlaceholder.style.display = 'block';
                        }

                        // 재료 데이터를 그리드에 로드
                        if (ingredients && Array.isArray(ingredients) && ingredients.length > 0) {
                            console.log('재료 데이터 그리드 로드:', ingredients.length + '개');
                            this.loadIngredientsToGrid(ingredients);
                        } else {
                            console.log('재료 데이터 없음');
                        }

                        // 총액 계산
                        this.calculateTotal();
                    } else {
                        console.error('API 응답 형식 오류:', result);
                    }
                } else {
                    console.error('메뉴 상세 정보 로드 실패:', response.status);
                }
            } catch (error) {
                console.error('메뉴 상세 정보 로드 오류:', error);
            }
        }
    }

    /**
     * 재료 데이터를 그리드에 로드하는 함수 (간단화)
     */
    loadIngredientsToGrid(ingredients) {
        console.log('loadIngredientsToGrid 호출됨, 재료 개수:', ingredients ? ingredients.length : 0);
        console.log('전달받은 재료 데이터:', ingredients);

        if (!this.hot) {
            console.error('Handsontable 인스턴스가 없습니다');
            return;
        }

        if (!ingredients || !Array.isArray(ingredients)) {
            console.log('재료 데이터가 없거나 배열이 아닙니다');
            // 빈 그리드 표시
            this.hot.loadData([['', '', '', '', '', '', '', '', '', '', '']]);
            return;
        }

        const gridData = [];

        // 재료 데이터를 그리드 형식으로 변환 (올바른 필드명 사용)
        ingredients.forEach((ingredient) => {
            console.log('재료 처리 중:', ingredient);
            gridData.push([
                ingredient.ingredient_code || '',        // 식자재코드
                ingredient.ingredient_name || '',        // 식자재명
                '',                                      // 검색 버튼 (빈 칸)
                ingredient.specification || '',          // 규격
                ingredient.unit || '',                   // 단위
                ingredient.delivery_days || 0,           // 선발주일
                ingredient.selling_price || 0,           // 판매가
                ingredient.quantity || 0,                // 소요량 (quantity 필드 사용)
                ingredient.amount || 0,                  // 재료비 (amount 필드 사용)
                ingredient.supplier_name || '',          // 거래처명
                new Date().toISOString().slice(5, 10).replace(/-/g, '.') // 등록일
            ]);
        });

        console.log('변환된 그리드 데이터:', gridData);

        // 그리드에 데이터 로드
        try {
            this.hot.loadData(gridData);
            console.log('그리드에 데이터 로드 성공:', gridData.length + '개 행');

            // 총액 계산
            this.calculateTotal();
        } catch (error) {
            console.error('그리드 데이터 로드 오류:', error);
        }
    }

    /**
     * 엑셀 가져오기
     */
    importFromExcel() {
        alert('엑셀 파일을 선택하여 데이터를 가져올 수 있습니다.');
    }

    /**
     * 엑셀 내보내기
     */
    exportToExcel() {
        if (!this.hot) return;

        const exportPlugin = this.hot.getPlugin('exportFile');
        exportPlugin.downloadFile('csv', {
            filename: '메뉴_레시피_' + new Date().toLocaleDateString('ko-KR'),
            columnHeaders: true,
            rowHeaders: false
        });
    }

    /**
     * 사진 업로드 처리 - 사진 영역 클릭
     */
    handlePhotoClick() {
        const photoUpload = document.getElementById('photoUpload');
        if (photoUpload) {
            photoUpload.click();
        }
    }

    /**
     * 사진 업로드 처리 - 파일 선택
     */
    handlePhotoUpload(event) {
        const file = event.target.files[0];
        if (file && file.type.startsWith('image/')) {
            this.currentPhotoFile = file;
            this.currentPhotoType = 'file';
            this.currentPhotoUrl = null;

            const reader = new FileReader();
            reader.onload = (e) => {
                const photoPreview = document.getElementById('photoPreview');
                const photoPlaceholder = document.getElementById('photoPlaceholder');

                if (photoPreview && photoPlaceholder) {
                    photoPreview.src = e.target.result;
                    photoPreview.style.display = 'block';
                    photoPlaceholder.style.display = 'none';
                }
            };
            reader.readAsDataURL(file);
        }
    }

    /**
     * 기존 사진 사용 (링크로 참조)
     */
    async useExistingPhoto() {
        try {
            // 저장된 메뉴 목록에서 사진 선택 모달 표시
            const response = await fetch(`${this.CONFIG.API_BASE_URL}/api/recipe/list`);
            const data = await response.json();
            const existingMenus = data.recipes || [];

            const menusWithPhotos = existingMenus.filter(menu => menu.thumbnail_path);

            if (menusWithPhotos.length === 0) {
                alert('사용 가능한 사진이 없습니다.');
                return;
            }

            // 사진 선택 모달 생성
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
            `;

            const modalContent = document.createElement('div');
            modalContent.style.cssText = `
                background: white;
                border-radius: 8px;
                padding: 20px;
                max-width: 80%;
                max-height: 80vh;
                overflow-y: auto;
            `;

            modalContent.innerHTML = `
                <h3 style="margin-bottom: 15px;">기존 사진 선택</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px;">
                    ${menusWithPhotos.map(menu => `
                        <div style="cursor: pointer; border: 2px solid #ddd; border-radius: 8px; padding: 5px;"
                             onclick="window.selectExistingPhoto('${menu.thumbnail_path}', '${menu.recipe_name}')">
                            <img src="/${menu.thumbnail_path}" style="width: 100%; height: 120px; object-fit: cover; border-radius: 4px;">
                            <div style="text-align: center; font-size: 12px; margin-top: 5px;">${menu.recipe_name}</div>
                        </div>
                    `).join('')}
                </div>
                <button onclick="this.parentElement.parentElement.remove()" style="margin-top: 15px; padding: 8px 16px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">닫기</button>
            `;

            modal.appendChild(modalContent);
            document.body.appendChild(modal);
        } catch (error) {
            console.error('기존 사진 로드 오류:', error);
            alert('기존 사진을 불러오는데 실패했습니다.');
        }
    }

    /**
     * 기존 사진 선택
     */
    selectExistingPhoto(photoPath, menuName) {
        this.currentPhotoUrl = photoPath;
        this.currentPhotoType = 'existing';
        this.currentPhotoFile = null;

        const photoPreview = document.getElementById('photoPreview');
        const photoPlaceholder = document.getElementById('photoPlaceholder');

        if (photoPreview && photoPlaceholder) {
            photoPreview.src = '/' + photoPath;
            photoPreview.style.display = 'block';
            photoPlaceholder.style.display = 'none';
        }

        // 모달 닫기
        const modal = document.querySelector('div[style*="z-index: 10000"]');
        if (modal) modal.remove();
    }

    /**
     * 사진 제거
     */
    clearPhoto() {
        this.currentPhotoFile = null;
        this.currentPhotoUrl = null;
        this.currentPhotoType = null;

        const photoPreview = document.getElementById('photoPreview');
        const photoPlaceholder = document.getElementById('photoPlaceholder');
        const photoUpload = document.getElementById('photoUpload');

        if (photoPreview) photoPreview.style.display = 'none';
        if (photoPlaceholder) photoPlaceholder.style.display = 'block';
        if (photoUpload) photoUpload.value = '';
    }

    /**
     * 새 메뉴 만들기 버튼 클릭
     */
    createNewMenu() {
        console.log('새 메뉴 만들기 함수 호출됨');
        this.currentMenuId = null;

        const menuTitleElement = document.getElementById('menuTitle');
        if (menuTitleElement) {
            menuTitleElement.textContent = '새 메뉴 만들기';
            console.log('메뉴 제목을 "새 메뉴 만들기"로 변경');
        }

        // 검색창에 입력된 텍스트를 메뉴명으로 가져오기
        const searchText = document.getElementById('menuSearch')?.value.trim() || '';
        const menuNameElement = document.getElementById('menuName');
        if (menuNameElement) {
            menuNameElement.value = searchText;
        }

        const categoryInputs = document.querySelectorAll('input[name="category"]');
        categoryInputs.forEach(input => input.checked = false);

        this.resetGrid(true);  // skipConfirm = true로 설정하여 확인 메시지 생략
        this.clearPhoto();

        const cookingNoteElement = document.getElementById('cookingNote');
        if (cookingNoteElement) {
            cookingNoteElement.value = '';
        }

        if (menuNameElement) {
            menuNameElement.focus();
        }

        // 새 메뉴 만들기 시 '다른 이름으로 저장' 버튼 숨김
        const saveAsButton = document.getElementById('saveAsButton');
        if (saveAsButton) {
            saveAsButton.style.display = 'none';
        }
    }

    /**
     * 검색된 이름으로 새 메뉴 만들기
     */
    createNewMenuWithName(menuName) {
        this.createNewMenu();

        const menuNameElement = document.getElementById('menuName');
        if (menuNameElement) {
            menuNameElement.value = menuName;
        }

        // 첫 번째 카테고리 자동 선택
        const firstCategory = document.querySelector('input[name="category"]');
        if (firstCategory) {
            firstCategory.checked = true;
        }
    }
}

// 모듈을 전역으로 노출
window.MenuRecipeManagement = MenuRecipeManagement;

// 인스턴스 생성 및 자동 초기화
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('ingredientsGrid')) {
        window.menuRecipeManagementInstance = new MenuRecipeManagement();
        window.menuRecipeManagementInstance.init();

        // selectMenu 전역 함수 추가 (HTML onclick에서 사용)
        window.selectMenu = (menuId, element) => {
            window.menuRecipeManagementInstance.selectMenu(menuId, element);
        };

        console.log('✅ MenuRecipeManagement 초기화 완료');
    }
});