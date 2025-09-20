// 식자재 관리 모듈
(function() {
'use strict';

// 식자재 관련 변수
let uploadedFiles = [];
let uploadHistory = [];

// 식자재 관리 페이지 초기화
function initializeIngredientsPage() {
    console.log('식자재 관리 모듈 초기화');
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
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('http://localhost:9000/api/admin/upload-ingredients', {
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

})(); // IIFE 종료