<template>
  <div class="sentiment-panel">
    <div class="sentiment-header">
      <h4>情感分析（DistilBERT）</h4>
      <span class="status-badge" :class="{ processing: stats.pending > 0, done: stats.pending === 0 }">
        {{ stats.pending > 0 ? '分析中...' : '已完成' }}
      </span>
    </div>

    <!-- 进度条 -->
    <div class="progress-container">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${(stats.analyzed / stats.total) * 100}%` }"></div>
      </div>
      <span class="progress-text">{{ stats.analyzed }} / {{ stats.total }}</span>
    </div>

    <!-- 统计卡片 -->
    <div class="sentiment-stats">
      <div class="s-card positive">
        <span class="emoji">😊</span>
        <span class="label">正面</span>
        <span class="count">{{ stats.positive }}</span>
      </div>
      <div class="s-card neutral">
        <span class="emoji">😐</span>
        <span class="label">中性</span>
        <span class="count">{{ stats.neutral }}</span>
      </div>
      <div class="s-card negative">
        <span class="emoji">😠</span>
        <span class="label">负面</span>
        <span class="count">{{ stats.negative }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  stats: { type: Object, required: true },
})
</script>

<style scoped>
.sentiment-panel {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}
.sentiment-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.sentiment-header h4 { font-size: 14px; font-weight: 600; color: var(--text-primary); margin: 0; }
.status-badge { font-size: 12px; padding: 2px 8px; border-radius: 4px; background: #e9ecef; color: var(--text-secondary); }
.status-badge.processing { background: #e7f5ff; color: #1971c2; animation: pulse 2s infinite; }
.status-badge.done { background: #d3f9d8; color: #2b8a3e; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.6; } }
.progress-container { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.progress-bar { flex: 1; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--primary-color); transition: width 0.5s ease; }
.progress-text { font-size: 12px; color: var(--text-muted); width: 60px; text-align: right; }
.sentiment-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.s-card {
  background: white; padding: 12px; border-radius: 8px; border: 1px solid #e9ecef;
  display: flex; flex-direction: column; align-items: center; gap: 4px;
}
.s-card .emoji { font-size: 20px; }
.s-card .label { font-size: 12px; color: var(--text-muted); }
.s-card .count { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.s-card.positive { border-bottom: 3px solid #40c057; }
.s-card.neutral  { border-bottom: 3px solid #adb5bd; }
.s-card.negative { border-bottom: 3px solid #fa5252; }
</style>
