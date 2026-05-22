<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  title: string
  content: string
  type?: 'default' | 'decision'
}>()

const formattedContent = computed(() => {
  if (!props.content) return ''
  return props.content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br/>')
})
</script>

<template>
  <div class="report-section" :class="`report-section--${type || 'default'}`">
    <div class="report-body" v-html="formattedContent" />
  </div>
</template>

<style scoped>
.report-section {
  margin-bottom: 16px;
}
.report-section--decision {
  border: 1px solid #1677ff;
  border-radius: 8px;
  padding: 16px;
  background: #f0f5ff;
}
.report-body {
  line-height: 1.8;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}
.report-section--decision .report-body {
  font-size: 16px;
  font-weight: 500;
}
</style>
