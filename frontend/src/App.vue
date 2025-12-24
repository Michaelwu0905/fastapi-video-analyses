<template>
  <div class="app-container">
    <!-- 头部 -->
    <header class="header">
      <div class="logo">
        <span class="logo-icon">📺</span>
        <h1>B站视频分析系统</h1>
      </div>
      <p class="subtitle">输入B站视频链接，获取视频详细信息</p>
    </header>

    <!-- 搜索区域 -->
    <div class="search-box">
      <div class="input-wrapper">
        <span class="input-icon">🔗</span>
        <input 
          type="text" 
          v-model="videoUrl" 
          placeholder="请输入B站视频链接 (例如 https://www.bilibili.com/video/BV...)"
          @keyup.enter="analyzeVideo"
          :disabled="loading"
        />
      </div>
      <button 
        class="analyze-btn" 
        @click="analyzeVideo" 
        :disabled="loading || !videoUrl.trim()"
      >
        <span v-if="loading" class="loading-spinner"></span>
        <span v-else>🔍 分析视频</span>
      </button>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="error-card">
      <span class="error-icon">❌</span>
      <div class="error-content">
        <h3>分析失败</h3>
        <p>{{ errorMsg }}</p>
      </div>
    </div>

    <!-- 结果展示 -->
    <div v-if="videoInfo" class="result-container">
      <!-- 成功提示 -->
      <div class="success-banner">
        <span class="success-icon">✅</span>
        <span>{{ videoInfo.msg }}</span>
      </div>

      <!-- 视频卡片 -->
      <div class="video-card">
        <!-- 封面 -->
        <div class="cover-section">
          <img :src="videoInfo.cover" :alt="videoInfo.title" class="cover-img" />
          <div class="duration-badge">{{ videoInfo.duration_formatted }}</div>
        </div>

        <!-- 视频信息 -->
        <div class="info-section">
          <h2 class="video-title">{{ videoInfo.title }}</h2>
          
          <div class="author-row">
            <img :src="videoInfo.author_face" class="author-avatar" />
            <span class="author-name">{{ videoInfo.author }}</span>
            <span class="bvid">{{ videoInfo.bvid }}</span>
          </div>

          <p class="video-desc">{{ videoInfo.desc || '暂无简介' }}</p>

          <div class="publish-time">
            <span>📅 发布时间：{{ videoInfo.pubdate }}</span>
          </div>
        </div>
      </div>

      <!-- 数据统计 -->
      <div class="stats-grid">
        <div class="stat-item play">
          <span class="stat-icon">▶️</span>
          <span class="stat-value">{{ videoInfo.view_formatted }}</span>
          <span class="stat-label">播放</span>
        </div>
        <div class="stat-item danmaku">
          <span class="stat-icon">💬</span>
          <span class="stat-value">{{ videoInfo.danmaku_formatted }}</span>
          <span class="stat-label">弹幕</span>
        </div>
        <div class="stat-item like">
          <span class="stat-icon">👍</span>
          <span class="stat-value">{{ videoInfo.like_formatted }}</span>
          <span class="stat-label">点赞</span>
        </div>
        <div class="stat-item coin">
          <span class="stat-icon">🪙</span>
          <span class="stat-value">{{ videoInfo.coin_formatted }}</span>
          <span class="stat-label">投币</span>
        </div>
        <div class="stat-item favorite">
          <span class="stat-icon">⭐</span>
          <span class="stat-value">{{ videoInfo.favorite_formatted }}</span>
          <span class="stat-label">收藏</span>
        </div>
        <div class="stat-item share">
          <span class="stat-icon">🔗</span>
          <span class="stat-value">{{ videoInfo.share_formatted }}</span>
          <span class="stat-label">分享</span>
        </div>
        <div class="stat-item reply">
          <span class="stat-icon">💭</span>
          <span class="stat-value">{{ videoInfo.reply_formatted }}</span>
          <span class="stat-label">评论</span>
        </div>
      </div>
    </div>

    <!-- 页脚 -->
    <footer class="footer">
      <p>B站视频分析系统 · FastAPI + Vue 3</p>
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
    console.error('分析失败:', err)
    if (err.response && err.response.data) {
      errorMsg.value = err.response.data.detail
    } else {
      errorMsg.value = '无法连接到后端服务器，请确保FastAPI已启动 (端口8000)'
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
  gap: 24px;
}

/* 头部样式 */
.header {
  text-align: center;
  padding: 20px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 8px;
}

