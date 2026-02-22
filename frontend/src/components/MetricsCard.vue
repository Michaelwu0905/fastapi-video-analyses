<template>
  <div class="metrics-card">
    <h3>传播力指标</h3>
    <div class="metrics-grid">
      <div class="metric-item">
        <span class="metric-label">综合得分</span>
        <span class="metric-value">{{ info.composite_score_formatted }}</span>
        <span class="metric-raw">({{ info.composite_score }})</span>
      </div>
      <div class="metric-item">
        <span class="metric-label">粘性度</span>
        <span class="metric-value">{{ info.stickiness_percent }}</span>
        <span class="metric-raw">({{ info.stickiness }})</span>
      </div>
    </div>
    <div class="metrics-formula">
      <p>综合得分 = 0.728*播放 + 0.154*弹幕 + 0.327*投币 + 0.242*收藏 - 0.192*点赞 - 0.157*分享</p>
      <p>粘性度 = (投币 + 收藏 + 分享) / 播放量</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  info: { type: Object, required: true },
})
</script>

<style scoped>
.metrics-card {
  background: var(--card-bg);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-subtle);
}
.metrics-card h3 { font-size: 16px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; }
.metrics-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 16px; }
.metric-item {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.metric-label { font-size: 12px; color: var(--text-muted); }
.metric-value { font-size: 24px; font-weight: 700; color: var(--primary-color); }
.metric-raw { font-size: 11px; color: var(--text-muted); }
.metrics-formula { padding-top: 16px; border-top: 1px solid #f1f2f3; }
.metrics-formula p { font-size: 11px; color: var(--text-muted); line-height: 1.8; }
@media (max-width: 640px) {
  .metrics-grid { grid-template-columns: 1fr; }
}
</style>
