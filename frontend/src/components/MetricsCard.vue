<template>
  <div class="metrics-card">
    <div class="panel-header">
      <h3>传播力基础指标</h3>
      <span class="panel-note">作为 AHP 传播力评价的输入依据</span>
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

      <section class="dimension-card">
        <div class="dimension-header">
          <h4>知识传播效果</h4>
          <span>衡量评论区是否产生知识反馈</span>
        </div>
        <div v-if="knowledgeEffect" class="dimension-metrics">
          <div class="dimension-metric">
            <span class="dimension-label">认知反馈占比</span>
            <strong>{{ knowledgeEffect.cognitive_feedback_ratio_percent }}</strong>
          </div>
          <div class="dimension-metric">
            <span class="dimension-label">问题型评论占比</span>
            <strong>{{ knowledgeEffect.question_comment_ratio_percent }}</strong>
          </div>
          <div class="dimension-metric wide">
            <span class="dimension-label">情感极化度</span>
            <strong>{{ knowledgeEffect.sentiment_polarization_percent }}</strong>
          </div>
        </div>
        <div v-else class="dimension-placeholder">
          抓取评论并完成情感分析后，将在这里显示知识传播效果指标。
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
defineProps({
  info: { type: Object, required: true },
  knowledgeEffect: { type: Object, default: null },
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
.dimension-list {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
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
.dimension-placeholder {
  background: white;
  border: 1px dashed #d9e1e8;
  border-radius: 10px;
  padding: 14px;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.6;
}
@media (max-width: 1100px) {
  .dimension-list { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
  .dimension-list,
  .dimension-metrics { grid-template-columns: 1fr; }
}
</style>
