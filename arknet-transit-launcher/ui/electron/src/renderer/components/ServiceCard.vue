<template>
  <div class="service-card-wrapper">
    <div 
      class="service-card"
      ref="cardRef"
    >
      <!-- Header -->
      <div class="card-header">
        <div class="header-content">
          <div class="title-row">
            <span class="service-icon-emoji">{{ service.icon || getServiceIcon(service.state) }}</span>
            <h3 class="service-name">{{ service.display_name || service.name }}</h3>
          </div>
          <p v-if="service.description" class="service-description">
            {{ service.description }}
          </p>
        </div>
        <span class="status-badge" :class="`status-${service.state}`">
          {{ service.state }}
        </span>
      </div>

      <!-- Main Content - Flexible -->
      <div class="card-content">
        <div v-if="service.port" class="detail-item">
          <span class="detail-label">Port:</span>
          <code class="detail-value">{{ service.port }}</code>
        </div>
        <div v-if="service.pid" class="detail-item">
          <span class="detail-label">PID:</span>
          <code class="detail-value">{{ service.pid }}</code>
        </div>
      </div>

      <!-- Status Bar - Fixed height -->
      <div class="status-bar" :class="{ 'has-message': service.message }">
        {{ service.message || '' }}
      </div>

      <!-- Buttons - Fixed at bottom -->
      <div v-if="service.type !== 'dependency'" class="card-actions">
        <button
          @click="start"
          :disabled="isRunning"
          class="btn btn-start"
        >
          ▶ Start
        </button>
        <button
          @click="stop"
          :disabled="!isRunning"
          class="btn btn-stop"
        >
          ⏹ Stop
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType, computed } from 'vue';

interface Service {
  name: string;
  display_name?: string;
  description?: string;
  state: string;
  port?: number;
  pid?: number;
  message?: string;
  icon?: string;
  type?: string;
}

export default defineComponent({
  name: 'ServiceCard',
  props: {
    service: {
      type: Object as PropType<Service>,
      required: true
    }
  },
  setup(props) {
    const isRunning = computed(() => 
      props.service.state === 'running' || props.service.state === 'healthy'
    );

    const getServiceIcon = (state: string): string => {
      const icons: Record<string, string> = {
        running: '🟢',
        healthy: '🟢',
        starting: '🟡',
        stopped: '⚪',
        failed: '🔴',
        unhealthy: '🟠',
        not_configured: '⚙️',
        unreachable: '❌',
      };
      return icons[state] || '⚪';
    };

    return {
      isRunning,
      getServiceIcon
    };
  },
  methods: {
    async start() {
      const result = await (window as any).electronAPI.startService(this.service.name);
      console.log('Start result:', result);
    },
    async stop() {
      const result = await (window as any).electronAPI.stopService(this.service.name);
      console.log('Stop result:', result);
    }
  }
});
</script>

<style scoped>
.service-card-wrapper {
  position: relative;
  height: 280px;
}

.service-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: rgba(11, 18, 36, 0.8);
  border: 1px solid rgba(255, 199, 38, 0.2);
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  transition: all 200ms ease-in-out;
}

.service-card:hover {
  box-shadow: 0 0 20px rgba(255, 199, 38, 0.3), 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  border-color: rgba(255, 199, 38, 0.5);
  transform: translateY(-2px);
}

/* Header */
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255, 199, 38, 0.2);
}

.header-content {
  flex: 1;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.service-icon-emoji {
  font-size: 1.25rem;
  line-height: 1;
}

.service-name {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #FFC726;
  letter-spacing: -0.01em;
}

.service-description {
  margin: 0;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.4;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.status-running,
.status-badge.status-healthy {
  background-color: rgba(34, 197, 94, 0.2);
  color: #86efac;
  border: 1px solid rgba(34, 197, 94, 0.4);
}

.status-badge.status-starting {
  background-color: rgba(234, 179, 8, 0.2);
  color: #fde047;
  border: 1px solid rgba(234, 179, 8, 0.4);
}

.status-badge.status-stopped {
  background-color: rgba(148, 163, 184, 0.2);
  color: #cbd5e1;
  border: 1px solid rgba(148, 163, 184, 0.4);
}

.status-badge.status-failed,
.status-badge.status-unhealthy {
  background-color: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
  border: 1px solid rgba(239, 68, 68, 0.4);
}

/* Main Content - Flexible */
.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.detail-label {
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
  min-width: 45px;
}

.detail-value {
  font-family: 'Courier New', monospace;
  background-color: rgba(255, 199, 38, 0.1);
  color: #FFC726;
  padding: 2px 8px;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
  font-weight: 500;
  border: 1px solid rgba(255, 199, 38, 0.3);
}

/* Status Bar - Fixed height */
.status-bar {
  height: 3rem;
  display: flex;
  align-items: center;
  padding: 0.5rem;
  border-radius: 0.375rem;
  margin-bottom: 1rem;
  font-size: 0.8125rem;
  line-height: 1.4;
  color: transparent;
  transition: all 200ms;
}

.status-bar.has-message {
  background-color: rgba(255, 199, 38, 0.1);
  border: 1px solid rgba(255, 199, 38, 0.3);
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

/* Buttons - Fixed at bottom */
.card-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.btn {
  padding: 0.625rem 1rem;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-start {
  background-color: rgba(34, 197, 94, 0.2);
  color: #86efac;
  border: 1px solid rgba(34, 197, 94, 0.4);
}

.btn-start:not(:disabled):hover {
  background-color: rgba(34, 197, 94, 0.3);
  border-color: rgba(34, 197, 94, 0.6);
}

.btn-start:disabled {
  background-color: rgba(100, 100, 100, 0.3);
  color: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(100, 100, 100, 0.3);
  cursor: not-allowed;
}

.btn-stop {
  background-color: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
  border: 1px solid rgba(239, 68, 68, 0.4);
}

.btn-stop:not(:disabled):hover {
  background-color: rgba(239, 68, 68, 0.3);
  border-color: rgba(239, 68, 68, 0.6);
}

.btn-stop:disabled {
  background-color: rgba(100, 100, 100, 0.3);
  color: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(100, 100, 100, 0.3);
  cursor: not-allowed;
}
</style>