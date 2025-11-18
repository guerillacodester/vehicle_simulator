<template>
  <div class="login-card-wrapper">
    <div class="login-card">
      <h2 class="login-title">Login</h2>
      <form @submit.prevent="onLogin">
        <div class="form-group">
          <label for="username">Username</label>
          <input id="username" v-model="username" type="text" required />
        </div>
        <div class="form-group">
          <label for="password">Password</label>
          <input id="password" v-model="password" type="password" required />
        </div>
        <button type="submit" class="btn-login" :disabled="loading">
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
        <div v-if="error" class="login-error">{{ error }}</div>
      </form>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue';

export default defineComponent({
  name: 'LoginCard',
  setup() {
    const username = ref('');
    const password = ref('');
    const loading = ref(false);
    const error = ref('');

    async function onLogin() {
      loading.value = true;
      error.value = '';
      try {
        // Call backend /login endpoint
        const resp = await fetch('http://localhost:7000/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: username.value, password: password.value }),
          credentials: 'include' // allow cookies
        });
        if (!resp.ok) {
          const err = await resp.json();
          error.value = err.detail || 'Login failed.';
          return;
        }
        // Success: notify parent to update authenticated state
        // Optionally parse user info from response
        const result = await resp.json();
        window.dispatchEvent(new CustomEvent('login-success', { detail: result }));
      } catch (e: any) {
        error.value = e.message || 'Login error.';
      } finally {
        loading.value = false;
      }
    }

    return { username, password, loading, error, onLogin };
  }
});
</script>

<style scoped>
.login-card-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}
.login-card {
  background: rgba(11, 18, 36, 0.9);
  border-radius: 0.75rem;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
  padding: 2rem 2.5rem;
  width: 350px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}
.login-title {
  color: #FFC726;
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  text-align: center;
}
.form-group {
  margin-bottom: 1.25rem;
  display: flex;
  flex-direction: column;
}
label {
  color: #fff;
  font-size: 0.95rem;
  margin-bottom: 0.5rem;
}
input {
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  border: 1px solid #FFC726;
  background: #181f2a;
  color: #FFC726;
  font-size: 1rem;
}
.btn-login {
  background: #FFC726;
  color: #181f2a;
  font-weight: 700;
  border: none;
  border-radius: 0.375rem;
  padding: 0.75rem;
  font-size: 1rem;
  cursor: pointer;
  margin-top: 0.5rem;
  transition: background 0.2s;
}
.btn-login:disabled {
  background: #cbb26a;
  cursor: not-allowed;
}
.login-error {
  color: #fca5a5;
  font-size: 0.95rem;
  margin-top: 1rem;
  text-align: center;
}
</style>
