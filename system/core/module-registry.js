/**
 * AI-Resistant Module Registry
 * 모듈 등록 및 의존성 관리를 담당하는 핵심 시스템
 */

class ModuleRegistry {
    constructor() {
        this.modules = new Map();
        this.dependencies = new Map();
        this.loadOrder = [];
        this.initialized = false;
    }

    /**
     * 모듈 정의 등록
     */
    define(name, dependencies, factory) {
        if (this.modules.has(name)) {
            console.warn(`⚠️ Module '${name}' already defined. Ignoring redefinition.`);
            return;
        }

        const moduleDefinition = {
            name,
            dependencies: Array.isArray(dependencies) ? dependencies : [],
            factory: typeof factory === 'function' ? factory : dependencies,
            loaded: false,
            instance: null,
            error: null
        };

        this.modules.set(name, moduleDefinition);
        this.dependencies.set(name, moduleDefinition.dependencies);
        
        console.log(`📦 Module '${name}' defined with dependencies:`, moduleDefinition.dependencies);
    }

    /**
     * 의존성 해결 및 로딩 순서 결정
     */
    resolveDependencies() {
        const resolved = new Set();
        const resolving = new Set();
        const loadOrder = [];

        const resolve = (name) => {
            if (resolved.has(name)) return;
            if (resolving.has(name)) {
                throw new Error(`🔄 Circular dependency detected: ${name}`);
            }

            if (!this.modules.has(name)) {
                throw new Error(`❌ Module not found: ${name}`);
            }

            resolving.add(name);
            const deps = this.dependencies.get(name) || [];
            
            for (const dep of deps) {
                resolve(dep);
            }

            resolving.delete(name);
            resolved.add(name);
            loadOrder.push(name);
        };

        // 모든 모듈에 대해 의존성 해결
        for (const name of this.modules.keys()) {
            if (!resolved.has(name)) {
                resolve(name);
            }
        }

        this.loadOrder = loadOrder;
        console.log('🎯 Dependency resolution complete. Load order:', loadOrder);
        return loadOrder;
    }

    /**
     * 단일 모듈 로드
     */
    async loadModule(name) {
        const moduleDefinition = this.modules.get(name);
        if (!moduleDefinition) {
            throw new Error(`❌ Module '${name}' not found`);
        }

        if (moduleDefinition.loaded) {
            return moduleDefinition.instance;
        }

        try {
            console.log(`⏳ Loading module: ${name}`);
            
            // 의존성 먼저 로드
            const depInstances = {};
            for (const dep of moduleDefinition.dependencies) {
                depInstances[dep] = await this.loadModule(dep);
            }

            // 모듈 팩토리 실행
            const instance = await moduleDefinition.factory(depInstances);
            
            // Fortress 프레임워크에 등록
            if (window.Fortress) {
                window.Fortress.registerModule(name, instance);
            }

            moduleDefinition.instance = instance;
            moduleDefinition.loaded = true;
            moduleDefinition.error = null;

            console.log(`✅ Module '${name}' loaded successfully`);
            return instance;

        } catch (error) {
            moduleDefinition.error = error;
            console.error(`❌ Failed to load module '${name}':`, error);
            throw error;
        }
    }

    /**
     * 모든 모듈 로드
     */
    async loadAllModules() {
        if (this.initialized) {
            console.log('📚 Modules already initialized');
            return;
        }

        try {
            const loadOrder = this.resolveDependencies();
            
            for (const name of loadOrder) {
                await this.loadModule(name);
            }

            this.initialized = true;
            console.log('🎉 All modules loaded successfully');
            
            // 모듈 초기화
            if (window.Fortress) {
                await window.Fortress.initializeModules();
            }

        } catch (error) {
            console.error('💥 Module loading failed:', error);
            throw error;
        }
    }

    /**
     * 모듈 상태 조회
     */
    getModuleStatus() {
        const status = {};
        for (const [name, def] of this.modules.entries()) {
            status[name] = {
                loaded: def.loaded,
                hasError: !!def.error,
                error: def.error?.message,
                dependencies: def.dependencies
            };
        }
        return status;
    }

    /**
     * 모듈 언로드 (개발용)
     */
    unloadModule(name) {
        const moduleDefinition = this.modules.get(name);
        if (!moduleDefinition) return;

        if (moduleDefinition.instance?.destroy) {
            moduleDefinition.instance.destroy();
        }

        moduleDefinition.loaded = false;
        moduleDefinition.instance = null;
        moduleDefinition.error = null;

        console.log(`🗑️ Module '${name}' unloaded`);
    }

    /**
     * 핫 리로드 (개발용)
     */
    async reloadModule(name) {
        this.unloadModule(name);
        return await this.loadModule(name);
    }
}

// 전역 레지스트리 인스턴스
window.ModuleRegistry = window.ModuleRegistry || new ModuleRegistry();

// API 노출
window.define = (name, deps, factory) => window.ModuleRegistry.define(name, deps, factory);
window.require = (name) => {
    const module = window.ModuleRegistry.modules.get(name);
    return module?.instance || null;
};

console.log('📋 Module Registry initialized');