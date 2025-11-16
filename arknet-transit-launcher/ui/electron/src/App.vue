<template>
  <div id="app">
    <header>
      <h1>ArkNet Transit Launcher</h1>
      <p>Manage transit services</p>
    </header>

    <main>
      <div class="services">
        <ServiceCard
          v-for="service in services"
          :key="service.name"
          :service="service"
          @start="startService"
          @stop="stopService"
        />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ServiceCard from './components/ServiceCard.vue'

interface Service {
  name: string
  displayName: string
  status: 'running' | 'stopped' | 'unknown'
}

const services = ref<Service[]>([
  { name: 'redis', displayName: 'Redis Cache', status: 'unknown' },
  { name: 'strapi', displayName: 'Strapi CMS', status: 'unknown' }
])

const loadServices = async () => {
  try {
    const status = await (window as any).electronAPI.getServicesStatus()
    services.value = services.value.map(service => ({
      ...service,
      status: status[service.name] || 'unknown'
    }))
  } catch (error) {
    console.error('Failed to load services:', error)
  }
}

const startService = async (serviceName: string) => {
  try {
    const result = await (window as any).electronAPI.startService(serviceName)
    alert(result.message)
    loadServices()
  } catch (error) {
    alert(`Failed to start ${serviceName}`)
  }
}

const stopService = async (serviceName: string) => {
  try {
    const result = await (window as any).electronAPI.stopService(serviceName)
    alert(result.message)
    loadServices()
  } catch (error) {
    alert(`Failed to stop ${serviceName}`)
  }
}

onMounted(() => {
  loadServices()
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

.services {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}
</style>