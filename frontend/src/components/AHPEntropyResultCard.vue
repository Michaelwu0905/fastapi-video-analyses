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

      <details class="details-panel formula-panel">
        <summary>查看文本计算明细</summary>

        <section class="detail-block">
          <h4>1. 原始指标</h4>
          <div
            v-for="group in formulaGroups"
            :key="`raw-${group.key}`"
            class="formula-group"
          >
            <h5>{{ group.label }}</h5>
            <div class="formula-list">
              <div
                v-for="item in rawMetricsByGroup[group.key] || []"
                :key="`raw-${item.key}`"
                class="formula-line"
              >
                <span class="formula-name">{{ item.name }}</span>
                <code>{{ item.value }}</code>
              </div>
            </div>
          </div>
        </section>

        <section class="detail-block">
          <h4>2. 标准化过程</h4>
          <div
            v-for="group in formulaGroups"
            :key="`normalized-${group.key}`"
            class="formula-group"
          >
            <h5>{{ group.label }}</h5>
            <div class="formula-list">
              <div
                v-for="item in normalizedMetricsByGroup[group.key] || []"
                :key="`normalized-${item.key}`"
                class="formula-text-block"
              >
                <span class="formula-name">{{ item.name }}</span>
                <code>{{ item.formula_text }}</code>
              </div>
            </div>
          </div>
        </section>

        <section class="detail-block">
          <h4>3. 组合权重过程</h4>
          <div
            v-for="group in formulaGroups"
            :key="`weight-${group.key}`"
            class="formula-group"
          >
            <h5>{{ group.label }}</h5>
            <div class="formula-list">
              <div
                v-for="item in weightMetricsByGroup[group.key] || []"
                :key="`weight-${item.key}`"
                class="formula-text-block"
              >
                <span class="formula-name">{{ item.name }}</span>
                <code>{{ item.formula_text }}</code>
              </div>
            </div>
          </div>
        </section>

        <section class="detail-block">
          <h4>4. 维度得分过程</h4>
          <div
            v-for="dimension in dimensionFormulas"
            :key="dimension.key"
            class="formula-group"
          >
            <h5>{{ dimension.name }}</h5>
            <div class="formula-list">
              <div
                v-for="item in dimension.items"
                :key="`dim-${dimension.key}-${item.key}`"
                class="formula-line"
              >
                <span class="formula-name">{{ item.name }}</span>
                <code>
                  标准化值 {{ item.normalized_value }} × 维度内权重 {{ item.dimension_weight }}
                </code>
              </div>
            </div>
            <div class="formula-result">
              <code>{{ dimension.formula_text }}</code>
            </div>
          </div>
        </section>

        <section class="detail-block">
          <h4>5. 最终总分过程</h4>
          <div class="formula-list">
            <div
              v-for="term in totalFormulaTerms"
              :key="`total-${term.key}`"
              class="formula-line"
            >
              <span class="formula-name">{{ term.name }}</span>
              <code>
                {{ term.normalized_value }} × {{ term.combined_weight }} × 100 = {{ term.contribution }}
              </code>
            </div>
          </div>
          <div class="formula-result">
            <code>{{ totalFormula.formula_text }}</code>
          </div>
        </section>
      </details>

      <details v-if="latexView" class="details-panel latex-panel">
        <summary>查看 LaTeX 数学推导过程</summary>

        <section class="detail-block">
          <h4>1. 指标定义</h4>
          <div class="symbol-note-grid">
            <div
              v-for="note in latexView.symbol_notes"
              :key="`symbol-${note.symbol}`"
              class="symbol-note"
            >
              <strong>{{ note.symbol }}</strong>
              <span>{{ note.label }}</span>
              <small>{{ note.description }}</small>
              <em v-if="note.value_label">当前值：{{ note.value_label }}</em>
              <em v-else-if="note.value_note">{{ note.value_note }}</em>
            </div>
          </div>
          <div class="latex-grid">
            <div
              v-for="item in latexView.metric_definitions"
              :key="`latex-metric-${item.key}`"
              class="latex-item"
            >
              <span>{{ item.name }}</span>
              <LatexFormula :formula="item.formula" />
            </div>
          </div>
        </section>

        <section class="detail-block">
          <h4>2. AHP 判断矩阵与一致性检验</h4>
          <div class="latex-step">
            <span>一级维度判断矩阵</span>
            <LatexFormula :formula="latexView.ahp.criteria_matrix" />
            <LatexFormula :formula="latexView.ahp.criteria_weight_vector" />
            <LatexFormula :formula="latexView.ahp.criteria_consistency" />
          </div>

          <div
            v-for="matrix in latexView.ahp.indicator_matrices"
            :key="`latex-ahp-${matrix.key}`"
            class="latex-step"
          >
            <span>{{ matrix.name }}二级指标判断矩阵</span>
            <LatexFormula :formula="matrix.matrix" />
            <LatexFormula :formula="matrix.local_weight_vector" />
            <LatexFormula :formula="matrix.consistency" />
          </div>
        </section>

        <section class="detail-block">
          <h4>3. 熵权法标准化与客观权重</h4>
          <div class="latex-step">
            <span>熵权法通用公式</span>
            <LatexFormula :formula="latexView.entropy.standardization_formula" />
            <LatexFormula :formula="latexView.entropy.proportion_formula" />
            <LatexFormula :formula="latexView.entropy.entropy_formula" />
            <LatexFormula :formula="latexView.entropy.divergence_formula" />
            <LatexFormula :formula="latexView.entropy.weight_formula" />
          </div>

          <div class="latex-two-col">
            <div
              v-for="row in latexView.entropy.normalization_rows"
              :key="`latex-norm-${row.key}`"
              class="latex-item"
            >
              <span>{{ row.name }}标准化</span>
              <LatexFormula :formula="row.formula" />
            </div>
          </div>

          <div class="latex-two-col">
            <div
              v-for="row in latexView.entropy.weight_rows"
              :key="`latex-ew-${row.key}`"
              class="latex-item"
            >
              <span>{{ row.name }}熵权</span>
              <LatexFormula :formula="row.formula" />
            </div>
          </div>
        </section>

        <section class="detail-block">
          <h4>4. AHP + 熵权法组合权重</h4>
          <LatexFormula :formula="latexView.combined_weights.formula" />
          <div class="latex-two-col">
            <div
              v-for="row in latexView.combined_weights.rows"
              :key="`latex-combined-${row.key}`"
              class="latex-item"
            >
              <span>{{ row.name }}</span>
              <LatexFormula :formula="row.formula" />
            </div>
          </div>
        </section>

        <section class="detail-block">
          <h4>5. 四个一级维度得分</h4>
          <div class="latex-two-col">
            <div
              v-for="row in latexView.dimension_scores"
              :key="`latex-dimension-${row.key}`"
              class="latex-item"
            >
              <span>{{ row.name }}</span>
              <LatexFormula :formula="row.formula" />
            </div>
          </div>
        </section>

        <section class="detail-block">
          <h4>6. 最终综合传播力得分</h4>
          <LatexFormula :formula="latexView.total_score.formula" />
          <div class="latex-two-col">
            <div
              v-for="row in latexView.total_score.contribution_rows"
              :key="`latex-total-${row.key}`"
              class="latex-item"
            >
              <span>{{ row.name }}贡献值</span>
              <LatexFormula :formula="row.formula" />
            </div>
          </div>
        </section>
      </details>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import LatexFormula from './LatexFormula.vue'

