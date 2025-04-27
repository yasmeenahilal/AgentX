/**
 * AgentX Chat Widget
 * This script provides a chat interface for interacting with AgentX.
 */

(function() {
    // Get configuration from window.AgentXConfig (set by embed.js)
    const config = {
        apiBaseUrl: window.AgentXConfig?.baseUrl || 'http://127.0.0.1:8000',
        agentName: window.AgentXConfig?.agentName || '',
        deploymentId: window.AgentXConfig?.deploymentId || '',
        theme: window.AgentXConfig?.theme || 'light',
        position: window.AgentXConfig?.position || 'bottom-right'
    };
    
    // Widget initialization
    const initChatWidget = () => {
        // Create widget container
        const widgetContainer = document.createElement('div');
        widgetContainer.id = 'agentx-widget-container';
        widgetContainer.style.position = 'fixed';
        
        // Set position based on config
        if (config.position.includes('bottom')) {
            widgetContainer.style.bottom = '20px';
        } else {
            widgetContainer.style.top = '20px';
        }
        
        if (config.position.includes('right')) {
            widgetContainer.style.right = '20px';
        } else {
            widgetContainer.style.left = '20px';
        }
        
        widgetContainer.style.zIndex = '9999';
        
        // Create chat button
        const chatButton = document.createElement('div');
        chatButton.id = 'agentx-chat-button';
        chatButton.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
        `;
        chatButton.style.width = '50px';
        chatButton.style.height = '50px';
        chatButton.style.borderRadius = '50%';
        chatButton.style.backgroundColor = '#4F46E5';
        chatButton.style.color = 'white';
        chatButton.style.display = 'flex';
        chatButton.style.justifyContent = 'center';
        chatButton.style.alignItems = 'center';
        chatButton.style.cursor = 'pointer';
        chatButton.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
        
        // Create chat window
        const chatWindow = document.createElement('div');
        chatWindow.id = 'agentx-chat-window';
        chatWindow.style.display = 'none';
        chatWindow.style.flexDirection = 'column';
        chatWindow.style.width = '350px';
        chatWindow.style.height = '500px';
        chatWindow.style.backgroundColor = 'white';
        chatWindow.style.borderRadius = '10px';
        chatWindow.style.overflow = 'hidden';
        chatWindow.style.boxShadow = '0 5px 15px rgba(0, 0, 0, 0.2)';
        chatWindow.style.marginBottom = '10px';
        
        // Create chat header
        const chatHeader = document.createElement('div');
        chatHeader.style.padding = '15px';
        chatHeader.style.backgroundColor = '#4F46E5';
        chatHeader.style.color = 'white';
        chatHeader.style.fontWeight = 'bold';
        chatHeader.style.display = 'flex';
        chatHeader.style.justifyContent = 'space-between';
        chatHeader.style.alignItems = 'center';
        chatHeader.innerHTML = `
            <div>Chat with ${config.agentName || 'AgentX'}</div>
            <div id="agentx-close-chat" style="cursor: pointer;">×</div>
        `;
        
        // Create messages container
        const messagesContainer = document.createElement('div');
        messagesContainer.id = 'agentx-messages';
        messagesContainer.style.flex = '1';
        messagesContainer.style.padding = '15px';
        messagesContainer.style.overflow = 'auto';
        messagesContainer.style.backgroundColor = '#f7f7f7';
        
        // Add welcome message
        const welcomeMessage = document.createElement('div');
        welcomeMessage.className = 'agentx-message bot-message';
        welcomeMessage.style.backgroundColor = '#e6e6fa';
        welcomeMessage.style.color = '#333';
        welcomeMessage.style.padding = '10px 15px';
        welcomeMessage.style.borderRadius = '10px';
        welcomeMessage.style.marginBottom = '10px';
        welcomeMessage.style.maxWidth = '80%';
        welcomeMessage.textContent = 'Hello! How can I help you today?';
        
        messagesContainer.appendChild(welcomeMessage);
        
        // Create input area
        const inputArea = document.createElement('div');
        inputArea.style.padding = '15px';
        inputArea.style.borderTop = '1px solid #eee';
        inputArea.style.display = 'flex';
        
        const textInput = document.createElement('input');
        textInput.id = 'agentx-input';
        textInput.type = 'text';
        textInput.placeholder = 'Type your message...';
        textInput.style.flex = '1';
        textInput.style.padding = '10px';
        textInput.style.border = '1px solid #ddd';
        textInput.style.borderRadius = '20px';
        textInput.style.marginRight = '10px';
        textInput.style.outline = 'none';
        
        const sendButton = document.createElement('button');
        sendButton.id = 'agentx-send';
        sendButton.textContent = 'Send';
        sendButton.style.padding = '10px 15px';
        sendButton.style.backgroundColor = '#4F46E5';
        sendButton.style.color = 'white';
        sendButton.style.border = 'none';
        sendButton.style.borderRadius = '20px';
        sendButton.style.cursor = 'pointer';
        
        inputArea.appendChild(textInput);
        inputArea.appendChild(sendButton);
        
        // Assemble chat window
        chatWindow.appendChild(chatHeader);
        chatWindow.appendChild(messagesContainer);
        chatWindow.appendChild(inputArea);
        
        // Add elements to container
        widgetContainer.appendChild(chatWindow);
        widgetContainer.appendChild(chatButton);
        
        // Add container to body
        document.body.appendChild(widgetContainer);
        
        // Add event listeners
        chatButton.addEventListener('click', () => {
            chatWindow.style.display = 'flex';
            chatButton.style.display = 'none';
        });
        
        document.getElementById('agentx-close-chat').addEventListener('click', () => {
            chatWindow.style.display = 'none';
            chatButton.style.display = 'flex';
        });
        
        // Actual API integration for sending messages
        const sendMessage = async () => {
            const input = document.getElementById('agentx-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            const userMessageElement = document.createElement('div');
            userMessageElement.className = 'agentx-message user-message';
            userMessageElement.style.backgroundColor = '#dcf8c6';
            userMessageElement.style.color = '#333';
            userMessageElement.style.padding = '10px 15px';
            userMessageElement.style.borderRadius = '10px';
            userMessageElement.style.marginBottom = '10px';
            userMessageElement.style.maxWidth = '80%';
            userMessageElement.style.marginLeft = 'auto';
            userMessageElement.textContent = message;
            
            messagesContainer.appendChild(userMessageElement);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            input.value = '';
            
            // Show typing indicator
            const typingIndicator = document.createElement('div');
            typingIndicator.className = 'agentx-message bot-message typing';
            typingIndicator.style.backgroundColor = '#e6e6fa';
            typingIndicator.style.color = '#333';
            typingIndicator.style.padding = '10px 15px';
            typingIndicator.style.borderRadius = '10px';
            typingIndicator.style.marginBottom = '10px';
            typingIndicator.style.maxWidth = '80%';
            typingIndicator.innerHTML = '<span>Typing</span><span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>';
            
            messagesContainer.appendChild(typingIndicator);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            try {
                // Call the deployment API endpoint
                const response = await fetch(`${config.apiBaseUrl}/api/v1/deployment/${config.deploymentId}/query`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        question: message,
                        agent_name: config.agentName
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to get response');
                }
                
                const data = await response.json();
                
                // Remove typing indicator
                messagesContainer.removeChild(typingIndicator);
                
                // Add bot response
                const botMessageElement = document.createElement('div');
                botMessageElement.className = 'agentx-message bot-message';
                botMessageElement.style.backgroundColor = '#e6e6fa';
                botMessageElement.style.color = '#333';
                botMessageElement.style.padding = '10px 15px';
                botMessageElement.style.borderRadius = '10px';
                botMessageElement.style.marginBottom = '10px';
                botMessageElement.style.maxWidth = '80%';
                botMessageElement.textContent = data.response || 'Sorry, I couldn\'t process your request.';
                
                messagesContainer.appendChild(botMessageElement);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            } catch (error) {
                console.error('Error sending message:', error);
                
                // Remove typing indicator
                messagesContainer.removeChild(typingIndicator);
                
                // Add error message
                const errorMessageElement = document.createElement('div');
                errorMessageElement.className = 'agentx-message bot-message error';
                errorMessageElement.style.backgroundColor = '#ffebee';
                errorMessageElement.style.color = '#c62828';
                errorMessageElement.style.padding = '10px 15px';
                errorMessageElement.style.borderRadius = '10px';
                errorMessageElement.style.marginBottom = '10px';
                errorMessageElement.style.maxWidth = '80%';
                errorMessageElement.textContent = 'Sorry, there was an error processing your request. Please try again later.';
                
                messagesContainer.appendChild(errorMessageElement);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        };
        
        sendButton.addEventListener('click', sendMessage);
        
        textInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Add some basic CSS for typing animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes typing {
                0% { opacity: 0.3; }
                50% { opacity: 1; }
                100% { opacity: 0.3; }
            }
            
            #agentx-messages .typing .dot {
                animation: typing 1.4s infinite;
                display: inline-block;
            }
            
            #agentx-messages .typing .dot:nth-child(2) {
                animation-delay: 0.2s;
            }
            
            #agentx-messages .typing .dot:nth-child(3) {
                animation-delay: 0.4s;
            }
        `;
        document.head.appendChild(style);
    };
    
    // Initialize widget when DOM is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChatWidget);
    } else {
        initChatWidget();
    }
})(); 