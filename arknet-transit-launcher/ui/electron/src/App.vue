<template>
  <div id="app">
    <header>
      <h1>ArkNet Transit Launcher</h1>
      <p>Manage transit services</p>
      <button @click="loadServices" class="refresh-btn">🔄 Refresh</button>
    </header>

    <main>
      <div v-if="loading" class="loading">Loading services...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else class="services">
        <ServiceCard
          v-for="service in services"
          :key="service.name"
          :service="service"
        />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import ServiceCard from './renderer/components/ServiceCard.vue'

interface Service {
  name: string
  display_name?: string
  description?: string
  state: string
  port?: number
  pid?: number
  message?: string
  icon?: string
  type?: string
}

const services = ref<Service[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
let refreshInterval: number | null = null

const loadServices = async () => {
  try {
    error.value = null
    const servicesData = await (window as any).electronAPI.getServicesStatus()
    
    if (Array.isArray(servicesData)) {
      services.value = servicesData
    } else {
      console.error('Invalid services data format:', servicesData)
      error.value = 'Invalid response from backend'
    }
  } catch (err) {
    console.error('Failed to load services:', err)
    error.value = 'Failed to connect to backend. Make sure launcher_server.py is running on port 7000.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadServices()
  // Auto-refresh every 5 seconds
  refreshInterval = window.setInterval(loadServices, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  margin: 0;
  padding: 20px;
  background-color: #1e1e1e;
  color: #ffffff;
  min-height: 100vh;
}

header {
  text-align: center;
  margin-bottom: 30px;
}

header h1 {
  margin: 0 0 0.5rem 0;
  color: #FFC726;
}

header p {
  margin: 0 0 1rem 0;
  color: rgba(255, 255, 255, 0.7);
}

.refresh-btn {
  padding: 0.5rem 1rem;
  background-color: rgba(255, 199, 38, 0.2);
  color: #FFC726;
  border: 1px solid rgba(255, 199, 38, 0.4);
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background-color: rgba(255, 199, 38, 0.3);
  border-color: rgba(255, 199, 38, 0.6);
}

.loading,
.error {
  text-align: center;
  padding: 2rem;
  font-size: 1.125rem;
}

.error {
  color: #fca5a5;
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 0.5rem;
  max-width: 600px;
  margin: 0 auto;
}

.services {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}
</style>