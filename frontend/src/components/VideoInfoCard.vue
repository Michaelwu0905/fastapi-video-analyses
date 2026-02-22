<template>
  <div class="text-info-card">
    <div class="video-header">
      <div class="bvid-badge">{{ info.bvid }}</div>
      <h2 class="title">{{ info.title }}</h2>
    </div>

    <div class="video-meta">
      <div class="meta-item">
        <span class="meta-label">发布UP主</span>
        <span class="meta-value up-name">{{ info.author }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">发布时间</span>
        <span class="meta-value">{{ info.pubdate }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">视频时长</span>
        <span class="meta-value">{{ info.duration_formatted }}</span>
      </div>
    </div>

    <div class="description-box">
      <span class="meta-label">视频简介</span>
      <p class="description-text">{{ info.desc || '暂无简介' }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  info: { type: Object, required: true },
})
</script>

<style scoped>
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
.video-header { display: flex; flex-direction: column; gap: 8px; }
.bvid-badge {
  align-self: flex-start;
  font-size: 12px;
  font-weight: 500;
  color: var(--primary-color);
  background: #e1f5fe;
  padding: 2px 8px;
  border-radius: 4px;
}
.title { font-size: 20px; font-weight: 600; line-height: 1.4; color: var(--text-primary); }
.video-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  padding: 16px 0;
  border-top: 1px solid #f1f2f3;
  border-bottom: 1px solid #f1f2f3;
}
.meta-item { display: flex; flex-direction: column; gap: 4px; }
.meta-label { font-size: 12px; color: var(--text-muted); }
.meta-value { font-size: 14px; font-weight: 500; color: var(--text-secondary); }
.up-name { color: var(--accent-color); }
.description-box { display: flex; flex-direction: column; gap: 8px; }
.description-text { font-size: 14px; color: var(--text-secondary); line-height: 1.6; white-space: pre-wrap; }
</style>
