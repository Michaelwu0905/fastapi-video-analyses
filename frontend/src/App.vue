<template>
  <div class="app-container">
    <!-- 头部 -->
    <header class="header">
      <h1>B站视频分析</h1>
      <p class="subtitle">输入视频链接获取数据详情</p>
    </header>

    <!-- 搜索区域 -->
    <SearchBar
      v-model="videoUrl"
      :loading="loading"
      @search="handleAnalyze"
    />

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

    <!-- 结果展示 -->
    <div v-if="videoInfo" class="result-layout">
      <VideoInfoCard :info="videoInfo" />
      <StatsGrid :info="videoInfo" />
      <MetricsCard :info="videoInfo" />
      <ContentAnalysisPanel
        :analysis="contentAnalysis"
        :loading="contentAnalysisLoading"
        :error="contentAnalysisError"
        :status="contentAnalysisStatus"
      />
      <CommentsSection
        :saved-count="videoInfo.saved_comments_count"
        :fetching-comments="fetchingComments"
        :fetch-status="fetchStatus"
        :show-comments="showComments"
        :loading-comments="loadingComments"
        :comments-list="commentsList"
        :sentiment-stats="sentimentStats"
        @fetch="handleFetch"
        @toggle="handleToggle"
      />
    </div>

    <!-- 页脚 -->
    <footer class="footer">Bilibili Video Analyzer - FastAPI &amp; Vue</footer>
  </div>
</template>

<script setup>
import SearchBar       from './components/SearchBar.vue'
import VideoInfoCard   from './components/VideoInfoCard.vue'
import StatsGrid       from './components/StatsGrid.vue'
import MetricsCard     from './components/MetricsCard.vue'
import ContentAnalysisPanel from './components/ContentAnalysisPanel.vue'
import CommentsSection from './components/CommentsSection.vue'

import { useVideoAnalysis } from './composables/useVideoAnalysis.js'
import { useComments }      from './composables/useComments.js'
import { useSentiment }     from './composables/useSentiment.js'

// ── composables ──────────────────────────────────────────────
const {
  videoUrl, loading, videoInfo,
  contentAnalysis, contentAnalysisLoading, contentAnalysisError, contentAnalysisStatus,
  errorMsg, analyzeVideo,
} = useVideoAnalysis()

const {
  sentimentStats, reset: resetSentiment,
  buildCheckFn, startSentimentPolling, stopSentimentPolling,
} = useSentiment()

const {
  fetchingComments, fetchStatus, showComments, loadingComments, commentsList,
  reset: resetComments, loadCommentsList, fetchComments, toggleCommentsList,
} = useComments()

// ── 情感分析轮询 setup ────────────────────────────────────────
const checkSentiment = buildCheckFn({
  getBvid: () => videoInfo.value?.bvid,
  onFinished: () => loadCommentsList({
    bvid: videoInfo.value?.bvid,
    onStatsLoaded: (s) => { sentimentStats.value = s },
  }),
})

// ── 事件处理 ─────────────────────────────────────────────────
const handleAnalyze = () => analyzeVideo({
  onReset: () => { resetComments(); resetSentiment() },
  onHasComments: () => checkSentiment(),
})

const handleFetch = () => fetchComments({
  videoInfo: videoInfo.value,
  onStatsLoaded: (s) => { sentimentStats.value = s },
  onStartPolling: () => startSentimentPolling(checkSentiment),
  onResetSentiment: resetSentiment,
})

const handleToggle = () => toggleCommentsList({
  bvid: videoInfo.value?.bvid,
  onStatsLoaded: (s) => { sentimentStats.value = s },
})
</script>

<style scoped>
.app-container { display: flex; flex-direction: column; gap: 32px; }
.header { text-align: center; }
.header h1 { font-size: 24px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
.subtitle { font-size: 14px; color: var(--text-secondary); }
.error-msg { text-align: center; color: #f85d5d; font-size: 14px; padding: 12px; background: #fff1f1; border-radius: 8px; }
.result-layout { display: flex; flex-direction: column; gap: 20px; animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.footer { text-align: center; font-size: 12px; color: var(--text-muted); padding: 40px 0; }
</style>
