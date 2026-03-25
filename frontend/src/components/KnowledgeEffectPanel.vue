<template>
  <div class="knowledge-panel">
    <div class="panel-header">
      <h4>知识传播效果</h4>
      <span class="panel-note">规则版第一版</span>
    </div>

    <div class="knowledge-grid">
      <div class="knowledge-item">
        <span class="knowledge-label">认知反馈占比</span>
        <strong>{{ effect.cognitive_feedback_ratio_percent }}</strong>
        <small>{{ effect.cognitive_feedback_count }} 条评论提到“学到了/看懂了”等反馈</small>
      </div>

      <div class="knowledge-item">
        <span class="knowledge-label">问题型评论占比</span>
        <strong>{{ effect.question_comment_ratio_percent }}</strong>
        <small>{{ effect.question_comment_count }} 条评论包含提问或求解释表达</small>
      </div>

      <div class="knowledge-item">
        <span class="knowledge-label">情感极化度</span>
        <strong>{{ effect.sentiment_polarization_percent }}</strong>
        <small>按正向评论与负向评论占比衡量态度分化</small>
      </div>

      <div class="knowledge-item">
        <span class="knowledge-label">争议度</span>
        <strong>{{ effect.controversy_score_percent }}</strong>
        <small>正负评论越接近平衡，争议度越高</small>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  effect: { type: Object, required: true },
})
</script>

<style scoped>
.knowledge-panel {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f1f2f3;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.panel-header h4 {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}
.panel-note {
  font-size: 12px;
  color: var(--text-muted);
}
.knowledge-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.knowledge-item {
  background: #fafbfd;
  border: 1px solid #edf0f2;
  border-radius: 10px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.knowledge-label {
  font-size: 12px;
  color: var(--text-muted);
}
.knowledge-item strong {
  font-size: 20px;
  color: var(--primary-color);
}
.knowledge-item small {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}
@media (max-width: 640px) {
  .knowledge-grid {
    grid-template-columns: 1fr;
  }
}
</style>
