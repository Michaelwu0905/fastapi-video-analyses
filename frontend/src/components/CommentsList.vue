<template>
  <div class="comments-list">
    <div v-if="loading" class="loading-comments">加载中...</div>
    <div v-else-if="comments.length === 0" class="no-comments">
      暂无评论数据，请先点击"爬取评论"
    </div>
    <table v-else class="comments-table">
      <thead>
        <tr>
          <th class="col-index">序号</th>
          <th class="col-sentiment">情感</th>
          <th class="col-content">评论内容</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="comment in comments" :key="comment.index">
          <td class="col-index">{{ comment.index }}</td>
          <td class="col-sentiment">
            <span v-if="comment.sentiment" :class="['sentiment-tag', comment.sentiment]">
              {{ labelMap[comment.sentiment] ?? comment.sentiment }}
            </span>
            <span v-else class="sentiment-tag pending">...</span>
          </td>
          <td class="col-content">{{ comment.content }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  comments: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const labelMap = { positive: '正面', neutral: '中性', negative: '负面' }
</script>

<style scoped>
.comments-list { margin-top: 16px; max-height: 400px; overflow-y: auto; }
.loading-comments, .no-comments { text-align: center; color: var(--text-muted); padding: 24px; font-size: 14px; }
.comments-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.comments-table th, .comments-table td { padding: 12px; text-align: left; border-bottom: 1px solid #f1f2f3; }
.comments-table th { background: #f6f7f8; font-weight: 600; color: var(--text-secondary); position: sticky; top: 0; }
.comments-table tbody tr:hover { background: #fafbfc; }
.col-index { width: 60px; text-align: center; color: var(--text-muted); }
.col-sentiment { width: 80px; }
.col-content { color: var(--text-primary); line-height: 1.5; }
.sentiment-tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }
.sentiment-tag.positive { background: #d3f9d8; color: #2b8a3e; }
.sentiment-tag.neutral  { background: #f1f3f5; color: #495057; }
.sentiment-tag.negative { background: #ffe3e3; color: #c92a2a; }
.sentiment-tag.pending  { color: #adb5bd; }
</style>
