/**
 * AgentX Embed Script
 * Use this script to embed an AgentX chat widget on your website
 * Usage: 
 * - Full: <script src="https://your-agentx-url/static/embed.js" data-agent="agent-name" data-deployment-id="deploy-id"></script>
 * - Short: <script src="https://your-agentx-url/s/SHORT_ID"></script>
 */

(function() {
    // Get the current script element
    const currentScript = document.currentScript;
    
    // Get configuration from script attributes or URL parameters
    let agentName, deploymentId, theme, position;
    
    // Check if this is a shortened URL by checking the URL path
    const scriptSrc = currentScript.src;
    const urlObj = new URL(scriptSrc);
    
    if (urlObj.pathname.startsWith('/s/')) {
        // This is a shortened URL - get parameters from query string
        const urlParams = new URLSearchParams(urlObj.search);
        agentName = urlParams.get('agent');
        deploymentId = urlParams.get('id');
        theme = urlParams.get('theme') || 'light';
        position = urlParams.get('pos') || 'bottom-right';
    } else {
        // Regular embed - get parameters from data attributes
        agentName = currentScript.getAttribute('data-agent') || '';
        deploymentId = currentScript.getAttribute('data-deployment-id') || '';
        theme = currentScript.getAttribute('data-theme') || 'light';
        position = currentScript.getAttribute('data-position') || 'bottom-right';
    }
    
    if (!agentName || !deploymentId) {
        console.error('AgentX Widget Error: Missing required attributes (agent name and deployment ID)');
        return;
    }
    
    // Get the base URL from the current script src
    const baseUrl = scriptSrc.substring(0, scriptSrc.lastIndexOf('/s/') > 0 ? 
        scriptSrc.lastIndexOf('/s/') : scriptSrc.lastIndexOf('/static'));
    
    // Create a new script element to load the chat widget
    const widgetScript = document.createElement('script');
    widgetScript.src = `${baseUrl}/static/chat-widget.js`;
    
    // Add configuration to window for the widget script to access
    window.AgentXConfig = {
        agentName: agentName,
        deploymentId: deploymentId,
        theme: theme,
        position: position,
        baseUrl: baseUrl
    };
    
    // Append the script to the head
    document.head.appendChild(widgetScript);
    
    console.log(`AgentX Widget: Initializing for agent "${agentName}" with deployment ID "${deploymentId}"`);
})(); 