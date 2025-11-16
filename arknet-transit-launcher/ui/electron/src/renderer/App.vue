<template>
  <div class="app-container glass-bg">
    <header class="app-header">
      <h1 class="app-title">ArkNet Transit Launcher</h1>
      <p class="app-desc">Manage transit services</p>
    </header>
    <ServicesView />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import ServicesView from './components/ServicesView.vue';

export default defineComponent({
  name: 'App',
  components: { ServicesView },
  // Pinia initialization is performed at app bootstrap in main.ts
});
</script>

<style scoped>
/* Theme tokens */
:root {
  --color-bg-main: #000b2a;
  --color-bg-gradient: linear-gradient(135deg, #000b2a 0%, #00133f 100%);
  --color-header-gradient: linear-gradient(90deg, #FFC107 0%, #FFD700 100%);
}

.glass-bg {
  min-height: 100vh;
  background: var(--color-bg-gradient);
  padding: 0;
}
.app-header {
  text-align: center;
  margin-bottom: 32px;
  padding: 2.5rem 0 1.5rem 0;
  background: rgba(11,18,36,0.7);
  border-bottom: 2px solid #FFC10722;
  box-shadow: 0 2px 16px rgba(255,199,38,0.08);
  backdrop-filter: blur(6px);
}
.app-title {
  font-size: 2.5rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  background: var(--color-header-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-fill-color: transparent;
  text-shadow: 0 0 18px rgba(255,199,38,0.3);
}
.app-desc {
  font-size: 1.15rem;
  color: #fff;
  opacity: 0.85;
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
}
</style>