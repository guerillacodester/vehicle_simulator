<template>
  <div class="service-card glass-card">
    <div class="service-header">
      <div class="service-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="12" :fill="iconColor" />
          <text x="12" y="16" text-anchor="middle" font-size="16" fill="#fff" font-weight="bold">{{ service.display_name.charAt(0).toUpperCase() }}</text>
        </svg>
      </div>
      <div class="service-title">{{ service.display_name }}</div>
    </div>
    <span :class="['status-badge', service.state]">{{ service.state }}</span>
    <div class="buttons">
      <button class="btn btn-start" @click="start" :disabled="service.state === 'running'">Start</button>
      <button class="btn btn-stop" @click="stop" :disabled="service.state === 'stopped'">Stop</button>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';

export default defineComponent({
  name: 'ServiceCard',
  props: {
    service: {
      type: Object as PropType<{ name: string; display_name: string; state: 'running' | 'stopped' | 'unknown'; }>,
      required: true
    }
  },
  computed: {
    iconColor(): string {
      // Amber for running, gray for stopped, yellow for unknown
      if (this.service.state === 'running') return '#FFC107';
      if (this.service.state === 'stopped') return '#64748b';
      return '#FFD700';
    }
  },
  methods: {
    async start() {
      const result = await (window as any).electronAPI.startService(this.service.name);
      alert(result.message);
    },
    async stop() {
      const result = await (window as any).electronAPI.stopService(this.service.name);
      alert(result.message);
    }
  }
});
</script>

<style scoped>

/* Theme tokens */
:root {
  --color-bg-card: #0b1224cc;
  --color-border-card: #1e293b;
  --color-amber: #FFC107;
  --color-amber-dark: #FFB300;
  --color-gray: #64748b;
  --color-shadow-card: 0 4px 24px rgba(0,0,0,0.18);
  --color-shadow-card-hover: 0 8px 32px rgba(255,199,38,0.18);
}

.glass-card {
  background: var(--color-bg-card);
  border: 1.5px solid var(--color-border-card);
  border-radius: 18px;
  box-shadow: var(--color-shadow-card);
  padding: 2rem 1.5rem 1.5rem 1.5rem;
  color: #fff;
  backdrop-filter: blur(8px);
  transition: box-shadow 0.2s, border-color 0.2s, transform 0.25s cubic-bezier(.23,1.01,.32,1);
  will-change: transform;
  perspective: 800px;
}
.glass-card:hover {
  box-shadow: var(--color-shadow-card-hover);
  border-color: var(--color-amber);
  transform: scale(1.04) translateY(-8px) rotateX(6deg) rotateY(-3deg);
}

.service-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}
.service-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-amber), var(--color-amber-dark));
  border-radius: 50%;
  box-shadow: 0 0 12px var(--color-amber);
}
.service-title {
  font-weight: 700;
  font-size: 1.25em;
  letter-spacing: 0.02em;
  color: var(--color-amber);
  text-shadow: 0 0 8px rgba(255,199,38,0.5);
}
.status-badge {
  padding: 5px 14px;
  border-radius: 6px;
  margin-top: 10px;
  display: inline-block;
  font-weight: 600;
  font-size: 0.95em;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}
.status-badge.running {
  background: linear-gradient(90deg, #FFC107 60%, #FFD700 100%);
  color: #222;
}
.status-badge.stopped {
  background: linear-gradient(90deg, #64748b 60%, #94a3b8 100%);
  color: #fff;
}
.status-badge.unknown {
  background: linear-gradient(90deg, #FFD700 60%, #FFFACD 100%);
  color: #222;
}
.buttons {
  margin-top: 18px;
  display: flex;
  gap: 12px;
}
.btn {
  font-weight: 700;
  font-size: 1em;
  border-radius: 8px;
  padding: 10px 22px;
  border: none;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  transition: background 0.18s, box-shadow 0.18s;
}
.btn-start {
  background: linear-gradient(90deg, #FFC107 60%, #FFD700 100%);
  color: #222;
}
.btn-start:disabled {
  background: #e2e8f0;
  color: #888;
  cursor: not-allowed;
}
.btn-stop {
  background: linear-gradient(90deg, #64748b 60%, #94a3b8 100%);
  color: #fff;
}
.btn-stop:disabled {
  background: #e2e8f0;
  color: #888;
  cursor: not-allowed;
}
</style>