const props = defineProps({
  result: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null },
})

const formulaGroups = [
  { key: 'breadth', label: '传播广度' },
  { key: 'depth', label: '互动深度' },
  { key: 'recognition', label: '传播认同' },
  { key: 'knowledge_effect', label: '知识传播效果' },
]

const topIndicators = computed(() => (props.result?.indicator_rows ?? []).slice(0, 6))
const rawMetricsByGroup = computed(() => props.result?.formula_view?.raw_metrics ?? {})
const normalizedMetricsByGroup = computed(() => props.result?.formula_view?.normalized_metrics ?? {})
const weightMetricsByGroup = computed(() => props.result?.formula_view?.weight_metrics ?? {})
const dimensionFormulas = computed(() => props.result?.formula_view?.dimension_formulas ?? [])
const totalFormula = computed(() => props.result?.formula_view?.total_formula ?? { formula_text: '', terms: [] })
const totalFormulaTerms = computed(() => totalFormula.value.terms ?? [])
const latexView = computed(() => props.result?.formula_view?.latex_view ?? null)
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
.formula-panel {
  margin-top: -4px;
}
.latex-panel {
  margin-top: -4px;
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
.formula-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border: 1px solid #edf0f2;
  border-radius: 12px;
  background: #fbfcfd;
}
.formula-group h5 {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
}
.formula-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.formula-line,
.formula-text-block {
  display: grid;
  grid-template-columns: 140px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
}
.formula-name {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
}
.formula-line code,
.formula-text-block code,
.formula-result code {
  display: block;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 12px;
  line-height: 1.7;
  color: #14532d;
  background: #f4fbf6;
  border: 1px solid #d8f3dc;
  border-radius: 8px;
  padding: 8px 10px;
  white-space: pre-wrap;
  word-break: break-word;
}
.formula-result {
  margin-top: 2px;
}
.latex-grid,
.latex-two-col {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.latex-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.latex-step,
.latex-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border: 1px solid #edf0f2;
  border-radius: 12px;
  background: #fbfcfd;
}
.latex-step > span,
.latex-item > span {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
}
.symbol-note-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.symbol-note {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 4px 8px;
  align-items: baseline;
  padding: 10px 12px;
  border: 1px solid #edf0f2;
  border-radius: 10px;
  background: #fff;
}
.symbol-note strong {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 13px;
  color: var(--primary-color);
}
.symbol-note span {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary);
}
.symbol-note small {
  grid-column: 1 / -1;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.5;
}
.symbol-note em {
  grid-column: 1 / -1;
  font-style: normal;
  color: #0f766e;
  font-size: 11px;
  line-height: 1.5;
  background: #e6fffb;
  border-radius: 6px;
  padding: 5px 7px;
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
  .formula-line,
  .formula-text-block,
  .latex-grid,
  .latex-two-col,
  .symbol-note-grid {
    grid-template-columns: 1fr;
  }
}
</style>
