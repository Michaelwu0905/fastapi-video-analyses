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
      <!-- 视频基本信息展示 (纯文字版) -->
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

const analyzeVideo = async () => {
  if (!videoUrl.value.trim()) return
  
  loading.value = true
  videoInfo.value = null
  errorMsg.value = null

  try {
    const response = await axios.post('http://127.0.0.1:8000/api/analyze', {
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
  white-space: pre-wrap; /* 保留简介中的换行 */
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
}
</style>
