/**
 * Fortress Protection System
 * 시스템을 AI 어시스턴트의 무차별적 수정으로부터 보호
 */

class FortressProtection {
    constructor() {
        this.version = '1.0.0';
        this.protectedFiles = new Map();
        this.backupStates = new Map();
        this.violations = [];
        this.watchdog = null;
        this.checksum = this.generateSystemChecksum();
        this.init();
    }

    /**
     * 보호 시스템 초기화
     */
    init() {
        console.log('🛡️ Fortress Protection System initializing...');
        
        // 보호된 파일들 등록
        this.registerProtectedFiles();
        
        // 감시 시작
        this.startWatchdog();
        
        // 전역 오류 처리
        this.setupGlobalErrorHandling();
        
        // DOM 보호
        this.protectDOM();
        
        // 콘솔 보호
        this.protectConsole();
        
        console.log('✅ Fortress Protection System active');
    }

    /**
     * 보호된 파일들 등록
     */
    registerProtectedFiles() {
        const protectedFiles = [
            '/system/core/framework.js',
            '/system/core/module-registry.js', 
            '/system/core/api-gateway.js',
            '/system/core/protection.js',
            '/admin_dashboard_fortress.html'
        ];

        protectedFiles.forEach(file => {
            this.protectedFiles.set(file, {
                path: file,
                checksum: this.calculateFileChecksum(file),
                protected: true,
                lastCheck: Date.now()
            });
        });

        console.log(`🔒 ${protectedFiles.length} files protected`);
    }

    /**
     * 파일 체크섬 계산
     */
    calculateFileChecksum(filePath) {
        // 실제 구현에서는 파일 내용의 해시를 계산
        return `fortress_${filePath.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}`;
    }

    /**
     * 시스템 체크섬 생성
     */
    generateSystemChecksum() {
        const systemInfo = {
            framework: window.Fortress?.version || 'unknown',
            modules: window.ModuleRegistry ? Object.keys(window.ModuleRegistry.getModuleStatus()).length : 0,
            protection: this.version,
            timestamp: Date.now()
        };
        
        return JSON.stringify(systemInfo);
    }

    /**
     * 감시 시스템 시작
     */
    startWatchdog() {
        if (this.watchdog) return;
        
        this.watchdog = setInterval(() => {
            this.performIntegrityCheck();
        }, 30000); // 30초마다 검사

        // 페이지 언로드 시 정리
        window.addEventListener('beforeunload', () => {
            if (this.watchdog) {
                clearInterval(this.watchdog);
            }
        });

        console.log('🐕 Watchdog started (30s interval)');
    }

    /**
     * 무결성 검사
     */
    performIntegrityCheck() {
        let violations = 0;

        // 시스템 체크섬 검증
        const currentChecksum = this.generateSystemChecksum();
        if (currentChecksum !== this.checksum) {
            console.warn('⚠️ System checksum changed');
            this.logViolation('SYSTEM_CHECKSUM_CHANGED', 'System integrity compromised');
        }

        // 핵심 객체 존재 확인
        const coreObjects = ['Fortress', 'ModuleRegistry', 'APIGateway'];
        for (const obj of coreObjects) {
            if (!window[obj]) {
                console.error(`❌ Core object missing: ${obj}`);
                this.logViolation('CORE_OBJECT_MISSING', `${obj} object not found`);
                violations++;
            }
        }

        // DOM 보호 확인
        const protectedElements = document.querySelectorAll('.fortress-protected');
        for (const element of protectedElements) {
            if (!element.getAttribute('data-fortress-protected')) {
                this.protectElement(element);
            }
        }

        if (violations > 0) {
            console.warn(`🚨 ${violations} integrity violations detected`);
            this.handleViolations();
        }

        return violations === 0;
    }

    /**
     * 위반 사항 로깅
     */
    logViolation(type, message) {
        const violation = {
            type,
            message,
            timestamp: Date.now(),
            stack: new Error().stack
        };

        this.violations.push(violation);
        
        // 최대 100개까지만 보관
        if (this.violations.length > 100) {
            this.violations = this.violations.slice(-100);
        }

        console.warn('🚨 Protection violation:', violation);
    }

    /**
     * 위반 사항 처리
     */
    handleViolations() {
        const recentViolations = this.violations.filter(v => 
            Date.now() - v.timestamp < 60000 // 최근 1분
        );

        if (recentViolations.length >= 5) {
            console.error('🚨 Too many violations! Initiating recovery...');
            this.initiateRecovery();
        }
    }

    /**
     * 시스템 복구
     */
    initiateRecovery() {
        console.log('🔄 Starting system recovery...');
        
        // 백업 상태가 있으면 복원
        if (this.backupStates.size > 0) {
            console.log('📦 Restoring from backup...');
            this.restoreFromBackup();
        } else {
            console.log('🔄 Performing hard reset...');
            this.performHardReset();
        }
    }

