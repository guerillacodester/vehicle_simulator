<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-content">
        <h1 class="app-title neon-text">ArkNet Fleet Manager</h1>
      </div>
    </header>
    <main class="app-main">
      <div class="main-container">
        <LoginCard v-if="!isAuthenticated" />
        <ServicesView v-if="isAuthenticated" />
      </div>
    </main>
  </div>
</template>


<script>
import { defineComponent, ref, onMounted } from 'vue';
import ServicesView from './components/ServicesView.vue';
import LoginCard from './components/LoginCard.vue';
import authProvider from './utils/authProvider';
import socketProvider from './utils/socketProvider';
import { useServiceStore } from './store/services';

export default defineComponent({
  name: 'App',
  components: { ServicesView, LoginCard },
  setup() {
    console.log('[App] 🚀 App.vue setup() called');
    const isAuthenticated = ref(false);
    const user = ref(null);
    const accessTier = ref(null);
    const serviceStore = useServiceStore();
    console.log('[App] 🗂️ Service store initialized:', serviceStore);

    function handleLoginSuccess(e) {
      console.log('[App] 🔐 Login successful:', e.detail);
      isAuthenticated.value = true;
      user.value = e.detail.user;
      accessTier.value = e.detail.user?.tier || e.detail.user?.roles || null;
      // Socket.IO is already connected - no need to reconnect
    }

    onMounted(() => {
      console.log('[App] 🎬 onMounted() - Connecting Socket.IO immediately for local service management');
      // CRITICAL FIX: Connect Socket.IO immediately without waiting for auth
      // This is a local Electron app managing local services - no auth barrier needed for Socket.IO
      socketProvider.connect({
        url: 'http://localhost:7000',
        token: undefined, // No token needed for local service management
        maxRetries: 5,
        backoffBase: 1000,
        backoffMax: 10000
      });
      
      // Setup Socket.IO event listeners
      socketProvider.on('service_status', (event) => {
        console.log('[App] 📨 Received service_status event:', JSON.stringify(event, null, 2));
        if (event && event.service_name) {
          console.log(`[App] 🔍 Processing event for service: ${event.service_name}, backend state: ${event.state}`);
          // Map backend state values to UI state values
          const stateMap = {
            'healthy': 'running',
            'running': 'running',
            'starting': 'running',
            'stopped': 'stopped',
            'unhealthy': 'stopped',
            'failed': 'stopped'
          };
          const mappedState = stateMap[event.state] || 'unknown';
          console.log(`[App] 🔄 Mapped state ${event.state} -> ${mappedState}`);
          console.log(`[App] 🗂️ Store before update:`, JSON.stringify(serviceStore.services.map(s => ({name: s.name, state: s.state})), null, 2));
          serviceStore.updateServiceState(event.service_name, mappedState);
          console.log(`[App] 🗂️ Store after update:`, JSON.stringify(serviceStore.services.map(s => ({name: s.name, state: s.state})), null, 2));
          console.log(`[App] ✅ Updated ${event.service_name} state to ${mappedState}`);
        } else {
          console.warn('[App] ⚠️ Invalid event received:', event);
        }
      });
      
      socketProvider.on('connect', () => {
        console.log('[App] ✅ Socket.IO connected - ready to receive service status updates');
      });
      
      socketProvider.on('disconnect', () => {
        console.warn('[App] ⚠️ Socket.IO disconnected');
      });
      
      window.addEventListener('login-success', handleLoginSuccess);
      // Check for existing session on startup
      const session = authProvider.getSession();
      if (session && authProvider.isAuthenticated()) {
        isAuthenticated.value = true;
        user.value = session.user;
        accessTier.value = authProvider.getAccessTier();
      }
    });

    return { isAuthenticated, user, accessTier };
  }
});

</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background-color: #000000;
}

.app-header {
  background-color: #0a0a0a;
  border-bottom: 1px solid rgba(255, 199, 38, 0.2);
  padding: 16px 32px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-content {
  flex: 1;
  text-align: center;
}

.app-title {
  font-size: 2.5rem;
  font-weight: 900;
  color: #FFC726;
  margin: 0;
  text-shadow: 0 0 10px rgba(255, 199, 38, 0.5), 0 0 20px rgba(255, 199, 38, 0.3);
  letter-spacing: 0.1em;
  font-family: 'Rajdhani', Arial, sans-serif;
}

.app-main {
  background-color: #000000;
  min-height: calc(100vh - 65px);
  padding: 32px;
  transition: background-color 0.3s;
}

.main-container {
  max-width: 1400px;
  margin: 0 auto;
}
</style>