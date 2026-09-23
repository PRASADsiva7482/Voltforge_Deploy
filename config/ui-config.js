// =============================================================================
// VoltForge UI — External Runtime Configuration
// Loaded by index.html before React initializes (<script src="/config.js"></script>)
// =============================================================================
window.config = {
  keycloak: {
    url: window.location.origin,
    realm: 'voltforge-realm',
    clientId: 'VOLT-UI',
  },
  api: {
    baseUrl: window.location.origin + '/voltForge-app/api/v1',
    wsUrl: (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/voltForge-app/ws-native',
  },
  ai: {
    baseUrl: window.location.origin + '/voltForge-ai',
  },
};
