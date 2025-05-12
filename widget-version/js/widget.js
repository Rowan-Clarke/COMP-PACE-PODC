(function() {
    class PODCWidget {
        constructor(config = {}) {
            this.config = {
                backendUrl: 'https://podc-chatbot-backend-v2.onrender.com',
                position: 'bottom-right',
                ...config
            };
            this.initialize();
        }

        initialize() {
            this.injectStyles();
            this.createWidget();
            this.setupEventListeners();
        }

        injectStyles() {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'https://your-cdn/widget.css';
            document.head.appendChild(link);
        }

        createWidget() {
            const template = `
                <div class="podc-widget-container">
                    <div class="podc-widget-header">
                        <span>Ask PODC</span>
                        <span class="podc-widget-arrow">▲</span>
                    </div>
                    <div class="podc-widget-body">
                        <div class="podc-widget-messages"></div>
                        <div class="podc-widget-input">
                            <input type="text" placeholder="Ask a question...">
                            <button>Send</button>
                        </div>
                    </div>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', template);
            this.widget = document.querySelector('.podc-widget-container');
        }

        setupEventListeners() {
            // Add your existing event listeners here
        }
    }

    window.PODCWidget = PODCWidget;
})();