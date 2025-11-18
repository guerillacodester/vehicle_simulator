
import { defineStore } from 'pinia';
import { ref } from 'vue';

export type ServiceState = 'running' | 'stopped' | 'unknown';
export interface ServiceModel {
  name: string;
  display_name: string;
  description: string;
  category: string;
  icon: string;
  port: number;
  health_url: string;
  spawn_console: boolean;
  startup_wait: string;
  dependencies: string;
  state: ServiceState;
}

export const useServiceStore = defineStore('services', () => {
  const services = ref<ServiceModel[]>([]);

  async function loadServices() {
    try {
      // Get full service list from backend
      const serviceList = await (window as any).electronAPI.getServicesStatus();
      // Convert port to number for type safety
      services.value = serviceList.map((service: any) => ({
        ...service,
        port: service.port ? Number(service.port) : undefined,
      }));
    } catch (error) {
      console.error('Failed to load services', error);
    }
  }

  async function startService(name: string) {
    const res = await (window as any).electronAPI.startService(name);
    await loadServices();
    return res;
  }

  async function stopService(name: string) {
    const res = await (window as any).electronAPI.stopService(name);
    await loadServices();
    return res;
  }

  function updateServiceState(serviceName: string, newState: ServiceState) {
    console.log(`[Store] 🔧 updateServiceState called for ${serviceName} with state ${newState}`);
    const idx = services.value.findIndex(s => s.name === serviceName);
    console.log(`[Store] 🔍 Found service at index: ${idx}`);
    if (idx !== -1) {
      const oldState = services.value[idx].state;
      services.value[idx] = {
        ...services.value[idx],
        state: newState
      };
      console.log(`[Store] ✅ Updated ${serviceName} from ${oldState} to ${newState}`);
      console.log(`[Store] 🗂️ New service object:`, services.value[idx]);
    } else {
      console.warn(`[Store] ⚠️ Service ${serviceName} not found in store`);
    }
  }

  return { services, loadServices, startService, stopService, updateServiceState };
});