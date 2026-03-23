<template>
  <div class="content-analysis-panel">
    <div class="panel-header">
      <h3>视频内容分析</h3>
      <span v-if="analysis?.summary_mode" class="mode-badge">{{ analysis.summary_mode }}</span>
    </div>

    <div v-if="status?.msg" class="panel-state" :class="status.type">
      {{ status.msg }}
    </div>
    <div v-if="loading" class="panel-state">正在生成内容分析结果...</div>
    <div v-else-if="error" class="panel-state error">{{ error }}</div>
    <template v-else-if="analysis">
      <section class="panel-block">
        <span class="block-label">内容摘要</span>
        <p class="summary-text">{{ analysis.summary || '暂无摘要' }}</p>
      </section>

      <section v-if="analysis.tags?.length" class="panel-block">
        <span class="block-label">内容标签</span>
        <div class="tags-list">
          <span
            v-for="tag in analysis.tags"
            :key="tag"
            class="tag-chip"
          >
            {{ tag }}
          </span>
        </div>
      </section>

      <section v-if="analysis.highlights?.length" class="panel-block">
        <span class="block-label">关键片段</span>
        <ul class="highlights-list">
          <li v-for="(highlight, index) in analysis.highlights" :key="`${index}-${highlight}`">
            {{ highlight }}
          </li>
        </ul>
      </section>
    </template>
  </div>
</template>

<script setup>
defineProps({
  analysis: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null },
  status: { type: Object, default: null },
})
</script>

<style scoped>
.content-analysis-panel {
  background: var(--card-bg);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-subtle);
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.panel-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}
.mode-badge {
  font-size: 12px;
  color: var(--primary-color);
  background: #e1f5fe;
  padding: 4px 10px;
  border-radius: 999px;
}
.panel-state {
  padding: 14px 16px;
  border-radius: 8px;
  background: #f8f9fa;
  color: var(--text-secondary);
  font-size: 14px;
}
.panel-state.error {
  background: #fff1f1;
  color: #c92a2a;
}
.panel-state.info {
  background: #e7f5ff;
  color: #1971c2;
}
.panel-state.success {
  background: #d3f9d8;
  color: #2b8a3e;
}
.panel-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.block-label {
  font-size: 12px;
  color: var(--text-muted);
}
.summary-text {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
}
.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.tag-chip {
  font-size: 13px;
  color: var(--primary-color);
  background: #eef8fd;
  border: 1px solid #cdeffd;
  padding: 6px 12px;
  border-radius: 999px;
}
.highlights-list {
  padding-left: 18px;
  color: var(--text-secondary);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.highlights-list li {
  line-height: 1.6;
}
</style>