.logo-icon {
  font-size: 42px;
  animation: bounce 2s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.header h1 {
  font-size: 2.2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #fff 0%, #ffd9e5 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 2px 10px rgba(255, 255, 255, 0.2);
}

.subtitle {
  color: rgba(255, 255, 255, 0.85);
  font-size: 1rem;
  margin-top: 4px;
}

/* 搜索框 */
.search-box {
  display: flex;
  gap: 12px;
  padding: 24px;
  background: var(--card-bg);
  border-radius: 20px;
  box-shadow: 0 10px 40px var(--shadow-color);
  backdrop-filter: blur(10px);
}

.input-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 16px;
  font-size: 1.2rem;
}

.input-wrapper input {
  width: 100%;
  padding: 16px 16px 16px 48px;
  font-size: 1rem;
  border: 2px solid #eee;
  border-radius: 12px;
  outline: none;
  transition: all 0.3s ease;
  font-family: inherit;
}

.input-wrapper input:focus {
  border-color: var(--bilibili-pink);
  box-shadow: 0 0 0 4px rgba(251, 114, 153, 0.1);
}

.input-wrapper input::placeholder {
  color: var(--text-muted);
}

.analyze-btn {
  padding: 16px 32px;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, var(--bilibili-pink), #ff8fab);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  font-family: inherit;
}

.analyze-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(251, 114, 153, 0.4);
}

.analyze-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 错误卡片 */
.error-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #fff5f5, #ffe3e3);
  border: 1px solid #ffc9c9;
  border-radius: 16px;
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-5px); }
  40%, 80% { transform: translateX(5px); }
}

.error-icon {
  font-size: 1.5rem;
}

.error-content h3 {
  color: #c92a2a;
  font-size: 1.1rem;
  margin-bottom: 4px;
}

.error-content p {
  color: #e03131;
  font-size: 0.95rem;
}

/* 成功提示 */
.success-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px;
  background: linear-gradient(135deg, #d3f9d8, #b2f2bb);
  border-radius: 12px;
  color: #2b8a3e;
  font-weight: 600;
  font-size: 1.05rem;
  animation: slideDown 0.4s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.success-icon {
  font-size: 1.3rem;
}

/* 结果容器 */
.result-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 视频卡片 */
.video-card {
  display: flex;
  gap: 24px;
  padding: 24px;
  background: var(--card-bg);
  border-radius: 20px;
  box-shadow: 0 10px 40px var(--shadow-color);
  overflow: hidden;
}

.cover-section {
  position: relative;
  flex-shrink: 0;
}

.cover-img {
  width: 320px;
  height: 200px;
  object-fit: cover;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.duration-badge {
  position: absolute;
  bottom: 12px;
  right: 12px;
  padding: 4px 10px;
  background: rgba(0, 0, 0, 0.75);
  color: white;
  font-size: 0.85rem;
  font-weight: 500;
  border-radius: 6px;
}

.info-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.video-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.author-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.author-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--bilibili-pink);
}

.author-name {
  font-weight: 600;
  color: var(--bilibili-pink);
  font-size: 1rem;
}

.bvid {
  padding: 4px 10px;
  background: linear-gradient(135deg, #f3f0ff, #e5dbff);
  color: #7950f2;
  font-size: 0.8rem;
  font-weight: 500;
  border-radius: 20px;
}

.video-desc {
  color: var(--text-secondary);
  font-size: 0.95rem;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.publish-time {
  color: var(--text-muted);
  font-size: 0.9rem;
}

/* 数据统计网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 20px 16px;
  background: var(--card-bg);
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  font-size: 1.5rem;
}

.stat-value {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 0.85rem;
  color: var(--text-muted);
}

/* 不同统计项的悬停效果 */
.stat-item.play:hover { background: linear-gradient(135deg, #fff5f5, #ffe3e3); }
.stat-item.danmaku:hover { background: linear-gradient(135deg, #e7f5ff, #d0ebff); }
.stat-item.like:hover { background: linear-gradient(135deg, #fff9db, #ffec99); }
.stat-item.coin:hover { background: linear-gradient(135deg, #fff4e6, #ffe8cc); }
.stat-item.favorite:hover { background: linear-gradient(135deg, #fff3bf, #ffe066); }
.stat-item.share:hover { background: linear-gradient(135deg, #d3f9d8, #b2f2bb); }
.stat-item.reply:hover { background: linear-gradient(135deg, #e5dbff, #d0bfff); }

/* 页脚 */
.footer {
  text-align: center;
  padding: 20px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-box {
    flex-direction: column;
  }
  
  .video-card {
    flex-direction: column;
  }
  
  .cover-img {
    width: 100%;
    height: auto;
    aspect-ratio: 16/10;
  }
  
  .header h1 {
    font-size: 1.6rem;
  }
  
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>

