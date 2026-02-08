<template>
  <div class="app-container">
    <!-- 头部 -->
    <header class="header">
      <h1>B站视频分析</h1>
      <p class="subtitle">输入视频链接获取数据详情</p>
    </header>

    <!-- 搜索区域 -->
    <div class="search-section">
      <div class="input-group">
        <input 
          type="text" 
          v-model="videoUrl" 
          placeholder="请输入B站视频链接 (BV...)"
          @keyup.enter="analyzeVideo"
          :disabled="loading"
        />
        <button 
          class="analyze-btn" 
          @click="analyzeVideo" 
          :disabled="loading || !videoUrl.trim()"
        >
          <span v-if="loading" class="spinner"></span>
          <span v-else>分析</span>
        </button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="error-msg">
      {{ errorMsg }}
    </div>

    <!-- 结果展示 -->
    <div v-if="videoInfo" class="result-layout">
      <!-- 视频基本信息展示 -->
      <div class="text-info-card">
        <div class="video-header">
          <div class="bvid-badge">{{ videoInfo.bvid }}</div>
          <h2 class="title">{{ videoInfo.title }}</h2>
        </div>
        
        <div class="video-meta">
          <div class="meta-item">
            <span class="meta-label">发布UP主</span>
            <span class="meta-value up-name">{{ videoInfo.author }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">发布时间</span>
            <span class="meta-value">{{ videoInfo.pubdate }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">视频时长</span>
            <span class="meta-value">{{ videoInfo.duration_formatted }}</span>
          </div>
        </div>

        <div class="description-box">
          <span class="meta-label">视频简介</span>
          <p class="description-text">{{ videoInfo.desc || '暂无简介' }}</p>
        </div>
      </div>

      <!-- 数据看板 -->
      <div class="stats-grid">
        <div class="stat-card">
          <span class="label">播放量</span>
          <span class="value">{{ videoInfo.view_formatted }}</span>
        </div>
        <div class="stat-card">
          <span class="label">弹幕</span>
          <span class="value">{{ videoInfo.danmaku_formatted }}</span>
        </div>
        <div class="stat-card">
          <span class="label">点赞</span>
          <span class="value">{{ videoInfo.like_formatted }}</span>
        </div>
        <div class="stat-card">
          <span class="label">投币</span>
          <span class="value">{{ videoInfo.coin_formatted }}</span>
        </div>
        <div class="stat-card">
          <span class="label">收藏</span>
          <span class="value">{{ videoInfo.favorite_formatted }}</span>
        </div>
        <div class="stat-card">
          <span class="label">分享</span>
          <span class="value">{{ videoInfo.share_formatted }}</span>
        </div>
      </div>

      <!-- 传播力指标 -->
      <div class="metrics-card">
        <h3>传播力指标</h3>
        <div class="metrics-grid">
          <div class="metric-item">
            <span class="metric-label">综合得分</span>
            <span class="metric-value">{{ videoInfo.composite_score_formatted }}</span>
            <span class="metric-raw">({{ videoInfo.composite_score }})</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">粘性度</span>
            <span class="metric-value">{{ videoInfo.stickiness_percent }}</span>
            <span class="metric-raw">({{ videoInfo.stickiness }})</span>
          </div>
        </div>
        <div class="metrics-formula">
          <p>综合得分 = 0.728*播放 + 0.154*弹幕 + 0.327*投币 + 0.242*收藏 - 0.192*点赞 - 0.157*分享</p>
          <p>粘性度 = (投币 + 收藏 + 分享) / 播放量</p>
        </div>
      </div>

      <!-- 评论操作区域 -->
      <div class="comments-section">
        <div class="comments-header">
          <h3>评论数据</h3>
          <span class="saved-count" v-if="videoInfo.saved_comments_count > 0">
            已保存 {{ videoInfo.saved_comments_count }} 条
          </span>
        </div>
        
        <div class="comments-actions">
          <button 
            class="action-btn fetch-btn" 
            @click="fetchComments"
            :disabled="fetchingComments"
          >
            <span v-if="fetchingComments" class="spinner"></span>
            <span v-else>爬取评论</span>
          </button>
          <button 
            class="action-btn view-btn" 
            @click="toggleCommentsList"
            :disabled="fetchingComments"
          >
            {{ showComments ? '收起列表' : '查看评论列表' }}
          </button>
        </div>

        <!-- 爬取状态提示 -->
        <div v-if="fetchStatus" class="fetch-status" :class="fetchStatus.type">
          {{ fetchStatus.msg }}
        </div>

        <!-- 评论列表 -->
        <div v-if="showComments" class="comments-list">
          <div v-if="loadingComments" class="loading-comments">
            加载中...
          </div>
          <div v-else-if="commentsList.length === 0" class="no-comments">
            暂无评论数据，请先点击"爬取评论"
          </div>
          <table v-else class="comments-table">
            <thead>
              <tr>
                <th class="col-index">序号</th>
                <th class="col-content">评论内容</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="comment in commentsList" :key="comment.index">
                <td class="col-index">{{ comment.index }}</td>
                <td class="col-content">{{ comment.content }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 页脚 -->
    <footer class="footer">
      Bilibili Video Analyzer - FastAPI & Vue
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const videoUrl = ref('https://www.bilibili.com/video/BV1GJ411x7h7')
const loading = ref(false)
const videoInfo = ref(null)
const errorMsg = ref(null)

// 评论相关状态
const fetchingComments = ref(false)
const fetchStatus = ref(null)
const showComments = ref(false)
const loadingComments = ref(false)
const commentsList = ref([])

const analyzeVideo = async () => {
  if (!videoUrl.value.trim()) return
  
  loading.value = true
  videoInfo.value = null
  errorMsg.value = null
  // 重置评论状态
  fetchStatus.value = null
  showComments.value = false
  commentsList.value = []

  try {
    const response = await axios.post('/api/analyze', {
      url: videoUrl.value
    })
    videoInfo.value = response.data
  } catch (err) {
    if (err.response && err.response.data) {
      errorMsg.value = err.response.data.detail
    } else {
      errorMsg.value = '无法连接到后端服务器'
    }
  } finally {
    loading.value = false
  }
}

const fetchComments = async () => {
  if (!videoInfo.value) return
  
  fetchingComments.value = true
  fetchStatus.value = { type: 'info', msg: '正在爬取评论，请稍候...' }

  try {
    const response = await axios.post('/api/fetch-comments', {
      bvid: videoInfo.value.bvid,
      aid: videoInfo.value.aid
    })
    fetchStatus.value = { type: 'success', msg: response.data.msg }
    // 更新已保存评论数
    videoInfo.value.saved_comments_count = response.data.saved_count
    // 自动加载评论列表
    await loadCommentsList()
    showComments.value = true
  } catch (err) {
    if (err.response && err.response.data) {
      fetchStatus.value = { type: 'error', msg: err.response.data.detail }
    } else {
      fetchStatus.value = { type: 'error', msg: '爬取评论失败' }
    }
  } finally {
    fetchingComments.value = false
  }
}

const loadCommentsList = async () => {
  if (!videoInfo.value) return
  
  loadingComments.value = true
  try {
    const response = await axios.get(`/api/comments/${videoInfo.value.bvid}`)
    commentsList.value = response.data.comments
  } catch (err) {
    console.error('加载评论失败:', err)
  } finally {
    loadingComments.value = false
  }
}

const toggleCommentsList = async () => {
  if (showComments.value) {
    showComments.value = false
  } else {
    showComments.value = true
    if (commentsList.value.length === 0) {
      await loadCommentsList()
    }
  }
}
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.header {
  text-align: center;
}

.header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 搜索区域 */
.search-section {
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
}

.input-group {
  display: flex;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 4px;
  transition: border-color 0.2s;
}

.input-group:focus-within {
  border-color: var(--primary-color);
}

.input-group input {
  flex: 1;
  border: none;
  padding: 12px 16px;
  font-size: 14px;
  outline: none;
  background: transparent;
}

.analyze-btn {
  background: var(--primary-color);
  color: white;
  border: none;
  padding: 0 24px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.analyze-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.analyze-btn:disabled {
  background: #ccd0d7;
  cursor: not-allowed;
}

/* 错误提示 */
.error-msg {
  text-align: center;
  color: #f85d5d;
  font-size: 14px;
  padding: 12px;
  background: #fff1f1;
  border-radius: 8px;
}

/* 结果布局 */
.result-layout {
  display: flex;
  flex-direction: column;
  gap: 20px;
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 纯文字信息卡片 */
.text-info-card {
  background: var(--card-bg);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-subtle);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.video-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bvid-badge {
  align-self: flex-start;
  font-size: 12px;
  font-weight: 500;
  color: var(--primary-color);
  background: #e1f5fe;
  padding: 2px 8px;
  border-radius: 4px;
}

.title {
  font-size: 20px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--text-primary);
}

.video-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  padding: 16px 0;
  border-top: 1px solid #f1f2f3;
  border-bottom: 1px solid #f1f2f3;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-label {
  font-size: 12px;
  color: var(--text-muted);
}

.meta-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.up-name {
  color: var(--accent-color);
}

.description-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.description-text {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
}

/* 数据网格 */
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

.stat-card .label {
  font-size: 12px;
  color: var(--text-muted);
}

.stat-card .value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 传播力指标 */
.metrics-card {
  background: var(--card-bg);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-subtle);
}

.metrics-card h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.metric-item {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.metric-label {
  font-size: 12px;
  color: var(--text-muted);
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--primary-color);
}

.metric-raw {
  font-size: 11px;
  color: var(--text-muted);
}

.metrics-formula {
  padding-top: 16px;
  border-top: 1px solid #f1f2f3;
}

.metrics-formula p {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.8;
}

/* 评论区域 */
.comments-section {
  background: var(--card-bg);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-subtle);
}

.comments-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.comments-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.saved-count {
  font-size: 12px;
  color: var(--primary-color);
  background: #e1f5fe;
  padding: 4px 10px;
  border-radius: 12px;
}

.comments-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.action-btn {
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.fetch-btn {
  background: #ff6b6b;
  color: white;
}

.fetch-btn:hover:not(:disabled) {
  background: #ee5a5a;
}

.view-btn {
  background: #f1f2f3;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.view-btn:hover:not(:disabled) {
  background: #e9eaeb;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.fetch-status {
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 16px;
}

.fetch-status.info {
  background: #e7f5ff;
  color: #1971c2;
}

.fetch-status.success {
  background: #d3f9d8;
  color: #2b8a3e;
}

.fetch-status.error {
  background: #fff1f1;
  color: #c92a2a;
}

.comments-list {
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.loading-comments,
.no-comments {
  text-align: center;
  color: var(--text-muted);
  padding: 24px;
  font-size: 14px;
}

.comments-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.comments-table th,
.comments-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #f1f2f3;
}

.comments-table th {
  background: #f6f7f8;
  font-weight: 600;
  color: var(--text-secondary);
  position: sticky;
  top: 0;
}

.comments-table tbody tr:hover {
  background: #fafbfc;
}

.col-index {
  width: 60px;
  text-align: center;
  color: var(--text-muted);
}

.col-content {
  color: var(--text-primary);
  line-height: 1.5;
}

/* 页脚 */
.footer {
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
  padding: 40px 0;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  .comments-actions {
    flex-direction: column;
  }
}
</style>
