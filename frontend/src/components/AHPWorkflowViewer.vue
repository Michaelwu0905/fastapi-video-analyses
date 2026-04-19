<template>
  <div class="workflow-viewer">
    <div class="workflow-toolbar">
      <div>
        <strong>AHP 计算流程图</strong>
        <span>拖动画布查看完整链路</span>
      </div>
      <div class="toolbar-actions">
        <button type="button" @click="zoomOut">缩小</button>
        <button type="button" @click="resetView">重置视图</button>
        <button type="button" @click="zoomIn">放大</button>
      </div>
    </div>

    <div
      ref="viewportRef"
      class="workflow-viewport"
      @pointerdown="startPan"
      @pointermove="movePan"
      @pointerup="endPan"
      @pointercancel="endPan"
      @pointerleave="endPan"
    >
      <div
        class="workflow-canvas"
        :style="{
          width: `${canvas.width}px`,
          height: `${canvas.height}px`,
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
        }"
      >
        <svg
          class="workflow-edges"
          :width="canvas.width"
          :height="canvas.height"
          aria-hidden="true"
        >
          <defs>
            <marker
              id="workflow-arrow"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" />
            </marker>
          </defs>
          <path
            v-for="edge in edges"
            :key="edge.key"
            class="workflow-edge"
            :d="edge.path"
          />
        </svg>

        <div class="stage-label" :style="stageStyle(40)">原始指标</div>
        <div class="stage-label" :style="stageStyle(350)">标准化</div>
        <div class="stage-label" :style="stageStyle(660)">AHP 权重</div>
        <div class="stage-label" :style="stageStyle(980)">维度得分</div>
        <div class="stage-label final-stage" :style="stageStyle(1280)">综合得分</div>

        <section
          v-for="group in groups"
          :key="`group-${group.key}`"
          class="dimension-band"
          :class="`band-${group.key}`"
          :style="bandStyle(group)"
        >
          <span>{{ group.label }}</span>
        </section>

        <article
          v-for="node in nodes"
          :key="node.id"
          class="workflow-node"
          :class="[node.kind, `node-${node.group}`]"
          :style="nodeStyle(node)"
          :title="node.tooltip"
        >
          <span class="node-type">{{ node.typeLabel }}</span>
          <strong>{{ node.title }}</strong>
          <small>{{ node.subtitle }}</small>
        </article>

        <button
          v-for="edge in edges"
          :key="`formula-${edge.key}`"
          type="button"
          class="formula-dot"
          :class="{ active: selectedEdge?.key === edge.key }"
          :style="edgeButtonStyle(edge)"
          :title="edge.title"
          @pointerdown.stop
          @click.stop="selectEdge(edge)"
        >
          i
        </button>
      </div>

      <aside
        v-if="selectedEdge"
        class="formula-popover"
        @pointerdown.stop
        @click.stop
      >
        <div class="popover-header">
          <div>
            <strong>{{ selectedEdge.title }}</strong>
            <span>{{ selectedEdge.description }}</span>
          </div>
          <button type="button" @click="closeFormula">关闭</button>
        </div>
        <LatexFormula :formula="selectedEdge.formula" />
        <p>{{ selectedEdge.text }}</p>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import LatexFormula from './LatexFormula.vue'

const props = defineProps({
  result: { type: Object, required: true },
})

const groups = [
  { key: 'breadth', label: '传播广度' },
  { key: 'depth', label: '互动深度' },
  { key: 'recognition', label: '传播认同' },
  { key: 'knowledge_effect', label: '知识传播效果' },
]

const canvasWidth = 1540
const nodeSize = { width: 210, height: 76 }
const columnX = {
  raw: 40,
  normalized: 350,
  weight: 660,
  dimension: 980,
  total: 1280,
}

const viewportRef = ref(null)
const scale = ref(0.88)
const selectedEdgeKey = ref(null)
const pan = reactive({ x: 0, y: 0 })
const drag = reactive({ active: false, startX: 0, startY: 0, originX: 0, originY: 0 })

const formulaView = computed(() => props.result?.formula_view ?? {})

