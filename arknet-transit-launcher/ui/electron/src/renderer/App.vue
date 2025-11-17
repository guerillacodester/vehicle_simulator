<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-content">
        <h1 class="app-title neon-text">ArkNet Fleet Manager</h1>
      </div>
    </header>
    <main class="app-main">
      <div class="main-container">
        <ServicesView />
      </div>
    </main>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import ServicesView from './components/ServicesView.vue';

export default defineComponent({
  name: 'App',
  components: { ServicesView },
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