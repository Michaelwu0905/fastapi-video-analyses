<template>
  <div class="ahp-card">
    <div class="panel-header">
      <div>
        <h3>AHP + 熵权法综合评价</h3>
        <p class="panel-subtitle">理论判断与样本差异度结合后的传播力评价结果</p>
      </div>
      <span class="panel-badge">AHP + Entropy</span>
    </div>

    <div v-if="loading" class="panel-state">正在计算综合评价结果...</div>
    <div v-else-if="error" class="panel-state error">{{ error }}</div>
    <div v-else-if="!result" class="panel-state">暂无可用评价结果</div>
    <template v-else>
      <div class="score-overview">
        <div class="score-main">
          <span class="score-label">综合传播力得分</span>
          <div class="score-value">{{ result.total_score }}</div>
          <div class="score-meta">
            <span class="score-level">{{ result.level }}</span>
            <span>样本排名 {{ result.rank }}/{{ result.sample_size }}</span>
          </div>
        </div>
        <div class="score-side">
          <div class="side-item">
            <span class="side-label">AHP 占比</span>
            <strong>{{ (result.alpha * 100).toFixed(0) }}%</strong>
          </div>
          <div class="side-item">
            <span class="side-label">熵权占比</span>
            <strong>{{ ((1 - result.alpha) * 100).toFixed(0) }}%</strong>
          </div>
        </div>
      </div>

      <div class="dimension-grid">
        <div class="dimension-item">
          <span class="dimension-label">传播广度</span>
          <strong>{{ result.dimension_scores.breadth }}</strong>
          <div class="dimension-bar"><span :style="{ width: `${result.dimension_scores.breadth}%` }"></span></div>
        </div>
        <div class="dimension-item">
          <span class="dimension-label">互动深度</span>
          <strong>{{ result.dimension_scores.depth }}</strong>
          <div class="dimension-bar"><span :style="{ width: `${result.dimension_scores.depth}%` }"></span></div>
        </div>
        <div class="dimension-item">
          <span class="dimension-label">传播认同</span>
          <strong>{{ result.dimension_scores.recognition }}</strong>
          <div class="dimension-bar"><span :style="{ width: `${result.dimension_scores.recognition}%` }"></span></div>
        </div>
        <div class="dimension-item">
          <span class="dimension-label">知识传播效果</span>
          <strong>{{ result.dimension_scores.knowledge_effect }}</strong>
          <div class="dimension-bar"><span :style="{ width: `${result.dimension_scores.knowledge_effect}%` }"></span></div>
        </div>
      </div>

      <details class="details-panel">
        <summary>查看权重与贡献说明</summary>

        <section class="detail-block">
          <h4>一级维度权重</h4>
          <div class="criteria-grid">
            <div class="criteria-item">
              <span>传播广度</span>
              <strong>{{ result.criteria_weights.breadth }}</strong>
            </div>
            <div class="criteria-item">
              <span>互动深度</span>
              <strong>{{ result.criteria_weights.depth }}</strong>
            </div>
            <div class="criteria-item">
              <span>传播认同</span>
              <strong>{{ result.criteria_weights.recognition }}</strong>
            </div>
            <div class="criteria-item">
              <span>知识传播效果</span>
              <strong>{{ result.criteria_weights.knowledge_effect }}</strong>
            </div>
          </div>
        </section>

        <section class="detail-block">
          <h4>指标贡献 Top 6</h4>
          <div class="contribution-table">
            <div class="table-head">
              <span>指标</span>
              <span>组合权重</span>
              <span>贡献值</span>
            </div>
            <div
              v-for="row in topIndicators"
              :key="row.key"
              class="table-row"
            >
              <span>{{ row.name }}</span>
              <span>{{ row.combined_weight }}</span>
              <span>{{ row.contribution }}</span>
            </div>
          </div>
        </section>

        <p class="method-note">
          AHP 反映理论判断，熵权反映样本数据差异度；前端展示的是两者按固定比例组合后的结果。
        </p>
      </details>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null },
})

const topIndicators = computed(() => (props.result?.indicator_rows ?? []).slice(0, 6))
</script>

<style scoped>
.ahp-card {
  background: var(--card-bg);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-subtle);
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.panel-header h3 {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}
.panel-subtitle {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.6;
}
.panel-badge {
  font-size: 12px;
  color: #0f766e;
  background: #e6fffb;
  border: 1px solid #b2f5ea;
  padding: 4px 10px;
  border-radius: 999px;
  white-space: nowrap;
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
.score-overview {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
}
.score-main,
.score-side {
  border: 1px solid #edf0f2;
  border-radius: 12px;
  padding: 18px;
  background: #fbfcfd;
}
.score-main {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.score-label,
.side-label,
.dimension-label {
  font-size: 12px;
  color: var(--text-muted);
}
.score-value {
  font-size: 40px;
  line-height: 1;
  font-weight: 800;
  color: var(--primary-color);
}
.score-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 13px;
  color: var(--text-secondary);
}
.score-level {
  color: var(--accent-color);
  font-weight: 700;
}
.score-side {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
.side-item {
  background: white;
  border-radius: 10px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.side-item strong {
  font-size: 24px;
  color: var(--text-primary);
}
.dimension-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
.dimension-item {
  border: 1px solid #edf0f2;
  border-radius: 12px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.dimension-item strong {
  font-size: 24px;
  color: var(--text-primary);
}
.dimension-bar {
  height: 8px;
  background: #eef2f5;
  border-radius: 999px;
  overflow: hidden;
}
.dimension-bar span {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #00aeec 0%, #62d0ff 100%);
}
.details-panel {
  border-top: 1px solid #f1f2f3;
  padding-top: 16px;
}
.details-panel summary {
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.detail-block {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.detail-block h4 {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
}
.criteria-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.criteria-item {
  background: #fafbfd;
  border: 1px solid #edf0f2;
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.criteria-item span,
.table-row span,
.table-head span,
.method-note {
  font-size: 12px;
  color: var(--text-secondary);
}
.criteria-item strong {
  font-size: 18px;
  color: var(--primary-color);
}
.contribution-table {
  border: 1px solid #edf0f2;
  border-radius: 12px;
  overflow: hidden;
}
.table-head,
.table-row {
  display: grid;
  grid-template-columns: 1.6fr 1fr 1fr;
  gap: 12px;
  padding: 10px 12px;
}
.table-head {
  background: #f8fafb;
  font-weight: 700;
}
.table-row {
  border-top: 1px solid #edf0f2;
}
.method-note {
  margin-top: 14px;
  line-height: 1.7;
}
@media (max-width: 900px) {
  .score-overview,
  .dimension-grid,
  .criteria-grid {
    grid-template-columns: 1fr;
  }
}
</style>