const groupLayout = computed(() => {
  const layout = {}
  let cursor = 74
  for (const group of groups) {
    const count = Math.max(formulaView.value.raw_metrics?.[group.key]?.length ?? 0, 1)
    const height = count * 94 + 42
    layout[group.key] = {
      top: cursor,
      height,
      center: cursor + height / 2,
    }
    cursor += height + 26
  }
  return layout
})

const canvas = computed(() => {
  const lastGroup = groups[groups.length - 1]
  const lastLayout = groupLayout.value[lastGroup.key]
  return {
    width: canvasWidth,
    height: Math.max(1040, (lastLayout?.top ?? 0) + (lastLayout?.height ?? 0) + 110),
  }
})

const nodes = computed(() => {
  const resultNodes = []

  for (const group of groups) {
    const rawItems = formulaView.value.raw_metrics?.[group.key] ?? []
    const normalizedItems = formulaView.value.normalized_metrics?.[group.key] ?? []
    const weightItems = formulaView.value.weight_metrics?.[group.key] ?? []
    const top = groupLayout.value[group.key]?.top ?? 0

    rawItems.forEach((item, index) => {
      const y = top + 36 + index * 94
      const normalized = normalizedItems.find((row) => row.key === item.key)
      const weight = weightItems.find((row) => row.key === item.key)

      resultNodes.push(makeNode({
        id: `raw-${item.key}`,
        group: group.key,
        kind: 'raw',
        typeLabel: '原始值',
        title: item.name,
        subtitle: formatValue(item.value),
        tooltip: `${item.name} 当前原始值：${formatValue(item.value)}`,
        x: columnX.raw,
        y,
      }))

      resultNodes.push(makeNode({
        id: `normalized-${item.key}`,
        group: group.key,
        kind: 'normalized',
        typeLabel: '标准化',
        title: item.name,
        subtitle: normalized ? `z = ${normalized.normalized_value}` : 'z = -',
        tooltip: normalized?.formula_text ?? '',
        x: columnX.normalized,
        y,
      }))

      resultNodes.push(makeNode({
        id: `weight-${item.key}`,
        group: group.key,
        kind: 'weight',
        typeLabel: '权重',
        title: item.name,
        subtitle: weight ? `w = ${weight.combined_weight}` : 'w = -',
        tooltip: weight?.formula_text ?? '',
        x: columnX.weight,
        y,
      }))
    })

    const dimension = (formulaView.value.dimension_formulas ?? []).find((item) => item.key === group.key)
    resultNodes.push(makeNode({
      id: `dimension-${group.key}`,
      group: group.key,
      kind: 'dimension',
      typeLabel: '维度得分',
      title: group.label,
      subtitle: dimension ? `${dimension.score} 分` : '-',
      tooltip: dimension?.formula_text ?? '',
      x: columnX.dimension,
      y: (groupLayout.value[group.key]?.center ?? 0) - nodeSize.height / 2,
    }))
  }

  resultNodes.push(makeNode({
    id: 'total-score',
    group: 'total',
    kind: 'total',
    typeLabel: '最终结果',
    title: '综合传播力',
    subtitle: `${props.result.total_score} 分 · ${props.result.level}`,
    tooltip: formulaView.value.total_formula?.formula_text ?? '',
    x: columnX.total,
    y: canvas.value.height / 2 - nodeSize.height / 2,
  }))

  return resultNodes
})

const nodeMap = computed(() => {
  const map = new Map()
  for (const node of nodes.value) map.set(node.id, node)
  return map
})

const edges = computed(() => {
  const resultEdges = []
  const indicators = groups.flatMap((group) => formulaView.value.raw_metrics?.[group.key] ?? [])

  for (const item of indicators) {
    resultEdges.push(makeEdge(
      `raw-${item.key}`,
      `normalized-${item.key}`,
      buildNormalizationDetail(item),
    ))
    resultEdges.push(makeEdge(
      `normalized-${item.key}`,
      `weight-${item.key}`,
      buildWeightDetail(item),
    ))
    resultEdges.push(makeEdge(
      `weight-${item.key}`,
      `dimension-${item.criterion}`,
      buildDimensionContributionDetail(item),
    ))
  }

  for (const group of groups) {
    resultEdges.push(makeEdge(
      `dimension-${group.key}`,
      'total-score',
      buildTotalContributionDetail(group),
    ))
  }

  return resultEdges.filter(Boolean)
})

