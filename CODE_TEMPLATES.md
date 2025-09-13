# 📝 표준 코드 템플릿 - AI는 이것만 사용할 것!

## 🎯 **목적: AI가 매번 다른 방식을 쓰는 것을 방지**

### **Template 1: 데이터 로드 함수**
```javascript
// 복사해서 사용 - 절대 수정하지 말 것
async load[DataName]Data() {
    try {
        console.log('[ModuleName] [DataName] 로드 시작');
        this.isLoading = true;
        
        const response = await API.get('[ENDPOINT_KEY]');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        this.[dataName] = data.[dataField] || [];
        this.render[DataName]();
        
    } catch (error) {
        console.error('[ModuleName] [DataName] 로드 에러:', error);
        this.show[DataName]Error();
    } finally {
        this.isLoading = false;
    }
}
```

### **Template 2: 테이블 렌더링**
```javascript
// 복사해서 사용 - 절대 수정하지 말 것  
render[DataName]Table(data) {
    const tbody = document.querySelector('#[tableName] tbody');
    if (!tbody) {
        console.error('[ModuleName] 테이블을 찾을 수 없습니다');
        return;
    }
    
    if (!data || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="100%" class="text-center text-muted">데이터가 없습니다</td></tr>';
        return;
    }
    
    tbody.innerHTML = data.map((item, index) => `
        <tr>
            <td>${index + 1}</td>
            <td>${item.name || '미지정'}</td>
            <td>${item.value || '0'}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="[ModuleName].edit(${item.id})">수정</button>
                <button class="btn btn-sm btn-danger" onclick="[ModuleName].delete(${item.id})">삭제</button>
            </td>
        </tr>
    `).join('');
}
```

### **Template 3: 모달 처리**
```javascript
// 복사해서 사용 - 절대 수정하지 말 것
show[ActionName]Modal(data = {}) {
    const modal = new bootstrap.Modal(document.getElementById('[modalId]'));
    
    // 폼 초기화
    const form = document.getElementById('[formId]');
    if (form) {
        form.reset();
        
        // 데이터가 있으면 채우기 (수정 모드)
        if (data.id) {
            Object.keys(data).forEach(key => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) {
                    input.value = data[key] || '';
                }
            });
        }
    }
    
    modal.show();
}
```

### **Template 4: 에러 처리**
```javascript
// 복사해서 사용 - 절대 수정하지 말 것
show[DataName]Error(message = '데이터를 불러올 수 없습니다') {
    const container = document.querySelector('#[containerId]');
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <h4 class="alert-heading">오류 발생</h4>
                <p>${message}</p>
                <hr>
                <p class="mb-0">
                    <button class="btn btn-outline-danger" onclick="location.reload()">페이지 새로고침</button>
                </p>
            </div>
        `;
    }
}
```

### **Template 5: 검색 기능**
```javascript
// 복사해서 사용 - 절대 수정하지 말 것
setupSearch() {
    const searchInput = document.getElementById('[searchInputId]');
    if (!searchInput) return;
    
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const query = e.target.value.toLowerCase().trim();
            this.filterData(query);
        }, 300);
    });
}

filterData(query) {
    if (!query) {
        this.render[DataName]Table(this.original[DataName]);
        return;
    }
    
    const filtered = this.original[DataName].filter(item => 
        item.name?.toLowerCase().includes(query) ||
        item.code?.toLowerCase().includes(query) ||
        item.description?.toLowerCase().includes(query)
    );
    
    this.render[DataName]Table(filtered);
}
```

## 🏗️ **HTML 템플릿**

### **Template A: 관리 페이지 레이아웃**
```html
<!-- 복사해서 사용 - 구조 절대 변경 금지 -->
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>다함 식자재 관리 - [페이지명]</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="config.js"></script>
</head>
<body>
    <div class="container-fluid">
        <!-- 헤더 -->
        <div class="row mb-4">
            <div class="col-12">
                <h1 class="text-primary">🍽️ [기능명] 관리</h1>
                <nav aria-label="breadcrumb">
                    <ol class="breadcrumb">
                        <li class="breadcrumb-item"><a href="admin_dashboard.html">관리자</a></li>
                        <li class="breadcrumb-item active">[기능명]</li>
                    </ol>
                </nav>
            </div>
        </div>
        
        <!-- 컨트롤 영역 -->
        <div class="row mb-3">
            <div class="col-md-8">
                <div class="input-group">
                    <input type="text" id="searchInput" class="form-control" placeholder="[항목명] 검색...">
                    <button class="btn btn-outline-secondary" type="button">🔍</button>
                </div>
            </div>
            <div class="col-md-4 text-end">
                <button class="btn btn-success" onclick="[ModuleName].showAddModal()">➕ [항목명] 추가</button>
            </div>
        </div>
        
        <!-- 데이터 테이블 -->
        <div class="row">
            <div class="col-12">
                <div class="table-responsive">
                    <table class="table table-striped" id="[tableName]">
                        <thead class="table-dark">
                            <tr>
                                <th>번호</th>
                                <th>[컬럼명1]</th>
                                <th>[컬럼명2]</th>
                                <th>관리</th>
                            </tr>
                        </thead>
                        <tbody>
                            <!-- 동적 생성 -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- 모달은 body 끝에 -->
    <div class="modal fade" id="[modalId]" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">[항목명] 관리</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="[formId]">
                        <!-- 폼 내용 -->
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">취소</button>
                    <button type="button" class="btn btn-primary" onclick="[ModuleName].save()">저장</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="static/modules/[module-name]/[module-name].js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            window.[ModuleName] = new [ModuleName]Module();
        });
    </script>
</body>
</html>
```

## 📋 **사용 지침**

### **AI가 새 기능 개발 시**
1. **해당하는 템플릿을 복사** (절대 처음부터 작성하지 말 것)
2. **[대괄호] 부분만 교체**
   - `[ModuleName]` → `Suppliers`
   - `[DataName]` → `Suppliers` 
   - `[tableName]` → `suppliersTable`
3. **로직만 추가**, 구조는 절대 변경 금지

### **금지사항**
- ❌ 템플릿을 "개선"하려고 하지 말 것
- ❌ "더 좋은 방법"이라며 구조 변경 금지  
- ❌ 새로운 라이브러리나 패턴 도입 금지
- ❌ CSS 클래스명 임의 변경 금지

### **허용사항**  
- ✅ `[대괄호]` 부분 교체
- ✅ 테이블 컬럼 추가/제거
- ✅ 폼 필드 추가/제거
- ✅ 특정 비즈니스 로직 추가

---
**💡 AI야, 창의성은 필요없다! 템플릿만 복사해서 대괄호만 바꿔라! 그게 일관성이다!**