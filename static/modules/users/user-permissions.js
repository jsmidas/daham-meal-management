/**
 * 사용자 권한 관리 모듈
 * 30개 이상의 사업장 권한을 효율적으로 관리하기 위한 듀얼 리스트 인터페이스
 */

class UserPermissionsManager {
    constructor() {
        this.availableSites = [];
        this.selectedSites = [];
        this.allSites = [];
        this.API_BASE_URL = window.CONFIG?.API?.BASE_URL || 'http://127.0.0.1:8010';
    }

    async init() {
        console.log('🔧 [UserPermissions] 권한 관리자 초기화');
        await this.loadAllSites();
        this.setupEventListeners();
    }

    async loadAllSites() {
        try {
            // 실제 데이터베이스에서 사업장 목록 로드
            const response = await fetch(`${this.API_BASE_URL}/api/admin/business-locations`);
            if (!response.ok) {
                throw new Error('사업장 목록 로드 실패');
            }
            const data = await response.json();
            this.allSites = data.locations || [];

            // 시뮬레이션: 10개의 사업장 추가 (실제로는 DB에서 가져옴)
            if (this.allSites.length < 10) {
                this.generateSimulatedSites();
            }

            this.refreshAvailableList();
        } catch (error) {
            console.error('사업장 로드 오류:', error);
            // 테스트용 데이터 생성
            this.generateSimulatedSites();
            this.refreshAvailableList();
        }
    }

    generateSimulatedSites() {
        // API 호출 실패 시 빈 배열 사용
        this.allSites = [];
        console.warn('사업장 데이터를 불러올 수 없습니다. API 연결을 확인하세요.');
    }

    setupEventListeners() {
        // 검색 기능
        const searchAvailable = document.getElementById('searchAvailableSites');
        const searchSelected = document.getElementById('searchSelectedSites');

        if (searchAvailable) {
            searchAvailable.addEventListener('input', (e) => this.filterAvailableList(e.target.value));
        }

        if (searchSelected) {
            searchSelected.addEventListener('input', (e) => this.filterSelectedList(e.target.value));
        }

        // 더블클릭으로 이동
        const availableSelect = document.getElementById('availableSites');
        const selectedSelect = document.getElementById('selectedSites');

        if (availableSelect) {
            availableSelect.addEventListener('dblclick', () => this.moveSelectedSites());
        }

        if (selectedSelect) {
            selectedSelect.addEventListener('dblclick', () => this.removeSelectedSites());
        }
    }

    refreshAvailableList(filter = '') {
        const availableSelect = document.getElementById('availableSites');
        if (!availableSelect) return;

        availableSelect.innerHTML = '';

        const availableSites = this.allSites.filter(site =>
            !this.selectedSites.some(selected => selected.id === site.id)
        );

        const filteredSites = filter ?
            availableSites.filter(site =>
                site.site_name.toLowerCase().includes(filter.toLowerCase()) ||
                site.site_code.toLowerCase().includes(filter.toLowerCase())
            ) : availableSites;

        filteredSites.forEach(site => {
            const option = document.createElement('option');
            option.value = site.id;
            option.textContent = `[${site.site_code}] ${site.site_name} (${site.site_type})`;
            option.dataset.siteData = JSON.stringify(site);
            availableSelect.appendChild(option);
        });

        this.updateCounts();
    }

    refreshSelectedList(filter = '') {
        const selectedSelect = document.getElementById('selectedSites');
        if (!selectedSelect) return;

        selectedSelect.innerHTML = '';

        const filteredSites = filter ?
            this.selectedSites.filter(site =>
                site.site_name.toLowerCase().includes(filter.toLowerCase()) ||
                site.site_code.toLowerCase().includes(filter.toLowerCase())
            ) : this.selectedSites;

        filteredSites.forEach(site => {
            const option = document.createElement('option');
            option.value = site.id;
            option.textContent = `[${site.site_code}] ${site.site_name} (${site.site_type})`;
            option.dataset.siteData = JSON.stringify(site);
            selectedSelect.appendChild(option);
        });

        this.updateCounts();
    }

    filterAvailableList(searchTerm) {
        this.refreshAvailableList(searchTerm);
    }

    filterSelectedList(searchTerm) {
        this.refreshSelectedList(searchTerm);
    }

    moveSelectedSites() {
        const availableSelect = document.getElementById('availableSites');
        if (!availableSelect) return;

        const selectedOptions = Array.from(availableSelect.selectedOptions);

        selectedOptions.forEach(option => {
            const siteData = JSON.parse(option.dataset.siteData);
            this.selectedSites.push(siteData);
        });

        this.refreshAvailableList();
        this.refreshSelectedList();
    }

    removeSelectedSites() {
        const selectedSelect = document.getElementById('selectedSites');
        if (!selectedSelect) return;

        const selectedOptions = Array.from(selectedSelect.selectedOptions);

        selectedOptions.forEach(option => {
            const siteId = parseInt(option.value);
            this.selectedSites = this.selectedSites.filter(site => site.id !== siteId);
        });

        this.refreshAvailableList();
        this.refreshSelectedList();
    }

    moveAllSites() {
        const availableSites = this.allSites.filter(site =>
            !this.selectedSites.some(selected => selected.id === site.id)
        );

        this.selectedSites = [...this.selectedSites, ...availableSites];

        this.refreshAvailableList();
        this.refreshSelectedList();
    }

    removeAllSites() {
        this.selectedSites = [];

        this.refreshAvailableList();
        this.refreshSelectedList();
    }

    selectByType(type) {
        const sitesToAdd = this.allSites.filter(site =>
            site.site_type === type &&
            !this.selectedSites.some(selected => selected.id === site.id)
        );

        this.selectedSites = [...this.selectedSites, ...sitesToAdd];

        this.refreshAvailableList();
        this.refreshSelectedList();
    }

    selectByRegion(region) {
        const sitesToAdd = this.allSites.filter(site =>
            site.region === region &&
            !this.selectedSites.some(selected => selected.id === site.id)
        );

        this.selectedSites = [...this.selectedSites, ...sitesToAdd];

        this.refreshAvailableList();
        this.refreshSelectedList();
    }

    updateCounts() {
        const availableCount = document.getElementById('availableCount');
        const selectedCount = document.getElementById('selectedCount');

        if (availableCount) {
            const available = this.allSites.filter(site =>
                !this.selectedSites.some(selected => selected.id === site.id)
            ).length;
            availableCount.textContent = available;
        }

        if (selectedCount) {
            selectedCount.textContent = this.selectedSites.length;
        }
    }

    getSelectedSiteIds() {
        return this.selectedSites.map(site => site.id);
    }

    setSelectedSites(siteIds) {
        this.selectedSites = this.allSites.filter(site =>
            siteIds.includes(site.id)
        );

        this.refreshAvailableList();
        this.refreshSelectedList();
    }

    reset() {
        this.selectedSites = [];
        this.refreshAvailableList();
        this.refreshSelectedList();
    }
}

// 전역 인스턴스 생성
if (!window.userPermissionsManager) {
    window.userPermissionsManager = new UserPermissionsManager();
}