const selectedEdge = computed(() => edges.value.find((edge) => edge.key === selectedEdgeKey.value) ?? null)

function makeNode({ id, group, kind, typeLabel, title, subtitle, tooltip, x, y }) {
  return { id, group, kind, typeLabel, title, subtitle, tooltip, x, y, width: nodeSize.width, height: nodeSize.height }
}

function makeEdge(fromId, toId, detail) {
  const from = nodeMap.value.get(fromId)
  const to = nodeMap.value.get(toId)
  if (!from || !to) return null

  const startX = from.x + from.width
  const startY = from.y + from.height / 2
  const endX = to.x
  const endY = to.y + to.height / 2
  const curve = Math.max(70, (endX - startX) / 2)

  return {
    key: `${fromId}-${toId}`,
    path: `M ${startX} ${startY} C ${startX + curve} ${startY}, ${endX - curve} ${endY}, ${endX} ${endY}`,
    buttonX: (startX + endX) / 2,
    buttonY: (startY + endY) / 2,
    ...detail,
  }
}

function nodeStyle(node) {
  return {
    width: `${node.width}px`,
    minHeight: `${node.height}px`,
    transform: `translate(${node.x}px, ${node.y}px)`,
  }
}

function edgeButtonStyle(edge) {
  return {
    transform: `translate(${edge.buttonX - 13}px, ${edge.buttonY - 13}px)`,
  }
}

function bandStyle(group) {
  const layout = groupLayout.value[group.key]
  return {
    top: `${layout.top - 12}px`,
    height: `${layout.height + 24}px`,
  }
}

function stageStyle(x) {
  return { transform: `translate(${x}px, 22px)` }
}

function formatValue(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return String(value ?? '-')
  if (Math.abs(numeric) >= 10000) return numeric.toLocaleString('zh-CN', { maximumFractionDigits: 0 })
  if (Math.abs(numeric) >= 1) return numeric.toLocaleString('zh-CN', { maximumFractionDigits: 4 })
  return numeric.toLocaleString('zh-CN', { maximumFractionDigits: 6 })
}

function findNormalized(indicator) {
  return (formulaView.value.normalized_metrics?.[indicator.criterion] ?? [])
    .find((item) => item.key === indicator.key)
}

function findWeight(indicator) {
  return (formulaView.value.weight_metrics?.[indicator.criterion] ?? [])
    .find((item) => item.key === indicator.key)
}

function findDimensionItem(indicator) {
  const dimension = (formulaView.value.dimension_formulas ?? [])
    .find((item) => item.key === indicator.criterion)
  return dimension?.items?.find((item) => item.key === indicator.key)
}

function buildNormalizationDetail(indicator) {
  const normalized = findNormalized(indicator)
  const formula = normalized?.is_constant
    ? String.raw`z_j=0,\quad \max(X_j)-\min(X_j)=0`
    : String.raw`z_j=\frac{x_j-\min(X_j)}{\max(X_j)-\min(X_j)}=\frac{${latexNumber(normalized?.raw_value)}-${latexNumber(normalized?.min_value)}}{${latexNumber(normalized?.max_value)}-${latexNumber(normalized?.min_value)}}=${latexNumber(normalized?.normalized_value)}`

  return {
    title: `${indicator.name}：原始值标准化`,
    description: '将不同量纲的指标压缩到 0-1 区间，便于后续加权。',
    formula,
    text: normalized?.formula_text ?? `${indicator.name} 标准化结果暂不可用。`,
  }
}

function buildWeightDetail(indicator) {
  const weight = findWeight(indicator)
  return {
    title: `${indicator.name}：AHP 权重`,
    description: '由一级维度判断矩阵和维度内指标判断矩阵共同得到最终权重。',
    formula: String.raw`w_j=w_j^A=${latexNumber(weight?.combined_weight)}`,
    text: weight?.formula_text ?? `${indicator.name} 的 AHP 权重暂不可用。`,
  }
}

