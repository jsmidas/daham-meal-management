// Event Handlers Module
class EventHandlersModule {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventDelegation();
        console.log('Event Handlers module initialized');
    }

    setupEventDelegation() {
        // 전체 document에 이벤트 위임 설정
        document.addEventListener('click', (e) => {
            this.handleClick(e);
        });
    }

    handleClick(e) {
        const target = e.target;
        
        // onclick 속성에서 함수명 추출
        const onclickAttr = target.getAttribute('onclick');
        if (onclickAttr) {
            e.preventDefault();
            this.executeFunction(onclickAttr, target, e);
        }

        // data-action 속성으로 처리
        const action = target.getAttribute('data-action');
        if (action) {
            e.preventDefault();
            this.executeAction(action, target, e);
        }
    }

    executeFunction(functionCall, element, event) {
        // onclick="functionName()" 형태에서 함수명과 매개변수 추출
        const match = functionCall.match(/(\w+)\((.*?)\)/);
        if (match) {
            const [, functionName, argsString] = match;
            const args = this.parseArguments(argsString);
            
            if (this[functionName]) {
                this[functionName].apply(this, [element, event, ...args]);
            } else if (window[functionName]) {
                window[functionName].apply(window, args);
            } else {
                console.warn(`Function ${functionName} not found`);
            }
        }
    }

    executeAction(action, element, event) {
        const [actionName, ...params] = action.split(':');
        
        switch(actionName) {
            case 'logout':
                this.logout();
                break;
            case 'showModal':
                this.showModal(params[0]);
                break;
            case 'closeModal':
                this.closeModal(params[0]);
                break;
            case 'save':
                this.save(params[0]);
                break;
            case 'delete':
                this.delete(params[0]);
                break;
            case 'openWindow':
                window.open(params[0], params[1] || '_blank');
                break;
            default:
                console.warn(`Action ${actionName} not found`);
        }
    }

    parseArguments(argsString) {
        if (!argsString.trim()) return [];
        
        // 간단한 인자 파싱 (문자열, 숫자 지원)
        return argsString.split(',').map(arg => {
            arg = arg.trim();
            if (arg.startsWith("'") && arg.endsWith("'")) {
                return arg.slice(1, -1);
            } else if (arg.startsWith('"') && arg.endsWith('"')) {
                return arg.slice(1, -1);
            } else if (!isNaN(arg)) {
                return Number(arg);
            }
            return arg;
        });
    }

    // 공통 핸들러 메서드들
    logout() {
        if (window.logout) {
            window.logout();
        }
    }

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
            modal.classList.remove('hidden');
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            modal.classList.add('hidden');
        }
    }

    save(type) {
        switch(type) {
            case 'user':
                if (window.saveUser) window.saveUser();
                break;
            case 'supplier':
                if (window.saveSupplier) window.saveSupplier();
                break;
            case 'site':
                if (window.saveSite) window.saveSite();
                break;
            case 'mapping':
                if (window.saveMapping) window.saveMapping();
                break;
        }
    }

    delete(type) {
        switch(type) {
            case 'user':
                if (window.deleteUser) window.deleteUser();
                break;
            case 'supplier':
                if (window.deleteSupplier) window.deleteSupplier();
                break;
        }
    }
}

// Export for use
window.EventHandlersModule = EventHandlersModule;