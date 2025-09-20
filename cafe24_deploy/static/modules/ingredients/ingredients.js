// 식자재 관리 모듈
(function() {
'use strict';

// 식자재 관련 변수
let uploadedFiles = [];
let uploadHistory = [];

// 정확한 필드 헤더 (띄어쓰기, 괄호 포함 - 매우 중요!)
const FIELD_HEADERS = [
    '분류(대분류)',
    '기본식자재(세분류)',
    '고유코드',
    '식자재명',
    '원산지',
    '게시유무',
    '규격',
    '단위',
    '면세',
    '선발주일',
    '입고가',
    '판매가',
    '거래처명',
    '비고',
    '등록일'
];

// IngredientsModule 객체 (다른 모듈과 일관성 유지)
window.IngredientsModule = {
    currentPage: 1,
    totalPages: 1,
    editingId: null,

    // 모듈 초기화
    async init() {
        // console.log('🥬 Ingredients Module 초기화');
        await this.loadIngredients();
        await this.loadIngredientStatistics();
        this.setupEventListeners();
        return this;
    },

    // 단위당 단가 재계산
    async recalculateUnitPrices() {
        // 확인 대화상자
        if (!confirm('모든 식자재의 단위당 단가를 재계산하시겠습니까?\n\n약 85,000개의 데이터를 처리하므로 1-2분 정도 소요될 수 있습니다.')) {
            return;
        }

        // 진행 상태 표시를 위한 모달 생성
        const progressModal = document.createElement('div');
        progressModal.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            z-index: 10000;
            min-width: 400px;
            text-align: center;
        `;
        progressModal.innerHTML = `
            <h3 style="margin-bottom: 20px;">🔄 단위당 단가 재계산 중...</h3>
            <div style="margin-bottom: 15px;">
                <div style="background: #f0f0f0; border-radius: 10px; height: 30px; overflow: hidden;">
                    <div id="progressBar" style="background: linear-gradient(90deg, #4CAF50, #45a049); height: 100%; width: 0%; transition: width 0.3s; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                        0%
                    </div>
                </div>
            </div>
            <p id="progressText" style="color: #666;">재계산을 시작하는 중...</p>
            <p style="font-size: 12px; color: #999; margin-top: 10px;">잠시만 기다려주세요.</p>
        `;
        document.body.appendChild(progressModal);

        // 배경 오버레이
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 9999;
        `;
        document.body.appendChild(overlay);

        try {
            const API_BASE_URL = window.CONFIG?.API?.BASE_URL || 'http://127.0.0.1:8010';

            // 진행률 시뮬레이션 (실제 진행 상황을 알 수 없으므로)
            let progress = 0;
            const progressInterval = setInterval(() => {
                if (progress < 90) {
                    progress += Math.random() * 10;
                    progress = Math.min(progress, 90);
                    document.getElementById('progressBar').style.width = progress + '%';
                    document.getElementById('progressBar').textContent = Math.floor(progress) + '%';
                    document.getElementById('progressText').textContent = `약 ${Math.floor(progress * 850)}개 처리 중...`;
                }
            }, 500);

            const response = await fetch(`${API_BASE_URL}/api/admin/ingredients/recalculate-unit-prices`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            clearInterval(progressInterval);

            if (response.ok) {
                const result = await response.json();

                // 완료 표시
                document.getElementById('progressBar').style.width = '100%';
                document.getElementById('progressBar').textContent = '100%';
                document.getElementById('progressText').textContent = '재계산 완료!';

                setTimeout(() => {
                    document.body.removeChild(progressModal);
                    document.body.removeChild(overlay);

                    alert(`✅ 단위당 단가 재계산 완료!\n\n${result.message}`);

                    // 테이블 새로고침
                    this.loadIngredients();
                }, 1000);
            } else {
                throw new Error('재계산 실패');
            }
        } catch (error) {
        // console.error('재계산 오류:', error);
            document.body.removeChild(progressModal);
            document.body.removeChild(overlay);
            alert('❌ 재계산 중 오류가 발생했습니다.\n\n' + error.message);
        }
    },

    // 이벤트 리스너 설정
    setupEventListeners() {
        const searchInput = document.getElementById('ingredients-search');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchIngredients();
                }
            });
        }
    },

    // 식자재 목록 로드
    async loadIngredients() {
        try {
            const search = document.getElementById('ingredients-search')?.value || '';
            const category = document.getElementById('ingredient-category-filter')?.value || '';
            const page = this.currentPage || 1;
            
            let url = `${window.CONFIG?.API_BASE_URL || 'http://127.0.0.1:8010'}/api/admin/ingredients-new?page=${page}&limit=20`;
            if (search) url += `&search=${encodeURIComponent(search)}`;
            if (category) url += `&category=${encodeURIComponent(category)}`;
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                this.displayIngredients(data.ingredients || []);
                this.updatePagination(data.currentPage || 1, data.totalPages || 1);
            }
        } catch (error) {
        // console.error('식자재 목록 로드 실패:', error);
            const tbody = document.getElementById('ingredients-table-body');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="11">식자재 목록을 불러올 수 없습니다.</td></tr>';
            }
        }
    },

    // 식자재 통계 로드
    async loadIngredientStatistics() {
        try {
            const response = await fetch(`${window.CONFIG?.API_BASE_URL || 'http://127.0.0.1:8010'}/api/admin/ingredients-new?page=1&limit=100`);
            const data = await response.json();
            
            if (data.success && data.ingredients) {
                const ingredients = data.ingredients;
                const totalCount = ingredients.length;
                const activeCount = ingredients.filter(i => i.posting_status === '게시' || i.posting_status === '활성').length;
                const vegetableCount = ingredients.filter(i => i.category && i.category.includes('채소')).length;
                const meatCount = ingredients.filter(i => i.category && i.category.includes('육류')).length;
                const seafoodCount = ingredients.filter(i => i.category && i.category.includes('생선')).length;

                // 통계 카드 업데이트
                this.updateStatistics({
                    total: totalCount,
                    active: activeCount,
                    vegetable: vegetableCount,
                    meat: meatCount,
                    seafood: seafoodCount
                });
            }
        } catch (error) {
        // console.error('식자재 통계 로드 실패:', error);
        }
    },

    // 통계 업데이트
    updateStatistics(stats) {
        const totalElement = document.getElementById('total-ingredients-count');
        const activeTextElement = document.getElementById('active-ingredients-text');
        const vegetableElement = document.getElementById('vegetable-count');
        const meatElement = document.getElementById('meat-count');
        const seafoodElement = document.getElementById('seafood-count');

        if (totalElement) totalElement.textContent = stats.total;
        if (activeTextElement) activeTextElement.textContent = `게시: ${stats.active}개`;
        if (vegetableElement) vegetableElement.textContent = stats.vegetable;
        if (meatElement) meatElement.textContent = stats.meat;
        if (seafoodElement) seafoodElement.textContent = stats.seafood;
    },

    // 식자재 목록 표시
    displayIngredients(ingredients) {
        const tbody = document.getElementById('ingredients-table-body');
        if (!tbody) return;

        if (!ingredients || ingredients.length === 0) {
            tbody.innerHTML = '<tr><td colspan="16">등록된 식자재가 없습니다.</td></tr>';
            return;
        }

        // 단위당 단가 포매팅 함수
        const formatUnitPrice = (price) => {
            if (!price || price === 0) return '-';
            return `<span style="color: #007bff; font-weight: 600;">${Number(price).toFixed(1)}</span>`;
        };

        tbody.innerHTML = ingredients.map(ingredient => `
            <tr>
                <td>${ingredient.category || '-'}</td>
                <td>${ingredient.sub_category || '-'}</td>
                <td>${ingredient.ingredient_code || '-'}</td>
                <td>${ingredient.ingredient_name || '-'}</td>
                <td>${ingredient.origin || '-'}</td>
                <td>${ingredient.posting_status || '미지정'}</td>
                <td>${ingredient.specification || '-'}</td>
                <td>${ingredient.unit || '-'}</td>
                <td>${ingredient.tax_type || '-'}</td>
                <td>${ingredient.delivery_days || '-'}</td>
                <td>${formatUnitPrice(ingredient.price_per_unit)}</td>
                <td>${ingredient.purchase_price ? Number(ingredient.purchase_price).toLocaleString() : '-'}</td>
                <td>${ingredient.selling_price ? Number(ingredient.selling_price).toLocaleString() : '-'}</td>
                <td>${ingredient.supplier_name || '-'}</td>
                <td>${ingredient.notes || '-'}</td>
                <td>${ingredient.created_at ? new Date(ingredient.created_at).toLocaleDateString('ko-KR') : '-'}</td>
            </tr>
        `).join('');
    },

    // 페이지네이션 업데이트
    updatePagination(current, total) {
        this.currentPage = current;
        this.totalPages = total;
        const pageInfo = document.getElementById('ingredients-page-info');
        if (pageInfo) {
            pageInfo.textContent = `${current} / ${total}`;
        }
    },

    // 검색
    searchIngredients() {
        this.currentPage = 1;
        this.loadIngredients();
    },

    // 새 식자재 추가 모달
    showAddModal() {
        // console.log('새 식자재 추가 모달');
        alert('새 식자재 추가 기능 (구현 예정)');
    },

    // 식자재 수정
    editIngredient(id) {
        // console.log('식자재 수정:', id);
        alert(`식자재 수정 기능 - ID: ${id} (구현 예정)`);
    },

    // 상태 토글
    toggleStatus(id) {
        // console.log('식자재 상태 토글:', id);
        alert(`식자재 상태 토글 기능 - ID: ${id} (구현 예정)`);
    },

    // 식자재 삭제
    deleteIngredient(id) {
        if (!confirm('정말로 이 식자재를 삭제하시겠습니까?')) {
            return;
        }
        // console.log('식자재 삭제:', id);
        alert(`식자재 삭제 기능 - ID: ${id} (구현 예정)`);
    },

    // 템플릿 다운로드
    downloadTemplate() {
        const link = document.createElement('a');
        link.href = '/sample-data/food-template.xls';
        link.download = '식자재_업로드_템플릿.xls';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    // 오류 데이터 다운로드
    downloadErrors() {
        if (!this.errorData || this.errorData.length === 0) {
            alert('다운로드할 오류 데이터가 없습니다.');
            return;
        }
        // 오류 데이터를 CSV로 변환하여 다운로드
        const csvContent = this.convertToCSV(this.errorData);
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `오류_데이터_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    // 파일 선택 처리
    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        const fileInfo = document.getElementById('file-info');
        const fileName = document.getElementById('file-name');
        const fileSize = document.getElementById('file-size');

        if (fileInfo && fileName && fileSize) {
            fileName.textContent = file.name;
            fileSize.textContent = `(${(file.size / 1024 / 1024).toFixed(2)} MB)`;
            fileInfo.style.display = 'flex';
        }

        this.selectedFile = file;
    },

    // CSV 변환
    convertToCSV(data) {
        const fieldHeaders = [
            '분류(대분류)', '기본식자재(세분류)', '고유코드', '식자재명',
            '원산지', '게시유무', '규격', '단위', '면세', '선발주일',
            '입고가', '판매가', '거래처명', '비고', '등록일'
        ];
        const headers = fieldHeaders.join(',');
        const rows = data.map(row =>
            fieldHeaders.map(header => row[header] || '').join(',')
        );
        return headers + '\n' + rows.join('\n');
    },

    // 단위당 단가 계산
    calculatePricePerUnit() {
        // console.log('단위당 단가 계산 시작...');

        // price-per-gram 모듈이 있으면 사용
        if (window.PricePerGramModule) {
            window.PricePerGramModule.calculateAll();
        } else {
            // 간단한 계산 로직
            const ingredients = document.querySelectorAll('#ingredients-table-body tr');
            ingredients.forEach(row => {
                const priceCell = row.querySelector('td:nth-child(6)'); // 입고가
                const specCell = row.querySelector('td:nth-child(7)'); // 규격

                if (priceCell && specCell) {
                    const price = parseFloat(priceCell.textContent.replace(/[^\d]/g, ''));
                    const specText = specCell.textContent;

                    // 규격에서 무게 추출 (예: "1kg", "500g", "2.5kg")
                    const weightMatch = specText.match(/(\d+(?:\.\d+)?)\s*(kg|g)/i);
                    if (weightMatch) {
                        const weight = parseFloat(weightMatch[1]);
                        const unit = weightMatch[2].toLowerCase();
                        const grams = unit === 'kg' ? weight * 1000 : weight;

                        if (grams > 0) {
                            const pricePerGram = (price / grams).toFixed(2);
        // console.log(`${specText}: ₩${pricePerGram}/단위`);
                        }
                    }
                }
            });
        }

        alert('단위당 단가 계산이 완료되었습니다. 콘솔에서 결과를 확인하세요.');
    }
};

// 식자재 관리 페이지 초기화
function initializeIngredientsPage() {
        // console.log('식자재 관리 모듈 초기화');
    setupEventListeners();
    loadUploadHistory();
}

// 이벤트 리스너 설정
function setupEventListeners() {
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.querySelector('.upload-area');
    
    if (fileInput && uploadArea) {
        // 파일 선택 이벤트
        fileInput.addEventListener('change', handleFileSelect);
        
        // 드래그 앤 드롭 이벤트
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleFileDrop);
    }
    
    // 날짜 필터 기본값 설정
    const today = new Date().toISOString().split('T')[0];
    const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    const dateToElement = document.getElementById('date-to');
    const dateFromElement = document.getElementById('date-from');
    
    if (dateToElement) dateToElement.value = today;
    if (dateFromElement) dateFromElement.value = weekAgo;
}

// 파일 업로드 섹션 토글
function showUploadSection() {
    const uploadSection = document.getElementById('upload-section');
    const historySection = document.getElementById('upload-history-section');
    
    if (!uploadSection) return;
    
    // 다른 섹션 숨기기
    if (historySection && historySection.style.display !== 'none') {
        historySection.style.display = 'none';
    }
    
    const isVisible = uploadSection.style.display !== 'none';
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
        link.href = '/sample-data/food-template.xls';
        link.download = '식자재_업로드_양식_샘플.xls';
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // 다운로드 성공 메시지
        showNotification('📋 양식 다운로드가 시작되었습니다.', 'success');
    } catch (error) {
        // console.error('양식 다운로드 실패:', error);
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
        // console.log('선택된 파일들:', uploadedFiles.map(f => f.name));
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
        // console.log('★★★ MODULAR uploadFiles 함수 호출됨 - 실제 서버 업로드 시작 ★★★');
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
                success: result.failedRows === 0,
                processedRows: result.processedRows,
                successRows: result.successRows,
                failedRows: result.failedRows,
                errors: result.errors || [],
                message: result.message || ''
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
        // console.error('업로드 실패:', error);
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
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border: 1px solid #eee; border-radius: 4px; margin-bottom: 8px; background: ${isSuccess ? '#f8fff8' : '#fff8f8'}; cursor: pointer;" onclick="showUploadResultDetail(${JSON.stringify(result).replace(/"/g, '&quot;')})">
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
        // console.log('🚀 uploadFileToServer 함수 시작 - 파일:', file.name);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        // console.log('🌐 서버 요청 시작 - /api/admin/upload-ingredients');
        const response = await fetch('http://localhost:9000/api/admin/upload-ingredients', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success && result.details) {
        // console.log(`파일 업로드 완료: ${file.name} - ${result.details.total_rows}행 처리됨 (신규: ${result.details.new_count}, 업데이트: ${result.details.updated_count}, 실패: ${result.details.error_count})`);
            return {
                processedRows: result.details.total_rows,
                successRows: result.details.new_count + result.details.updated_count,
                failedRows: result.details.error_count,
                errors: result.details.errors || [],
                message: result.message || ''
            };
        } else if (result.success) {
            // 이전 형식 지원 (details 없는 경우)
        // console.log(`파일 업로드 완료: ${file.name} - ${result.total || 0}행 처리됨`);
            return {
                processedRows: result.total || 0,
                successRows: result.processed || 0,
                failedRows: result.errors || 0
            };
        } else {
            throw new Error(result.message || '업로드 실패');
        }
    } catch (error) {
        // console.error('업로드 오류:', error);
        throw error;
    }
}

// simulateFileUpload 함수가 제거됨 - 실제 서버 업로드만 사용

// 업로드 히스토리 로드
function loadUploadHistory() {
    // 실제 구현에서는 API에서 데이터를 가져옴
        // console.log('업로드 히스토리 로드됨');
}

// 업로드 결과 상세 팝업 표시 - 전역 함수로 선언
window.showUploadResultDetail = function(result) {
    const isSuccess = result.failedRows === 0;
    
    // 팝업 HTML 생성
    const popupHtml = `
        <div id="resultDetailModal" class="modal" style="display: block; position: fixed; z-index: 10000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5);">
            <div class="modal-content" style="background-color: #fefefe; margin: 5% auto; padding: 20px; border: 1px solid #888; width: 80%; max-width: 800px; max-height: 80vh; overflow-y: auto; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2 style="color: ${isSuccess ? '#28a745' : '#dc3545'};">
                        <i class="bi bi-${isSuccess ? 'check-circle' : 'exclamation-triangle'}"></i>
                        업로드 ${isSuccess ? '성공' : '결과'}
                    </h2>
                    <span onclick="closeResultModal()" style="color: #aaa; font-size: 28px; font-weight: bold; cursor: pointer;">&times;</span>
                </div>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h4>${result.fileName}</h4>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px;">
                        <div>
                            <strong>전체 행:</strong> ${result.processedRows}개
                        </div>
                        <div style="color: #28a745;">
                            <strong>성공:</strong> ${result.successRows}개
                        </div>
                        <div style="color: #dc3545;">
                            <strong>실패:</strong> ${result.failedRows}개
                        </div>
                    </div>
                </div>
                
                ${!isSuccess && result.errors && result.errors.length > 0 ? `
                    <div style="margin-top: 20px;">
                        <h4 style="color: #dc3545;">오류 상세 (최대 10개 표시)</h4>
                        <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 5px; padding: 15px; max-height: 300px; overflow-y: auto;">
                            <ul style="margin: 0; padding-left: 20px;">
                                ${result.errors.map(error => `<li style="margin: 5px 0; color: #856404;">${error}</li>`).join('')}
                            </ul>
                        </div>
                        ${result.failedRows > 10 ? `<p style="color: #6c757d; margin-top: 10px;">... 외 ${result.failedRows - 10}개 오류</p>` : ''}
                    </div>
                ` : ''}
                
                ${isSuccess ? `
                    <div style="text-align: center; margin-top: 20px;">
                        <i class="bi bi-check-circle" style="font-size: 48px; color: #28a745;"></i>
                        <p style="margin-top: 15px; font-size: 18px;">모든 데이터가 성공적으로 처리되었습니다!</p>
                    </div>
                ` : ''}
                
                <div style="text-align: right; margin-top: 30px;">
                    <button onclick="closeResultModal()" style="padding: 10px 30px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">확인</button>
                </div>
            </div>
        </div>
    `;
    
    // 팝업을 body에 추가
    document.body.insertAdjacentHTML('beforeend', popupHtml);
}

// 팝업 닫기 - 전역 함수로 선언
window.closeResultModal = function() {
    const modal = document.getElementById('resultDetailModal');
    if (modal) {
        modal.remove();
    }
}

// 업체별 필터링
function filterUploadHistory() {
    const supplierFilter = document.getElementById('supplier-filter')?.value;
        // console.log('업체별 필터:', supplierFilter);
    showNotification('업체별 필터가 적용되었습니다.', 'info');
}

// 업로드 이력 검색
function searchUploadHistory() {
    const supplierFilter = document.getElementById('supplier-filter')?.value;
    const dateFrom = document.getElementById('date-from')?.value;
    const dateTo = document.getElementById('date-to')?.value;
    
        // console.log('업로드 이력 검색:', { supplierFilter, dateFrom, dateTo });
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

// 이미지 모달 관련 함수 - 전역으로 노출
window.showImageModal = function() {
    const modal = document.getElementById('imageModal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
};

window.hideImageModal = function() {
    const modal = document.getElementById('imageModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
};

// 호환성을 위한 별칭 추가
window.IngredientManagement = window.IngredientsModule;

})(); // IIFE 종료