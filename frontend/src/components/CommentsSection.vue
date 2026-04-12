<template>
  <div class="comments-section">
    <div class="comments-header">
      <h3>评论数据</h3>
      <span class="saved-count" v-if="savedCount > 0">已保存 {{ savedCount }} 条</span>
    </div>

    <div class="comments-actions">
      <label class="max-comments-control">
        <span>最大抓取数</span>
        <input
          :value="maxComments"
          type="number"
          min="20"
          max="5000"
          step="20"
          :disabled="fetchingComments"
          @input="$emit('update:maxComments', Number($event.target.value))"
        />
      </label>
      <button class="action-btn fetch-btn" @click="$emit('fetch')" :disabled="fetchingComments">
        <span v-if="fetchingComments" class="spinner"></span>
        <span v-else>爬取评论</span>
      </button>
      <button class="action-btn view-btn" @click="$emit('toggle')" :disabled="fetchingComments">
        {{ showComments ? '收起列表' : '查看评论列表' }}
      </button>
    </div>

    <!-- 爬取状态提示 -->
    <div v-if="fetchStatus" class="fetch-status" :class="fetchStatus.type">
      {{ fetchStatus.msg }}
    </div>

    <!-- 情感分析面板 -->
    <SentimentPanel v-if="sentimentStats" :stats="sentimentStats" />
    <KnowledgeEffectPanel v-if="knowledgeEffect" :effect="knowledgeEffect" />

    <!-- 评论列表 -->
    <CommentsList v-if="showComments" :comments="commentsList" :loading="loadingComments" />
  </div>
</template>

<script setup>
import SentimentPanel from './SentimentPanel.vue'
import KnowledgeEffectPanel from './KnowledgeEffectPanel.vue'
import CommentsList from './CommentsList.vue'

defineProps({
  savedCount:        { type: Number, default: 0 },
  maxComments:       { type: Number, default: 200 },
  fetchingComments:  { type: Boolean, default: false },
  fetchStatus:       { type: Object, default: null },
  showComments:      { type: Boolean, default: false },
  loadingComments:   { type: Boolean, default: false },
  commentsList:      { type: Array, default: () => [] },
  sentimentStats:    { type: Object, default: null },
  knowledgeEffect:   { type: Object, default: null },
})
defineEmits(['fetch', 'toggle', 'update:maxComments'])
</script>

<style scoped>
.comments-section {
  background: var(--card-bg);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-subtle);
}
.comments-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.comments-header h3 { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.saved-count { font-size: 12px; color: var(--primary-color); background: #e1f5fe; padding: 4px 10px; border-radius: 12px; }
.comments-actions { display: flex; gap: 12px; margin-bottom: 16px; align-items: flex-end; flex-wrap: wrap; }
.max-comments-control {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 130px;
  font-size: 12px;
  color: var(--text-secondary);
}
.max-comments-control input {
  height: 38px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 0 10px;
  font-size: 14px;
  color: var(--text-primary);
  background: white;
}
.max-comments-control input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.action-btn { padding: 10px 20px; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s; border: none; }
.fetch-btn { background: #ff6b6b; color: white; }
.fetch-btn:hover:not(:disabled) { background: #ee5a5a; }
.view-btn { background: #f1f2f3; color: var(--text-secondary); border: 1px solid var(--border-color); }
.view-btn:hover:not(:disabled) { background: #e9eaeb; }
.action-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.fetch-status { padding: 12px; border-radius: 8px; font-size: 14px; margin-bottom: 16px; }
.fetch-status.info    { background: #e7f5ff; color: #1971c2; }
.fetch-status.success { background: #d3f9d8; color: #2b8a3e; }
.fetch-status.error   { background: #fff1f1; color: #c92a2a; }
.spinner {
  display: inline-block; width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3); border-radius: 50%;
  border-top-color: white; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 640px) {
  .comments-actions { flex-direction: column; align-items: stretch; }
  .max-comments-control { width: 100%; }
}
</style>