function buildDimensionContributionDetail(indicator) {
  const item = findDimensionItem(indicator)
  const contribution = Number(item?.normalized_value ?? 0) * Number(item?.dimension_weight ?? 0) * 100
  return {
    title: `${indicator.name}：进入维度得分`,
    description: '标准化值乘以维度内权重，形成该指标对一级维度得分的贡献。',
    formula: String.raw`C_{j|d}=z_j\times w_{j|d}\times100=${latexNumber(item?.normalized_value)}\times${latexNumber(item?.dimension_weight)}\times100=${latexNumber(contribution, 2)}`,
    text: `${indicator.name} 在 ${indicator.criterion_label} 维度内的贡献值约为 ${formatValue(contribution)} 分。`,
  }
}

function buildTotalContributionDetail(group) {
  const terms = formulaView.value.total_formula?.terms ?? []
  const groupTerms = terms.filter((item) => item.criterion === group.key)
  const contribution = groupTerms.reduce((sum, item) => sum + Number(item.contribution || 0), 0)
  const latexTerms = groupTerms
    .map((item) => `${latexNumber(item.normalized_value)}\\times${latexNumber(item.combined_weight)}`)
    .join('+') || '0'

  return {
    title: `${group.label}：汇入综合得分`,
    description: '该维度下所有指标按全局权重加权后，汇入最终传播力总分。',
    formula: String.raw`C_d=\left(${latexTerms}\right)\times100=${latexNumber(contribution, 2)}`,
    text: `${group.label} 对综合传播力得分的直接贡献约为 ${formatValue(contribution)} 分。`,
  }
}

function latexNumber(value, digits = 4) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric)) return '0'
  return Number(numeric.toFixed(digits)).toString()
}

function selectEdge(edge) {
  selectedEdgeKey.value = selectedEdgeKey.value === edge.key ? null : edge.key
}

function closeFormula() {
  selectedEdgeKey.value = null
}

function startPan(event) {
  if (event.button !== 0) return
  drag.active = true
  drag.startX = event.clientX
  drag.startY = event.clientY
  drag.originX = pan.x
  drag.originY = pan.y
  viewportRef.value?.setPointerCapture?.(event.pointerId)
}

function movePan(event) {
  if (!drag.active) return
  pan.x = drag.originX + event.clientX - drag.startX
  pan.y = drag.originY + event.clientY - drag.startY
}

function endPan(event) {
  if (!drag.active) return
  drag.active = false
  viewportRef.value?.releasePointerCapture?.(event.pointerId)
}

function zoomIn() {
  scale.value = Math.min(1.35, Number((scale.value + 0.1).toFixed(2)))
}

function zoomOut() {
  scale.value = Math.max(0.55, Number((scale.value - 0.1).toFixed(2)))
}

function resetView() {
  scale.value = 0.88
  pan.x = 0
  pan.y = 0
  selectedEdgeKey.value = null
}
</script>

