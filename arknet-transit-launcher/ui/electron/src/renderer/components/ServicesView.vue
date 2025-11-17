<template>
  <div class="services-container">
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
.services-container {
  width: 100%;
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

@media (min-width: 1024px) {
  .services-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1400px) {
  .services-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
</style>