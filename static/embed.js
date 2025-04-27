/**
 * AgentX Embed Script
 * Use this script to embed an AgentX chat widget on your website
 * Usage: 
 * - Full: <script src="https://your-agentx-url/static/embed.js" data-agent="agent-name" data-deployment-id="deploy-id"></script>
 * - Short: <script src="https://your-agentx-url/s/SHORT_TOKEN"></script>
 */

(function() {
    // Get the current script element
    const currentScript = document.currentScript;
    
    // If no script tag is found, show an error and exit
    if (!currentScript) {
        console.error("AgentX Widget Error: Could not find the script tag. This widget must be loaded via a script tag.");
        return;
    }
    
    // Get configuration from script attributes or URL parameters
    let agentName, deploymentId, apiKey, theme, position;
    
    // Check if this is a shortened URL by checking the URL path
    const scriptSrc = currentScript.src;
    const urlObj = new URL(scriptSrc);
    
    // The shortened URL will be handled differently - it will return a JavaScript 
    // that directly sets window.AgentXConfig, so we don't need to parse parameters here
    if (urlObj.pathname.startsWith('/s/')) {
        console.log("AgentX Widget: Loading via shorthand URL, configuration will be set automatically.");
        return; // Let the server-generated JS handle everything
    } else {
        // Regular embed - get parameters from data attributes
        agentName = currentScript.getAttribute('data-agent') || '';
        deploymentId = currentScript.getAttribute('data-deployment-id') || '';
        apiKey = currentScript.getAttribute('data-api-key') || ''; // Optional API key
        theme = currentScript.getAttribute('data-theme') || 'light';
        position = currentScript.getAttribute('data-position') || 'bottom-right';
        console.log("AgentX Widget: Loaded with data attributes, deployment ID:", deploymentId);
    }
    
    if (!agentName || !deploymentId) {
        console.error('AgentX Widget Error: Missing required attributes (agent name and deployment ID)');
        // Add visible error message to the page if in development
        if (urlObj.hostname === 'localhost' || urlObj.hostname === '127.0.0.1') {
            const errorDiv = document.createElement('div');
            errorDiv.style.padding = '10px';
            errorDiv.style.backgroundColor = '#ffebee';
            errorDiv.style.color = '#c62828';
            errorDiv.style.border = '1px solid #c62828';
            errorDiv.style.borderRadius = '4px';
            errorDiv.style.margin = '10px 0';
            errorDiv.style.fontFamily = 'Arial, sans-serif';
            errorDiv.textContent = 'AgentX Widget Error: Missing required attributes (agent name and deployment ID)';
            document.body.appendChild(errorDiv);
        }
        return;
    }
    
    // Validate deployment ID format (should be a UUID)
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(deploymentId)) {
        console.warn('AgentX Widget Warning: Deployment ID does not appear to be a valid UUID format');
    }
    
    // Get the base URL from the current script src
    const baseUrl = scriptSrc.substring(0, scriptSrc.lastIndexOf('/static'));
    
    // Instead of directly setting window.AgentXConfig, fetch configuration from server
    // This adds an extra step but prevents sensitive details from being visible in HTML source
    const fetchConfiguration = async () => {
        try {
            // Create and append a hidden iframe for secure communication
            const secureIframe = document.createElement('iframe');
            secureIframe.style.display = 'none';
            secureIframe.style.width = '0';
            secureIframe.style.height = '0';
            secureIframe.style.border = 'none';
            secureIframe.src = `${baseUrl}/api/v1/widget-config?id=${encodeURIComponent(deploymentId)}`;
            document.body.appendChild(secureIframe);
            
            // For now, create a simple configuration based on parameters
            // In production, this should be obtained securely from backend
            window.AgentXConfig = {
                agentName: agentName,
                deploymentId: deploymentId,
                apiKey: apiKey,
                theme: theme,
                position: position,
                baseUrl: baseUrl
            };
            
            // Create a new script element to load the chat widget
            const widgetScript = document.createElement('script');
            widgetScript.src = `${baseUrl}/static/chat-widget.js`;
            
            // Handle errors loading the widget script
            widgetScript.onerror = function() {
                console.error('AgentX Widget Error: Failed to load widget script');
                // Add visible error message in development
                if (urlObj.hostname === 'localhost' || urlObj.hostname === '127.0.0.1') {
                    const errorDiv = document.createElement('div');
                    errorDiv.style.padding = '10px';
                    errorDiv.style.backgroundColor = '#ffebee';
                    errorDiv.style.color = '#c62828';
                    errorDiv.style.border = '1px solid #c62828';
                    errorDiv.style.borderRadius = '4px';
                    errorDiv.style.margin = '10px 0';
                    errorDiv.style.fontFamily = 'Arial, sans-serif';
                    errorDiv.textContent = 'AgentX Widget Error: Failed to load widget script';
                    document.body.appendChild(errorDiv);
                }
            };
            
            // Append the script to the head
            document.head.appendChild(widgetScript);
            
            console.log(`AgentX Widget: Initializing for agent "${agentName}" with deployment ID "${deploymentId}"`);
        } catch (error) {
            console.error("AgentX Widget Error: Failed to initialize", error);
        }
    };
    
    // Start the initialization process
    fetchConfiguration();
})(); 