/**
 * 🔍 System Monitoring Agent
 * 시스템 전체 성능 모니터링, 에러 로그 수집, 리소스 사용량 추적
 */

define('monitoring-agent', ['navigation'], (deps) => {

    return {
        name: 'monitoring-agent',
        version: '1.0.0',
        protected: true,

        // 내부 상태
        state: {
            isMonitoring: false,
            systemMetrics: {
                cpuUsage: 0,
                memoryUsage: 0,
                diskUsage: 0,
                networkTraffic: { in: 0, out: 0 }
            },
            errorLogs: [],
            performanceData: [],
            alerts: [],
            clients: new Set(),
            monitoringInterval: null
        },

        // 설정
        config: {
            monitoringInterval: 5000, // 5초마다 모니터링
            maxErrorLogs: 1000,
            maxPerformanceData: 500,
            alertThresholds: {
                cpuUsage: 80,
                memoryUsage: 85,
                diskUsage: 90,
                errorRate: 10 // 분당 에러 개수
            }
        },

        // 초기화
        async init() {
            console.log('🔍 System Monitoring Agent initializing...');

            try {
                this.setupErrorCapture();
                this.setupPerformanceObserver();
                this.startMonitoring();
                this.setupWebSocket();

                console.log('✅ System Monitoring Agent initialized successfully');

                // 관리 인터페이스 등록
                if (window.Fortress) {
                    window.Fortress.registerInterface('monitoring', this.getPublicInterface());
                }

                return this;
            } catch (error) {
                console.error('❌ Failed to initialize Monitoring Agent:', error);
                throw error;
            }
        },

        // 공개 인터페이스
        getPublicInterface() {
            return {
                // 모니터링 시작/정지
                startMonitoring: () => this.startMonitoring(),
                stopMonitoring: () => this.stopMonitoring(),

                // 데이터 조회
                getSystemMetrics: () => ({ ...this.state.systemMetrics }),
                getErrorLogs: (limit = 50) => this.state.errorLogs.slice(-limit),
                getPerformanceData: (limit = 100) => this.state.performanceData.slice(-limit),
                getAlerts: () => [...this.state.alerts],

                // 설정
                updateConfig: (newConfig) => this.updateConfig(newConfig),
                getConfig: () => ({ ...this.config }),

                // 알림 관리
                clearAlerts: () => this.clearAlerts(),
                acknowledgeAlert: (alertId) => this.acknowledgeAlert(alertId),

                // 실시간 구독
                subscribe: (callback) => this.subscribe(callback),
                unsubscribe: (callback) => this.unsubscribe(callback)
            };
        },

        // 에러 캡처 설정
        setupErrorCapture() {
            // 전역 에러 핸들러
            const originalErrorHandler = window.onerror;
            window.onerror = (message, source, lineno, colno, error) => {
                this.logError({
                    type: 'javascript',
                    message: message,
                    source: source,
                    line: lineno,
                    column: colno,
                    stack: error?.stack,
                    timestamp: new Date().toISOString(),
                    userAgent: navigator.userAgent
                });

                if (originalErrorHandler) {
                    return originalErrorHandler(message, source, lineno, colno, error);
                }
            };

            // Promise rejection 핸들러
            window.addEventListener('unhandledrejection', (event) => {
                this.logError({
                    type: 'promise-rejection',
                    message: event.reason?.message || String(event.reason),
                    stack: event.reason?.stack,
                    timestamp: new Date().toISOString(),
                    userAgent: navigator.userAgent
                });
            });

            // Fetch API 에러 모니터링
            this.interceptFetchAPI();
        },

        // Fetch API 인터셉트
        interceptFetchAPI() {
            const originalFetch = window.fetch;
            window.fetch = async (...args) => {
                const startTime = performance.now();

                try {
                    const response = await originalFetch(...args);
                    const endTime = performance.now();

                    this.logAPICall({
                        url: args[0],
                        method: args[1]?.method || 'GET',
                        status: response.status,
                        duration: endTime - startTime,
                        timestamp: new Date().toISOString(),
                        success: response.ok
                    });

                    if (!response.ok) {
                        this.logError({
                            type: 'api-error',
                            message: `API Error: ${response.status} ${response.statusText}`,
                            url: args[0],
                            status: response.status,
                            timestamp: new Date().toISOString()
                        });
                    }

                    return response;
                } catch (error) {
                    const endTime = performance.now();

                    this.logAPICall({
                        url: args[0],
                        method: args[1]?.method || 'GET',
                        status: 0,
                        duration: endTime - startTime,
                        timestamp: new Date().toISOString(),
                        success: false,
                        error: error.message
                    });

                    this.logError({
                        type: 'network-error',
                        message: `Network Error: ${error.message}`,
                        url: args[0],
                        timestamp: new Date().toISOString()
                    });

                    throw error;
                }
            };
        },

        // 성능 관찰자 설정
        setupPerformanceObserver() {
            if ('PerformanceObserver' in window) {
                try {
                    // 페이지 로드 성능
                    const observer = new PerformanceObserver((list) => {
                        for (const entry of list.getEntries()) {
                            this.logPerformance({
                                type: entry.entryType,
                                name: entry.name,
                                duration: entry.duration,
                                startTime: entry.startTime,
                                timestamp: new Date().toISOString()
                            });
                        }
                    });

                    observer.observe({ entryTypes: ['navigation', 'resource', 'measure'] });
                } catch (error) {
                    console.warn('⚠️ PerformanceObserver not supported:', error);
                }
            }
        },

        // 모니터링 시작
        startMonitoring() {
            if (this.state.isMonitoring) return;

            this.state.isMonitoring = true;
            this.state.monitoringInterval = setInterval(() => {
                this.collectSystemMetrics();
                this.checkAlerts();
                this.broadcastUpdate();
            }, this.config.monitoringInterval);

            console.log('🟢 System monitoring started');
        },

        // 모니터링 정지
        stopMonitoring() {
            if (!this.state.isMonitoring) return;

            this.state.isMonitoring = false;
            if (this.state.monitoringInterval) {
                clearInterval(this.state.monitoringInterval);
                this.state.monitoringInterval = null;
            }

            console.log('🔴 System monitoring stopped');
        },

        // 시스템 메트릭 수집
        async collectSystemMetrics() {
            try {
                // 메모리 사용량
                if ('memory' in performance) {
                    const memory = performance.memory;
                    this.state.systemMetrics.memoryUsage = Math.round(
                        (memory.usedJSHeapSize / memory.totalJSHeapSize) * 100
                    );
                }

                // CPU 사용량 (근사치)
                const start = performance.now();
                await new Promise(resolve => setTimeout(resolve, 1));
                const end = performance.now();
                const cpuDelay = end - start;
                this.state.systemMetrics.cpuUsage = Math.min(100, Math.max(0,
                    (cpuDelay - 1) / 10 * 100
                ));

                // 네트워크 트래픽 (Performance API 사용)
                const entries = performance.getEntriesByType('resource');
                const recentEntries = entries.filter(entry =>
                    Date.now() - entry.startTime < this.config.monitoringInterval * 2
                );

                this.state.systemMetrics.networkTraffic = {
                    in: recentEntries.reduce((sum, entry) => sum + (entry.transferSize || 0), 0),
                    out: recentEntries.reduce((sum, entry) => sum + (entry.encodedBodySize || 0), 0)
                };

                // 스토리지 사용량 (localStorage 기준)
                if ('localStorage' in window) {
                    let totalSize = 0;
                    for (let key in localStorage) {
                        if (localStorage.hasOwnProperty(key)) {
                            totalSize += localStorage[key].length;
                        }
                    }
                    this.state.systemMetrics.diskUsage = Math.round(
                        (totalSize / (5 * 1024 * 1024)) * 100 // 5MB 기준
                    );
                }

            } catch (error) {
                console.warn('⚠️ Failed to collect system metrics:', error);
            }
        },

        // 알림 확인
        checkAlerts() {
            const metrics = this.state.systemMetrics;
            const thresholds = this.config.alertThresholds;

            // CPU 사용량 알림
            if (metrics.cpuUsage > thresholds.cpuUsage) {
                this.createAlert('high-cpu', `High CPU usage: ${metrics.cpuUsage}%`, 'warning');
            }

            // 메모리 사용량 알림
            if (metrics.memoryUsage > thresholds.memoryUsage) {
                this.createAlert('high-memory', `High memory usage: ${metrics.memoryUsage}%`, 'warning');
            }

            // 디스크 사용량 알림
            if (metrics.diskUsage > thresholds.diskUsage) {
                this.createAlert('high-disk', `High disk usage: ${metrics.diskUsage}%`, 'error');
            }

            // 에러율 확인
            const recentErrors = this.state.errorLogs.filter(log =>
                Date.now() - new Date(log.timestamp).getTime() < 60000 // 1분 이내
            );

            if (recentErrors.length > thresholds.errorRate) {
                this.createAlert('high-error-rate',
                    `High error rate: ${recentErrors.length} errors in last minute`, 'error');
            }
        },

        // 알림 생성
        createAlert(type, message, severity = 'info') {
            const existingAlert = this.state.alerts.find(alert =>
                alert.type === type && !alert.acknowledged
            );

            if (existingAlert) return; // 중복 알림 방지

            const alert = {
                id: Date.now().toString(),
                type,
                message,
                severity,
                timestamp: new Date().toISOString(),
                acknowledged: false
            };

            this.state.alerts.push(alert);

            // 최대 알림 수 제한
            if (this.state.alerts.length > 100) {
                this.state.alerts = this.state.alerts.slice(-100);
            }

            console.log(`🚨 Alert created: ${message}`);
        },

        // 에러 로깅
        logError(errorData) {
            this.state.errorLogs.push({
                id: Date.now().toString(),
                ...errorData
            });

            // 최대 로그 수 제한
            if (this.state.errorLogs.length > this.config.maxErrorLogs) {
                this.state.errorLogs = this.state.errorLogs.slice(-this.config.maxErrorLogs);
            }

            console.log('📝 Error logged:', errorData);
        },

        // API 호출 로깅
        logAPICall(apiData) {
            this.logPerformance({
                type: 'api-call',
                ...apiData
            });
        },

        // 성능 데이터 로깅
        logPerformance(performanceData) {
            this.state.performanceData.push({
                id: Date.now().toString(),
                ...performanceData
            });

            // 최대 성능 데이터 수 제한
            if (this.state.performanceData.length > this.config.maxPerformanceData) {
                this.state.performanceData = this.state.performanceData.slice(-this.config.maxPerformanceData);
            }
        },

        // WebSocket 설정 (실시간 모니터링)
        setupWebSocket() {
            // 향후 WebSocket 서버 연결 구현
            console.log('🔌 WebSocket setup placeholder');
        },

        // 실시간 업데이트 브로드캐스트
        broadcastUpdate() {
            const updateData = {
                timestamp: new Date().toISOString(),
                metrics: this.state.systemMetrics,
                alertCount: this.state.alerts.filter(a => !a.acknowledged).length,
                errorCount: this.state.errorLogs.length,
                performanceScore: this.calculatePerformanceScore()
            };

            // 구독자들에게 업데이트 전송
            this.state.clients.forEach(callback => {
                try {
                    callback(updateData);
                } catch (error) {
                    console.warn('⚠️ Failed to send update to subscriber:', error);
                }
            });
        },

        // 성능 점수 계산
        calculatePerformanceScore() {
            const metrics = this.state.systemMetrics;
            const cpuScore = Math.max(0, 100 - metrics.cpuUsage);
            const memoryScore = Math.max(0, 100 - metrics.memoryUsage);
            const diskScore = Math.max(0, 100 - metrics.diskUsage);

            return Math.round((cpuScore + memoryScore + diskScore) / 3);
        },

        // 구독 관리
        subscribe(callback) {
            this.state.clients.add(callback);
        },

        unsubscribe(callback) {
            this.state.clients.delete(callback);
        },

        // 설정 업데이트
        updateConfig(newConfig) {
            this.config = { ...this.config, ...newConfig };

            // 모니터링 간격 변경 시 재시작
            if (newConfig.monitoringInterval && this.state.isMonitoring) {
                this.stopMonitoring();
                this.startMonitoring();
            }
        },

        // 알림 관리
        clearAlerts() {
            this.state.alerts = [];
        },

        acknowledgeAlert(alertId) {
            const alert = this.state.alerts.find(a => a.id === alertId);
            if (alert) {
                alert.acknowledged = true;
                alert.acknowledgedAt = new Date().toISOString();
            }
        },

        // 정리
        destroy() {
            this.stopMonitoring();
            this.state.clients.clear();
            console.log('🗑️ Monitoring Agent destroyed');
        },

        // 헬스체크
        healthCheck() {
            return {
                status: 'healthy',
                monitoring: this.state.isMonitoring,
                uptime: Date.now() - this.initTime,
                version: this.version,
                metrics: this.state.systemMetrics
            };
        }
    };
});

console.log('🔍 System Monitoring Agent module loaded');