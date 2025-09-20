/**
 * 🚀 System Agents Initialization
 * 시스템 레벨 에이전트들을 ModuleRegistry에 등록하고 초기화
 */

(function() {
    'use strict';

    console.log('🚀 Initializing System Agents...');

    // ModuleRegistry가 로드될 때까지 대기
    function waitForRegistry() {
        return new Promise((resolve) => {
            if (window.ModuleRegistry) {
                resolve();
                return;
            }

            const checkInterval = setInterval(() => {
                if (window.ModuleRegistry) {
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 100);
        });
    }

    // 시스템 에이전트 등록
    async function registerSystemAgents() {
        await waitForRegistry();

        console.log('📋 Registering system agents to ModuleRegistry...');

        // 1. 모니터링 에이전트 등록
        window.ModuleRegistry.define('monitoring-agent', ['navigation'], async (deps) => {
            console.log('🔍 Loading Monitoring Agent...');

            // 스크립트 동적 로드
            await loadScript('system/modules/monitoring/monitoring-agent.js');

            // 모듈이 정의될 때까지 대기
            while (!window.require || !window.require('monitoring-agent')) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            return window.require('monitoring-agent');
        });

        // 2. 유지보수 에이전트 등록
        window.ModuleRegistry.define('maintenance-agent', ['navigation'], async (deps) => {
            console.log('🔧 Loading Maintenance Agent...');

            await loadScript('system/modules/maintenance/maintenance-agent.js');

            while (!window.require || !window.require('maintenance-agent')) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            return window.require('maintenance-agent');
        });

        // 3. API 게이트웨이 에이전트 등록
        window.ModuleRegistry.define('api-gateway-agent', ['navigation'], async (deps) => {
            console.log('🌐 Loading API Gateway Agent...');

            await loadScript('system/modules/api-gateway/api-gateway-agent.js');

            while (!window.require || !window.require('api-gateway-agent')) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            return window.require('api-gateway-agent');
        });

        console.log('✅ All system agents registered to ModuleRegistry');
    }

    // 스크립트 동적 로드 유틸리티
    function loadScript(src) {
        return new Promise((resolve, reject) => {
            // 이미 로드된 스크립트인지 확인
            const existingScript = document.querySelector(`script[src="${src}"]`);
            if (existingScript) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = src;
            script.onload = () => {
                console.log(`✅ Script loaded: ${src}`);
                resolve();
            };
            script.onerror = () => {
                console.error(`❌ Failed to load script: ${src}`);
                reject(new Error(`Failed to load script: ${src}`));
            };

            document.head.appendChild(script);
        });
    }

    // 시스템 에이전트 관리자 클래스
    class SystemAgentManager {
        constructor() {
            this.agents = new Map();
            this.initialized = false;
        }

        // 모든 시스템 에이전트 초기화
        async initializeAll() {
            if (this.initialized) {
                console.log('⚠️ System agents already initialized');
                return;
            }

            try {
                console.log('🚀 Starting system agents initialization...');

                // 1. 모니터링 에이전트 초기화
                const monitoringAgent = await window.ModuleRegistry.loadModule('monitoring-agent');
                if (monitoringAgent && typeof monitoringAgent.init === 'function') {
                    await monitoringAgent.init();
                    this.agents.set('monitoring', monitoringAgent);
                    console.log('✅ Monitoring Agent initialized');
                }

                // 2. 유지보수 에이전트 초기화
                const maintenanceAgent = await window.ModuleRegistry.loadModule('maintenance-agent');
                if (maintenanceAgent && typeof maintenanceAgent.init === 'function') {
                    await maintenanceAgent.init();
                    this.agents.set('maintenance', maintenanceAgent);
                    console.log('✅ Maintenance Agent initialized');
                }

                // 3. API 게이트웨이 에이전트 초기화
                const gatewayAgent = await window.ModuleRegistry.loadModule('api-gateway-agent');
                if (gatewayAgent && typeof gatewayAgent.init === 'function') {
                    await gatewayAgent.init();
                    this.agents.set('api-gateway', gatewayAgent);
                    console.log('✅ API Gateway Agent initialized');
                }

                this.initialized = true;
                console.log('🎉 All system agents initialized successfully!');

                // 전역 접근을 위한 인터페이스 설정
                this.setupGlobalInterface();

            } catch (error) {
                console.error('💥 System agents initialization failed:', error);
                throw error;
            }
        }

        // 전역 인터페이스 설정
        setupGlobalInterface() {
            window.SystemAgents = {
                // 개별 에이전트 접근
                monitoring: this.agents.get('monitoring'),
                maintenance: this.agents.get('maintenance'),
                apiGateway: this.agents.get('api-gateway'),

                // 통합 관리 기능
                getStatus: () => this.getSystemStatus(),
                getHealth: () => this.getSystemHealth(),
                restart: () => this.restartAllAgents(),
                stop: () => this.stopAllAgents(),

                // 개발자 도구
                debug: {
                    listAgents: () => Array.from(this.agents.keys()),
                    getAgent: (name) => this.agents.get(name),
                    reinitialize: () => this.reinitialize()
                }
            };

            console.log('🔧 Global SystemAgents interface ready');
        }

        // 시스템 상태 조회
        getSystemStatus() {
            const status = {
                initialized: this.initialized,
                agentCount: this.agents.size,
                agents: {}
            };

            for (const [name, agent] of this.agents) {
                status.agents[name] = {
                    active: !!agent,
                    health: agent.healthCheck ? agent.healthCheck() : 'unknown'
                };
            }

            return status;
        }

        // 시스템 헬스 상태
        getSystemHealth() {
            const health = {
                overall: 'healthy',
                agents: {},
                timestamp: new Date().toISOString()
            };

            let hasWarnings = false;
            let hasErrors = false;

            for (const [name, agent] of this.agents) {
                try {
                    const agentHealth = agent.healthCheck ? agent.healthCheck() : { status: 'unknown' };
                    health.agents[name] = agentHealth;

                    if (agentHealth.status === 'warning' || agentHealth.status === 'degraded') {
                        hasWarnings = true;
                    } else if (agentHealth.status === 'error' || agentHealth.status === 'unhealthy') {
                        hasErrors = true;
                    }
                } catch (error) {
                    health.agents[name] = { status: 'error', error: error.message };
                    hasErrors = true;
                }
            }

            if (hasErrors) {
                health.overall = 'unhealthy';
            } else if (hasWarnings) {
                health.overall = 'degraded';
            }

            return health;
        }

        // 모든 에이전트 재시작
        async restartAllAgents() {
            console.log('🔄 Restarting all system agents...');

            for (const [name, agent] of this.agents) {
                try {
                    if (agent.destroy && typeof agent.destroy === 'function') {
                        agent.destroy();
                    }
                } catch (error) {
                    console.warn(`⚠️ Error destroying agent ${name}:`, error);
                }
            }

            this.agents.clear();
            this.initialized = false;

            await this.initializeAll();
            console.log('✅ All system agents restarted');
        }

        // 모든 에이전트 정지
        stopAllAgents() {
            console.log('🛑 Stopping all system agents...');

            for (const [name, agent] of this.agents) {
                try {
                    if (agent.destroy && typeof agent.destroy === 'function') {
                        agent.destroy();
                    }
                } catch (error) {
                    console.warn(`⚠️ Error stopping agent ${name}:`, error);
                }
            }

            this.agents.clear();
            this.initialized = false;
            console.log('✅ All system agents stopped');
        }

        // 재초기화
        async reinitialize() {
            await this.restartAllAgents();
        }
    }

    // 전역 시스템 에이전트 매니저 인스턴스
    window.SystemAgentManager = new SystemAgentManager();

    // 자동 초기화 (DOM 로드 후)
    async function autoInitialize() {
        try {
            // 기본 의존성 확인
            await waitForRegistry();

            // 네비게이션 모듈이 있는지 확인 (의존성)
            if (!window.require || !window.require('navigation')) {
                console.log('⏳ Waiting for navigation module...');
                // 간단한 네비게이션 모듈 스텁 생성
                window.define && window.define('navigation', [], () => ({
                    name: 'navigation-stub',
                    version: '1.0.0'
                }));
            }

            // 에이전트 등록
            await registerSystemAgents();

            // 자동 초기화 (선택적)
            const autoInit = localStorage.getItem('system-agents-auto-init');
            if (autoInit !== 'false') {
                setTimeout(async () => {
                    try {
                        await window.SystemAgentManager.initializeAll();
                    } catch (error) {
                        console.warn('⚠️ Auto-initialization failed:', error);
                        console.log('💡 Try manually: SystemAgentManager.initializeAll()');
                    }
                }, 2000); // 2초 후 자동 초기화
            }

        } catch (error) {
            console.error('💥 System agents registration failed:', error);
        }
    }

    // DOM 로드 완료 후 실행
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoInitialize);
    } else {
        autoInitialize();
    }

    console.log('🔧 System Agents initialization script loaded');

})();