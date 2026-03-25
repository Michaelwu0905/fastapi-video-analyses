<template>
  <div class="metrics-card">
    <div class="panel-header">
      <h3>多维传播力体系</h3>
      <span class="panel-note">保留原综合分用于对照</span>
    </div>

    <div class="overview-grid">
      <div class="overview-item">
        <span class="metric-label">综合得分</span>
        <span class="metric-value">{{ info.composite_score_formatted }}</span>
        <span class="metric-raw">({{ info.composite_score }})</span>
      </div>
      <div class="overview-item">
        <span class="metric-label">粘性度</span>
        <span class="metric-value">{{ info.stickiness_percent }}</span>
        <span class="metric-raw">({{ info.stickiness }})</span>
      </div>
    </div>

    <div class="dimension-list">
      <section class="dimension-card">
        <div class="dimension-header">
          <h4>传播广度</h4>
          <span>解决“看见了多少人”</span>
        </div>
        <div class="dimension-metrics">
          <div class="dimension-metric">
            <span class="dimension-label">播放量</span>
            <strong>{{ info.view_formatted }}</strong>
          </div>
          <div class="dimension-metric">
            <span class="dimension-label">单位天播放量</span>
            <strong>{{ info.daily_views_formatted }}</strong>
          </div>
          <div class="dimension-metric">
            <span class="dimension-label">分享率</span>
            <strong>{{ info.share_rate_percent }}</strong>
          </div>
        </div>
      </section>

      <section class="dimension-card">
        <div class="dimension-header">
          <h4>互动深度</h4>
          <span>衡量讨论和参与强度</span>
        </div>
        <div class="dimension-metrics">
          <div class="dimension-metric">
            <span class="dimension-label">评论率</span>
            <strong>{{ info.reply_rate_percent }}</strong>
          </div>
          <div class="dimension-metric">
            <span class="dimension-label">弹幕密度</span>
            <strong>{{ info.danmaku_density_formatted }}</strong>
          </div>
          <div class="dimension-metric">
            <span class="dimension-label">复合互动率</span>
            <strong>{{ info.composite_interaction_rate_percent }}</strong>
          </div>
        </div>
      </section>

      <section class="dimension-card">
        <div class="dimension-header">
          <h4>传播认同</h4>
          <span>衡量观众是否认可内容</span>
        </div>
        <div class="dimension-metrics">
          <div class="dimension-metric">
            <span class="dimension-label">点赞率</span>
            <strong>{{ info.like_rate_percent }}</strong>
          </div>
          <div class="dimension-metric">
            <span class="dimension-label">投币率</span>
            <strong>{{ info.coin_rate_percent }}</strong>
          </div>
          <div class="dimension-metric">
            <span class="dimension-label">收藏率</span>
            <strong>{{ info.favorite_rate_percent }}</strong>
          </div>
          <div class="dimension-metric wide">
            <span class="dimension-label">认同效率</span>
            <strong>{{ info.recognition_rate_percent }}</strong>
          </div>
        </div>
      </section>
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
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.metrics-card h3 { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.panel-note {
  font-size: 12px;
  color: var(--text-muted);
}
.overview-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.overview-item {
  background: linear-gradient(180deg, #f8fbff 0%, #f3f6f8 100%);
  padding: 16px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.metric-label { font-size: 12px; color: var(--text-muted); }
.metric-value { font-size: 24px; font-weight: 700; color: var(--primary-color); }
.metric-raw { font-size: 11px; color: var(--text-muted); }
.dimension-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}
.dimension-card {
  border: 1px solid #edf0f2;
  border-radius: 12px;
  padding: 16px;
  background: #fbfcfd;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.dimension-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.dimension-header h4 {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}
.dimension-header span {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
}
.dimension-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.dimension-metric {
  background: white;
  border: 1px solid #edf0f2;
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.dimension-metric.wide {
  grid-column: 1 / -1;
}
.dimension-label {
  font-size: 12px;
  color: var(--text-muted);
}
.dimension-metric strong {
  font-size: 18px;
  color: var(--primary-color);
}
@media (max-width: 640px) {
  .overview-grid,
  .dimension-list,
  .dimension-metrics { grid-template-columns: 1fr; }
}
</style>