    /**
     * 백업에서 복원
     */
    restoreFromBackup() {
        try {
            for (const [key, backup] of this.backupStates.entries()) {
                if (window[key] && typeof backup === 'object') {
                    Object.assign(window[key], backup);
                }
            }
            console.log('✅ System restored from backup');
        } catch (error) {
            console.error('❌ Backup restoration failed:', error);
            this.performHardReset();
        }
    }

    /**
     * 하드 리셋
     */
    performHardReset() {
        const confirmReset = confirm(
            '🚨 시스템 무결성이 손상되었습니다.\n' +
            '안전한 상태로 복원하기 위해 페이지를 새로고침하시겠습니까?'
        );

        if (confirmReset) {
            window.location.reload();
        }
    }

    /**
     * DOM 보호
     */
    protectDOM() {
        // MutationObserver로 DOM 변경 감시
        if (typeof MutationObserver === 'undefined') return;

        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                // 보호된 요소 감시
                if (mutation.target.classList?.contains('fortress-protected')) {
                    this.validateProtectedElement(mutation.target);
                }

                // 새로 추가된 노드 중 보호된 것들 확인
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const protectedElements = node.querySelectorAll?.('.fortress-protected');
                        protectedElements?.forEach(element => this.protectElement(element));
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class', 'id', 'data-fortress-protected']
        });

        console.log('🛡️ DOM protection active');
    }

    /**
     * 요소 보호
     */
    protectElement(element) {
        if (element.getAttribute('data-fortress-protected')) return;

        element.setAttribute('data-fortress-protected', 'true');
        
        // 변경 방지 이벤트 리스너
        const preventModification = (e) => {
            console.warn('🛡️ Attempted modification of protected element blocked');
            e.preventDefault();
            return false;
        };

        element.addEventListener('DOMNodeRemoved', preventModification);
        element.addEventListener('DOMNodeInserted', preventModification);
    }

    /**
     * 보호된 요소 검증
     */
    validateProtectedElement(element) {
        if (!element.getAttribute('data-fortress-protected')) {
            console.warn('🚨 Protected element lost protection attribute');
            this.protectElement(element);
        }
    }

    /**
     * 콘솔 보호
     */
    protectConsole() {
        const originalConsole = { ...console };

        // 위험한 콘솔 명령어 감시
        const dangerousPatterns = [
            /delete\s+window\./,
            /window\.\w+\s*=\s*null/,
            /Fortress/,
            /ModuleRegistry/,
            /APIGateway/
        ];

        const protectConsoleMethod = (method) => {
            const original = console[method];
            console[method] = function(...args) {
                const message = args.join(' ');
                
                // 위험한 패턴 검사
                for (const pattern of dangerousPatterns) {
                    if (pattern.test(message)) {
                        console.warn(`🛡️ Potentially dangerous console operation blocked: ${method}`);
                        return;
                    }
                }
                
                return original.apply(console, args);
            };
        };

        // 주요 콘솔 메서드 보호
        ['log', 'warn', 'error', 'debug'].forEach(protectConsoleMethod);

        console.log('🛡️ Console protection active');
    }

    /**
     * 전역 오류 처리
     */
    setupGlobalErrorHandling() {
        window.addEventListener('error', (event) => {
            if (event.filename && this.protectedFiles.has(event.filename)) {
                console.error('🚨 Error in protected file:', event.filename);
                this.logViolation('PROTECTED_FILE_ERROR', `Error in ${event.filename}: ${event.message}`);
            }
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('🚨 Unhandled promise rejection:', event.reason);
            this.logViolation('UNHANDLED_REJECTION', `Unhandled rejection: ${event.reason}`);
        });

        console.log('🛡️ Global error handling active');
    }

    /**
     * 백업 생성
     */
    createBackup(key, object) {
        if (typeof object === 'object' && object !== null) {
            this.backupStates.set(key, JSON.parse(JSON.stringify(object)));
            console.log(`📦 Backup created for: ${key}`);
        }
    }

    /**
     * 보호 통계
     */
    getProtectionStats() {
        return {
            version: this.version,
            protectedFiles: this.protectedFiles.size,
            violations: this.violations.length,
            recentViolations: this.violations.filter(v => Date.now() - v.timestamp < 300000).length,
            watchdogActive: !!this.watchdog,
            lastCheck: Math.max(...Array.from(this.protectedFiles.values()).map(f => f.lastCheck)),
            uptime: Date.now() - this.startTime
        };
    }

    /**
     * 보호 비활성화 (개발용)
     */
    disable() {
        if (this.watchdog) {
            clearInterval(this.watchdog);
            this.watchdog = null;
        }
        console.log('🛡️ Protection disabled');
    }
}

// 전역 보호 시스템 인스턴스
window.FortressProtection = window.FortressProtection || new FortressProtection();

// 보호된 API 노출
window.ProtectionAPI = {
    getStats: () => window.FortressProtection.getProtectionStats(),
    getViolations: () => window.FortressProtection.violations.slice(),
    performCheck: () => window.FortressProtection.performIntegrityCheck()
};

console.log('🛡️ Fortress Protection System loaded');