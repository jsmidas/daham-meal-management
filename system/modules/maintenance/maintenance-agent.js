/**
 * 🔧 System Maintenance Agent
 * 자동 백업, 시스템 헬스체크, 자동 업데이트 관리
 */

define('maintenance-agent', ['navigation'], (deps) => {

    return {
        name: 'maintenance-agent',
        version: '1.0.0',
        protected: true,

        // 내부 상태
        state: {
            isMaintenanceMode: false,
            scheduledTasks: new Map(),
            backupHistory: [],
            healthCheckResults: [],
            maintenanceLog: [],
            autoUpdateEnabled: true,
            lastBackup: null,
            lastHealthCheck: null,
            maintenanceWindow: null
        },

        // 설정
        config: {
            backupInterval: 6 * 60 * 60 * 1000, // 6시간마다
            healthCheckInterval: 30 * 60 * 1000, // 30분마다
            maxBackupFiles: 50,
            maxLogEntries: 500,
            maintenanceWindow: {
                start: '02:00', // 새벽 2시
                end: '04:00',   // 새벽 4시
                timezone: 'Asia/Seoul'
            },
            autoCleanup: {
                enabled: true,
                oldLogsThreshold: 30 * 24 * 60 * 60 * 1000, // 30일
                tempFilesThreshold: 7 * 24 * 60 * 60 * 1000  // 7일
            }
        },

        // 초기화
        async init() {
            console.log('🔧 System Maintenance Agent initializing...');

            try {
                this.setupScheduledTasks();
                this.startPeriodicMaintenance();
                this.setupMaintenanceWindow();

                // 시작 시 헬스체크 실행
                await this.performHealthCheck();

                console.log('✅ System Maintenance Agent initialized successfully');

                // 관리 인터페이스 등록
                if (window.Fortress) {
                    window.Fortress.registerInterface('maintenance', this.getPublicInterface());
                }

                return this;
            } catch (error) {
                console.error('❌ Failed to initialize Maintenance Agent:', error);
                throw error;
            }
        },

        // 공개 인터페이스
        getPublicInterface() {
            return {
                // 메인터넌스 모드
                enableMaintenanceMode: (reason) => this.enableMaintenanceMode(reason),
                disableMaintenanceMode: () => this.disableMaintenanceMode(),
                isMaintenanceMode: () => this.state.isMaintenanceMode,

                // 백업 관리
                createBackup: (type = 'manual') => this.createBackup(type),
                restoreBackup: (backupId) => this.restoreBackup(backupId),
                getBackupHistory: () => [...this.state.backupHistory],
                deleteBackup: (backupId) => this.deleteBackup(backupId),

                // 헬스체크
                performHealthCheck: () => this.performHealthCheck(),
                getHealthStatus: () => this.getHealthStatus(),
                getHealthHistory: () => [...this.state.healthCheckResults],

                // 업데이트 관리
                checkForUpdates: () => this.checkForUpdates(),
                performUpdate: (updateInfo) => this.performUpdate(updateInfo),
                enableAutoUpdate: () => this.enableAutoUpdate(),
                disableAutoUpdate: () => this.disableAutoUpdate(),

                // 시스템 정리
                performCleanup: () => this.performCleanup(),
                clearCache: () => this.clearCache(),
                optimizeDatabase: () => this.optimizeDatabase(),

                // 예약 작업
                scheduleTask: (name, schedule, task) => this.scheduleTask(name, schedule, task),
                cancelTask: (name) => this.cancelTask(name),
                getScheduledTasks: () => this.getScheduledTasksInfo(),

                // 로그 관리
                getMaintenanceLog: (limit = 100) => this.state.maintenanceLog.slice(-limit),
                clearLog: () => this.clearMaintenanceLog(),

                // 설정
                updateConfig: (newConfig) => this.updateConfig(newConfig),
                getConfig: () => ({ ...this.config })
            };
        },

        // 예약 작업 설정
        setupScheduledTasks() {
            // 자동 백업
            this.scheduleTask('auto-backup', {
                interval: this.config.backupInterval,
                immediate: false
            }, () => this.createBackup('scheduled'));

            // 정기 헬스체크
            this.scheduleTask('health-check', {
                interval: this.config.healthCheckInterval,
                immediate: true
            }, () => this.performHealthCheck());

            // 일일 정리 작업
            this.scheduleTask('daily-cleanup', {
                cron: '0 3 * * *', // 매일 새벽 3시
                timezone: 'Asia/Seoul'
            }, () => this.performDailyCleanup());

            // 주간 최적화
            this.scheduleTask('weekly-optimization', {
                cron: '0 4 * * 0', // 매주 일요일 새벽 4시
                timezone: 'Asia/Seoul'
            }, () => this.performWeeklyOptimization());

            console.log('📅 Scheduled tasks configured');
        },

        // 정기 유지보수 시작
        startPeriodicMaintenance() {
            // 예약된 작업들을 실제 스케줄러에 등록
            for (const [name, task] of this.state.scheduledTasks) {
                this.activateScheduledTask(name, task);
            }
        },

        // 유지보수 창 설정
        setupMaintenanceWindow() {
            const checkMaintenanceWindow = () => {
                const now = new Date();
                const currentTime = now.toTimeString().slice(0, 5);
                const { start, end } = this.config.maintenanceWindow;

                const isInWindow = (currentTime >= start && currentTime <= end);

                if (isInWindow && !this.state.maintenanceWindow) {
                    this.state.maintenanceWindow = {
                        start: now,
                        scheduled: true
                    };
                    this.log('🕐 Entered maintenance window');
                } else if (!isInWindow && this.state.maintenanceWindow) {
                    this.state.maintenanceWindow = null;
                    this.log('🕐 Exited maintenance window');
                }
            };

            // 1분마다 유지보수 창 확인
            setInterval(checkMaintenanceWindow, 60000);
            checkMaintenanceWindow(); // 즉시 한 번 실행
        },

        // 메인터넌스 모드 활성화
        async enableMaintenanceMode(reason = 'Manual maintenance') {
            if (this.state.isMaintenanceMode) return;

            this.state.isMaintenanceMode = true;
            this.log(`🚧 Maintenance mode enabled: ${reason}`);

            // 시스템 알림 (다른 모듈들에게)
            if (window.Fortress) {
                window.Fortress.broadcastEvent('maintenance-mode-enabled', {
                    reason,
                    timestamp: new Date().toISOString()
                });
            }

            // 진행 중인 작업들을 안전하게 정리
            await this.gracefulShutdown();
        },

        // 메인터넌스 모드 비활성화
        async disableMaintenanceMode() {
            if (!this.state.isMaintenanceMode) return;

            this.state.isMaintenanceMode = false;
            this.log('✅ Maintenance mode disabled');

            // 시스템 알림
            if (window.Fortress) {
                window.Fortress.broadcastEvent('maintenance-mode-disabled', {
                    timestamp: new Date().toISOString()
                });
            }

            // 서비스 재시작
            await this.restartServices();
        },

        // 백업 생성
        async createBackup(type = 'manual') {
            try {
                this.log(`💾 Creating ${type} backup...`);

                const backupId = `backup_${Date.now()}`;
                const timestamp = new Date().toISOString();

                // 데이터베이스 백업
                const dbBackup = await this.backupDatabase();

                // 설정 파일 백업
                const configBackup = await this.backupConfiguration();

                // 로그 파일 백업
                const logBackup = await this.backupLogs();

                // 사용자 데이터 백업
                const userDataBackup = await this.backupUserData();

                const backup = {
                    id: backupId,
                    type,
                    timestamp,
                    size: this.calculateBackupSize(dbBackup, configBackup, logBackup, userDataBackup),
                    components: {
                        database: dbBackup,
                        configuration: configBackup,
                        logs: logBackup,
                        userData: userDataBackup
                    },
                    integrity: await this.calculateBackupHash(backupId)
                };

                this.state.backupHistory.push(backup);
                this.state.lastBackup = timestamp;

                // 오래된 백업 정리
                await this.cleanupOldBackups();

                this.log(`✅ Backup created successfully: ${backupId}`);
                return backup;

            } catch (error) {
                this.log(`❌ Backup failed: ${error.message}`, 'error');
                throw error;
            }
        },

        // 데이터베이스 백업
        async backupDatabase() {
            try {
                // SQLite 데이터베이스 백업 로직
                const dbPath = 'backups/daham_meal.db';
                const backupPath = `backups/db_backup_${Date.now()}.db`;

                // 실제 구현에서는 파일 복사 API 사용
                return {
                    source: dbPath,
                    destination: backupPath,
                    size: 0, // 실제 파일 크기
                    timestamp: new Date().toISOString()
                };
            } catch (error) {
                throw new Error(`Database backup failed: ${error.message}`);
            }
        },

        // 설정 백업
        async backupConfiguration() {
            try {
                const configData = {
                    config: this.config,
                    moduleConfigs: window.Fortress?.getAllModuleConfigs() || {},
                    systemSettings: this.getSystemSettings()
                };

                return {
                    data: configData,
                    size: JSON.stringify(configData).length,
                    timestamp: new Date().toISOString()
                };
            } catch (error) {
                throw new Error(`Configuration backup failed: ${error.message}`);
            }
        },

        // 로그 백업
        async backupLogs() {
            try {
                const logs = {
                    maintenance: this.state.maintenanceLog,
                    system: window.require?.('monitoring-agent')?.getErrorLogs?.() || [],
                    performance: window.require?.('monitoring-agent')?.getPerformanceData?.() || []
                };

                return {
                    data: logs,
                    size: JSON.stringify(logs).length,
                    timestamp: new Date().toISOString()
                };
            } catch (error) {
                throw new Error(`Log backup failed: ${error.message}`);
            }
        },

        // 사용자 데이터 백업
        async backupUserData() {
            try {
                const userData = {
                    localStorage: { ...localStorage },
                    sessionStorage: { ...sessionStorage }
                };

                return {
                    data: userData,
                    size: JSON.stringify(userData).length,
                    timestamp: new Date().toISOString()
                };
            } catch (error) {
                throw new Error(`User data backup failed: ${error.message}`);
            }
        },

        // 헬스체크 수행
        async performHealthCheck() {
            try {
                this.log('🏥 Performing health check...');

                const healthCheck = {
                    id: `health_${Date.now()}`,
                    timestamp: new Date().toISOString(),
                    status: 'healthy',
                    checks: {}
                };

                // 시스템 리소스 체크
                healthCheck.checks.system = await this.checkSystemResources();

                // 데이터베이스 체크
                healthCheck.checks.database = await this.checkDatabase();

                // API 서비스 체크
                healthCheck.checks.api = await this.checkAPIServices();

                // 모듈 상태 체크
                healthCheck.checks.modules = await this.checkModules();

                // 네트워크 연결 체크
                healthCheck.checks.network = await this.checkNetworkConnectivity();

                // 전체 상태 결정
                const allChecks = Object.values(healthCheck.checks);
                const hasErrors = allChecks.some(check => check.status === 'error');
                const hasWarnings = allChecks.some(check => check.status === 'warning');

                if (hasErrors) {
                    healthCheck.status = 'unhealthy';
                } else if (hasWarnings) {
                    healthCheck.status = 'degraded';
                }

                this.state.healthCheckResults.push(healthCheck);
                this.state.lastHealthCheck = healthCheck.timestamp;

                // 최대 결과 수 제한
                if (this.state.healthCheckResults.length > 100) {
                    this.state.healthCheckResults = this.state.healthCheckResults.slice(-100);
                }

                this.log(`✅ Health check completed: ${healthCheck.status}`);
                return healthCheck;

            } catch (error) {
                this.log(`❌ Health check failed: ${error.message}`, 'error');
                throw error;
            }
        },

        // 시스템 리소스 체크
        async checkSystemResources() {
            try {
                const monitoring = window.require?.('monitoring-agent');
                if (!monitoring) {
                    return { status: 'warning', message: 'Monitoring agent not available' };
                }

                const metrics = monitoring.getSystemMetrics();
                const issues = [];

                if (metrics.cpuUsage > 90) issues.push('High CPU usage');
                if (metrics.memoryUsage > 95) issues.push('High memory usage');
                if (metrics.diskUsage > 95) issues.push('High disk usage');

                return {
                    status: issues.length > 0 ? 'warning' : 'healthy',
                    metrics,
                    issues
                };
            } catch (error) {
                return { status: 'error', message: error.message };
            }
        },

        // 데이터베이스 체크
        async checkDatabase() {
            try {
                // 간단한 연결 테스트
                const response = await fetch('http://127.0.0.1:8010/api/admin/dashboard-stats');

                if (response.ok) {
                    return { status: 'healthy', message: 'Database connection OK' };
                } else {
                    return { status: 'error', message: 'Database connection failed' };
                }
            } catch (error) {
                return { status: 'error', message: `Database check failed: ${error.message}` };
            }
        },

        // API 서비스 체크
        async checkAPIServices() {
            const services = [
                { name: 'Dashboard API', url: 'http://127.0.0.1:8010/api/admin/dashboard-stats' },
                { name: 'Users API', url: 'http://127.0.0.1:8010/api/admin/users' },
                { name: 'Ingredients API', url: 'http://127.0.0.1:8010/api/admin/ingredients-new' }
            ];

            const results = [];
            let healthyCount = 0;

            for (const service of services) {
                try {
                    const response = await fetch(service.url);
                    const status = response.ok ? 'healthy' : 'warning';
                    if (response.ok) healthyCount++;

                    results.push({
                        name: service.name,
                        status,
                        responseTime: Date.now()
                    });
                } catch (error) {
                    results.push({
                        name: service.name,
                        status: 'error',
                        error: error.message
                    });
                }
            }

            const overallStatus = healthyCount === services.length ? 'healthy' :
                                healthyCount > 0 ? 'warning' : 'error';

            return {
                status: overallStatus,
                services: results,
                healthyCount,
                totalCount: services.length
            };
        },

        // 모듈 상태 체크
        async checkModules() {
            try {
                if (!window.Fortress) {
                    return { status: 'warning', message: 'Fortress framework not available' };
                }

                const moduleStatus = window.Fortress.getModuleStatus?.() || {};
                const issues = [];

                for (const [name, status] of Object.entries(moduleStatus)) {
                    if (status.hasError) {
                        issues.push(`Module ${name} has errors`);
                    }
                }

                return {
                    status: issues.length > 0 ? 'warning' : 'healthy',
                    modules: moduleStatus,
                    issues
                };
            } catch (error) {
                return { status: 'error', message: error.message };
            }
        },

        // 네트워크 연결 체크
        async checkNetworkConnectivity() {
            try {
                const online = navigator.onLine;
                if (!online) {
                    return { status: 'warning', message: 'Network offline' };
                }

                // 간단한 연결 테스트
                const start = Date.now();
                await fetch('http://127.0.0.1:8010/health', { method: 'HEAD' });
                const latency = Date.now() - start;

                return {
                    status: latency < 1000 ? 'healthy' : 'warning',
                    online,
                    latency
                };
            } catch (error) {
                return { status: 'error', message: error.message };
            }
        },

        // 예약 작업 관리
        scheduleTask(name, schedule, task) {
            if (this.state.scheduledTasks.has(name)) {
                this.cancelTask(name);
            }

            const taskInfo = {
                name,
                schedule,
                task,
                lastRun: null,
                nextRun: this.calculateNextRun(schedule),
                active: false,
                timerId: null
            };

            this.state.scheduledTasks.set(name, taskInfo);
            this.activateScheduledTask(name, taskInfo);

            this.log(`📅 Task scheduled: ${name}`);
        },

        // 예약 작업 활성화
        activateScheduledTask(name, taskInfo) {
            if (taskInfo.active) return;

            if (taskInfo.schedule.interval) {
                // 인터벌 기반 스케줄
                taskInfo.timerId = setInterval(async () => {
                    await this.executeScheduledTask(name, taskInfo);
                }, taskInfo.schedule.interval);

                if (taskInfo.schedule.immediate) {
                    this.executeScheduledTask(name, taskInfo);
                }
            } else if (taskInfo.schedule.cron) {
                // Cron 기반 스케줄 (간단한 구현)
                this.setupCronTask(name, taskInfo);
            }

            taskInfo.active = true;
        },

        // 예약 작업 실행
        async executeScheduledTask(name, taskInfo) {
            try {
                this.log(`⚡ Executing scheduled task: ${name}`);

                taskInfo.lastRun = new Date().toISOString();
                await taskInfo.task();

                this.log(`✅ Scheduled task completed: ${name}`);
            } catch (error) {
                this.log(`❌ Scheduled task failed: ${name} - ${error.message}`, 'error');
            }
        },

        // 일일 정리 작업
        async performDailyCleanup() {
            this.log('🧹 Performing daily cleanup...');

            if (this.config.autoCleanup.enabled) {
                await this.cleanupOldLogs();
                await this.cleanupTempFiles();
                await this.clearCache();
            }

            this.log('✅ Daily cleanup completed');
        },

        // 주간 최적화
        async performWeeklyOptimization() {
            this.log('⚡ Performing weekly optimization...');

            await this.optimizeDatabase();
            await this.defragmentStorage();
            await this.updateSystemStats();

            this.log('✅ Weekly optimization completed');
        },

        // 로깅
        log(message, level = 'info') {
            const logEntry = {
                timestamp: new Date().toISOString(),
                level,
                message,
                agent: 'maintenance'
            };

            this.state.maintenanceLog.push(logEntry);

            // 최대 로그 수 제한
            if (this.state.maintenanceLog.length > this.config.maxLogEntries) {
                this.state.maintenanceLog = this.state.maintenanceLog.slice(-this.config.maxLogEntries);
            }

            console.log(`[Maintenance] ${message}`);
        },

        // 정리
        destroy() {
            // 모든 예약 작업 취소
            for (const [name] of this.state.scheduledTasks) {
                this.cancelTask(name);
            }

            this.log('🗑️ Maintenance Agent destroyed');
        },

        // 헬스체크 결과 반환
        getHealthStatus() {
            const latest = this.state.healthCheckResults.slice(-1)[0];
            return latest || { status: 'unknown', message: 'No health check performed yet' };
        },

        // 설정 업데이트
        updateConfig(newConfig) {
            this.config = { ...this.config, ...newConfig };
            this.log('⚙️ Configuration updated');
        }
    };
});

console.log('🔧 System Maintenance Agent module loaded');