<style scoped>
.workflow-viewer {
  border: 1px solid #e4ebf0;
  border-radius: 14px;
  background: #f8fafc;
  overflow: hidden;
}
.workflow-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border-bottom: 1px solid #e4ebf0;
  background: white;
}
.workflow-toolbar div:first-child {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.workflow-toolbar strong {
  font-size: 14px;
  color: var(--text-primary);
}
.workflow-toolbar span {
  font-size: 12px;
  color: var(--text-muted);
}
.toolbar-actions {
  display: flex;
  gap: 8px;
}
.toolbar-actions button {
  border: 1px solid #d7e0e7;
  background: #fbfdff;
  color: var(--text-secondary);
  border-radius: 8px;
  padding: 7px 10px;
  font-size: 12px;
  cursor: pointer;
}
.toolbar-actions button:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}
.workflow-viewport {
  position: relative;
  height: 520px;
  overflow: hidden;
  cursor: grab;
  touch-action: none;
  user-select: none;
  background:
    radial-gradient(circle at 1px 1px, #d9e3ea 1px, transparent 0) 0 0 / 22px 22px,
    linear-gradient(180deg, #fbfdff 0%, #f5f8fb 100%);
}
.workflow-viewport:active {
  cursor: grabbing;
}
.workflow-canvas {
  position: relative;
  transform-origin: 0 0;
}
.workflow-edges {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 2;
}
.workflow-edge {
  fill: none;
  stroke: #9fb6c8;
  stroke-width: 1.8;
  marker-end: url(#workflow-arrow);
}
marker path {
  fill: #9fb6c8;
}
.stage-label {
  position: absolute;
  top: 0;
  width: 210px;
  padding: 8px 10px;
  border-radius: 999px;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  color: #36536a;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid #dbe6ef;
  z-index: 4;
}
.final-stage {
  color: #0f766e;
  border-color: #99f6e4;
  background: #ecfdf5;
}
.dimension-band {
  position: absolute;
  left: 22px;
  right: 22px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  z-index: 1;
}
.dimension-band span {
  position: absolute;
  left: 12px;
  top: 8px;
  font-size: 12px;
  font-weight: 700;
  color: rgba(15, 23, 42, 0.48);
}
.band-breadth { background: rgba(224, 242, 254, 0.46); }
.band-depth { background: rgba(236, 253, 245, 0.5); }
.band-recognition { background: rgba(255, 247, 237, 0.56); }
.band-knowledge_effect { background: rgba(245, 243, 255, 0.52); }
.workflow-node {
  position: absolute;
  z-index: 3;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid #dce7ef;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
  pointer-events: auto;
}
.workflow-node:hover {
  border-color: var(--primary-color);
  box-shadow: 0 12px 28px rgba(0, 174, 236, 0.16);
}
.node-type {
  align-self: flex-start;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  color: #64748b;
  background: #f1f5f9;
}
.workflow-node strong {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.35;
}
.workflow-node small {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.45;
}
.workflow-node.dimension {
  border-color: #bae6fd;
  background: #f0f9ff;
}
.workflow-node.total {
  border-color: #99f6e4;
  background: linear-gradient(180deg, #ecfdf5 0%, #ffffff 100%);
}
.workflow-node.total strong {
  color: #0f766e;
  font-size: 16px;
}
.workflow-node.total small {
  color: #047857;
  font-weight: 700;
}
.formula-dot {
  position: absolute;
  z-index: 6;
  width: 26px;
  height: 26px;
  border-radius: 999px;
  border: 2px solid #38bdf8;
  background: white;
  color: #0284c7;
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
  box-shadow: 0 6px 16px rgba(2, 132, 199, 0.22);
  cursor: pointer;
  pointer-events: auto;
  transition: transform 0.15s ease, border-color 0.15s ease, background 0.15s ease;
}
.formula-dot:hover,
.formula-dot.active {
  border-color: #0f766e;
  background: #ecfdf5;
  color: #0f766e;
}
.formula-popover {
  position: absolute;
  right: 18px;
  bottom: 18px;
  z-index: 20;
  width: min(460px, calc(100% - 36px));
  max-height: calc(100% - 36px);
  overflow-y: auto;
  padding: 16px;
  border: 1px solid #bfdbfe;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 22px 60px rgba(15, 23, 42, 0.2);
  cursor: default;
}
.popover-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}
.popover-header div {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.popover-header strong {
  font-size: 14px;
  color: var(--text-primary);
}
.popover-header span {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.55;
}
.popover-header button {
  border: 1px solid #d7e0e7;
  background: #fbfdff;
  color: var(--text-secondary);
  border-radius: 8px;
  padding: 6px 9px;
  font-size: 12px;
  cursor: pointer;
  flex-shrink: 0;
}
.formula-popover p {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.7;
}
@media (max-width: 700px) {
  .workflow-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }
  .workflow-viewport {
    height: 460px;
  }
  .formula-popover {
    right: 10px;
    bottom: 10px;
    width: calc(100% - 20px);
  }
}
</style>
