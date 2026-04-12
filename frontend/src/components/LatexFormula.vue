<template>
  <div class="latex-formula" :class="{ 'is-inline': !display }">
    <div v-if="renderError" class="latex-fallback">
      <span>公式渲染失败</span>
      <code>{{ formula }}</code>
    </div>
    <div v-else v-html="renderedFormula"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const props = defineProps({
  formula: { type: String, required: true },
  display: { type: Boolean, default: true },
})

const renderedFormula = computed(() => {
  try {
    return katex.renderToString(props.formula, {
      displayMode: props.display,
      throwOnError: false,
      strict: false,
      trust: false,
    })
  } catch {
    return ''
  }
})

const renderError = computed(() => !renderedFormula.value)
</script>

<style scoped>
.latex-formula {
  overflow-x: auto;
  padding: 10px 12px;
  border: 1px solid #d8f3dc;
  border-radius: 10px;
  background: #f4fbf6;
}
.latex-formula.is-inline {
  display: inline-block;
  padding: 4px 6px;
}
.latex-fallback {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #c92a2a;
  font-size: 12px;
}
.latex-fallback code {
  color: #14532d;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
