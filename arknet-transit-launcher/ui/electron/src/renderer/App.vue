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

export default defineComponent({
  name: 'App',
  components: { ServicesView, LoginCard },
  setup() {
    const isAuthenticated = ref(false);
    const user = ref(null);
    const accessTier = ref(null);

    function connectSocket() {
      const session = authProvider.getSession();
      if (!session) return;
      socketProvider.connect({
        url: 'http://localhost:7000',
        token: session.jwt,
        maxRetries: 5,
        backoffBase: 1000,
        backoffMax: 10000
      });
      socketProvider.on('service_status', (event) => {
        // Handle service status events (update UI/state as needed)
        console.log('Service event:', event);
      });
      socketProvider.on('connect', () => {
        console.log('Socket connected');
      });
      socketProvider.on('disconnect', () => {
        console.log('Socket disconnected');
      });
    }

    function handleLoginSuccess(e) {
      isAuthenticated.value = true;
      user.value = e.detail.user;
      accessTier.value = e.detail.user?.tier || e.detail.user?.roles || null;
      connectSocket();
    }

    onMounted(() => {
      window.addEventListener('login-success', handleLoginSuccess);
      // Check for existing session on startup
      const session = authProvider.getSession();
      if (session && authProvider.isAuthenticated()) {
        isAuthenticated.value = true;
        user.value = session.user;
        accessTier.value = authProvider.getAccessTier();
        connectSocket();
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