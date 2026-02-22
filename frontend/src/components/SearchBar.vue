<template>
  <div class="search-section">
    <div class="input-group">
      <input
        type="text"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        placeholder="请输入B站视频链接 (BV...)"
        @keyup.enter="$emit('search')"
        :disabled="loading"
      />
      <button
        class="analyze-btn"
        @click="$emit('search')"
        :disabled="loading || !modelValue.trim()"
      >
        <span v-if="loading" class="spinner"></span>
        <span v-else>分析</span>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: String, required: true },
  loading: { type: Boolean, default: false },
})
defineEmits(['update:modelValue', 'search'])
</script>

<style scoped>
.search-section {
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
}
.input-group {
  display: flex;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 4px;
  transition: border-color 0.2s;
}
.input-group:focus-within { border-color: var(--primary-color); }
.input-group input {
  flex: 1;
  border: none;
  padding: 12px 16px;
  font-size: 14px;
  outline: none;
  background: transparent;
}
.analyze-btn {
  background: var(--primary-color);
  color: white;
  border: none;
  padding: 0 24px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}
.analyze-btn:hover:not(:disabled) { opacity: 0.9; }
.analyze-btn:disabled { background: #ccd0d7; cursor: not-allowed; }
.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
