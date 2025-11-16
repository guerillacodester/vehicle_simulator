<template>
  <div class="services-container glass-section">
    <div class="services-grid">
      <ServiceCard v-for="service in services" :key="service.name" :service="service" />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useServiceStore } from '../store/services';
import ServiceCard from './ServiceCard.vue';

export default defineComponent({
  name: 'ServicesView',
  components: { ServiceCard },
  setup() {
    const store = useServiceStore();
    const { services } = storeToRefs(store);

    async function loadStatus() {
      await store.loadServices();
    }

    onMounted(() => {
      loadStatus();
      setInterval(loadStatus, 5000);
    });

    return { services };
  }
});
</script>

<style scoped>

.glass-section {
  padding: 2rem 2vw;
  background: rgba(11,18,36,0.5);
  border-radius: 24px;
  box-shadow: 0 4px 32px rgba(0,0,0,0.18);
  margin-bottom: 2rem;
  backdrop-filter: blur(4px);
}
.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 2rem;
}
</style>