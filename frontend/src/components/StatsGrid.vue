<template>
  <div class="stats-grid">
    <div class="stat-card" v-for="item in stats" :key="item.label">
      <span class="label">{{ item.label }}</span>
      <span class="value">{{ item.value }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  info: { type: Object, required: true },
})

const stats = computed(() => [
  { label: '播放量', value: props.info.view_formatted },
  { label: '弹幕',   value: props.info.danmaku_formatted },
  { label: '点赞',   value: props.info.like_formatted },
  { label: '投币',   value: props.info.coin_formatted },
  { label: '收藏',   value: props.info.favorite_formatted },
  { label: '分享',   value: props.info.share_formatted },
])
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.stat-card {
  background: var(--card-bg);
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  box-shadow: var(--shadow-subtle);
}
.stat-card .label { font-size: 12px; color: var(--text-muted); }
.stat-card .value { font-size: 18px; font-weight: 600; color: var(--text-primary); }
@media (max-width: 640px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
