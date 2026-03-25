<template>
  <aside class="history-panel">
    <div class="panel-header">
      <h3>最近分析</h3>
      <span class="panel-count">{{ items.length }}/10</span>
    </div>

    <div v-if="loading" class="panel-empty">正在加载历史记录...</div>
    <div v-else-if="!items.length" class="panel-empty">暂无历史记录</div>
    <template v-else>
      <button
        v-for="item in items"
        :key="item.bvid"
        type="button"
        class="history-item"
        @click="$emit('select', item)"
      >
        <img
          v-if="item.cover"
          :src="item.cover"
          :alt="item.title"
          class="history-cover"
          loading="lazy"
          referrerpolicy="no-referrer"
        />
        <div class="history-content">
          <div class="history-bvid">{{ item.bvid }}</div>
          <div class="history-title">{{ item.title }}</div>
          <div class="history-meta">{{ item.author }} · {{ item.composite_score_formatted || item.composite_score }}</div>
          <div class="history-summary">
            {{ item.content_summary || '已记录基础分析结果，点击重新查看' }}
          </div>
          <div class="history-time">{{ item.updated_at }}</div>
        </div>
      </button>
    </template>
  </aside>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

defineEmits(['select'])
</script>

<style scoped>
.history-panel {
  position: sticky;
  top: 24px;
  align-self: flex-start;
  width: 320px;
  max-height: calc(100vh - 48px);
  overflow-y: auto;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  box-shadow: var(--shadow-subtle);
  padding: 18px;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.panel-header h3 {
  font-size: 16px;
  font-weight: 600;
}
.panel-count {
  font-size: 12px;
  color: var(--text-muted);
}
.panel-empty {
  font-size: 13px;
  color: var(--text-muted);
  padding: 12px 4px;
}
.history-item {
  width: 100%;
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border: none;
  border-top: 1px solid #f1f2f3;
  background: transparent;
  text-align: left;
  cursor: pointer;
}
.history-item:first-of-type {
  border-top: none;
}
.history-cover {
  width: 88px;
  height: 56px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
}
.history-content {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.history-bvid {
  font-size: 11px;
  color: var(--primary-color);
  font-weight: 600;
}
.history-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}
.history-meta,
.history-time {
  font-size: 12px;
  color: var(--text-muted);
}
.history-summary {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}
@media (max-width: 1100px) {
  .history-panel {
    width: 100%;
    max-height: none;
    position: static;
  }
}
</style>
