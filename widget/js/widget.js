(function() {
    class PODCWidget {
        constructor(config = {}) {
            // Reuse existing chatbot logic
            this.config = {
                backendUrl: 'https://podc-chatbot-backend-v2.onrender.com',
                position: 'bottom-right',
                ...config
            };
            this.initialize();
        }

        initialize() {
            // Reuse your existing initialization logic from script.js
            this.createWidget();
            this.setupEventListeners();
        }
    }
    window.PODCWidget = PODCWidget;
})();