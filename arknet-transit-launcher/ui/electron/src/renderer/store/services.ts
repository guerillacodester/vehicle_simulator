
import { defineStore } from 'pinia';
import { ref } from 'vue';

export type ServiceState = 'running' | 'stopped' | 'unknown';
export interface ServiceModel {
  name: string;
  display_name: string;
  description: string;
  category: string;
  icon: string;
  port: string;
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
      // Add state field (default unknown)
      services.value = serviceList.map((s: any) => ({ ...s, state: 'unknown' }));
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

  return { services, loadServices, startService, stopService };
});