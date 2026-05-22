<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  DownloadOutlined,
  TrophyOutlined,
  StarOutlined,
} from '@ant-design/icons-vue'
import { getReport, getReportPdfUrl, type ReportData } from '@/api'

const route = useRoute()
const taskId = route.params.taskId as string

const loading = ref(true)
const report = ref<ReportData | null>(null)
const pdfUrl = ref<string>('')

const sections = [
  { key: 'market_report', label: '行情分析' },
  { key: 'sentiment_report', label: '情绪分析' },
  { key: 'news_report', label: '新闻分析' },
  { key: 'fundamentals_report', label: '基本面分析' },
  { key: 'investment_plan', label: '投资计划' },
  { key: 'trader_investment_plan', label: '交易计划' },
  { key: 'final_trade_decision', label: '最终决策' },
]

const visibleSections = computed(() =>
  sections.filter((s) => (report.value as any)?.[s.key])
)

function getRatingColor(rating?: string): string {
  if (!rating) return 'default'
  const r = rating.toLowerCase()
  if (r.includes('buy') || r.includes('买入') || r.includes('strong')) return 'green'
  if (r.includes('sell') || r.includes('卖出')) return 'red'
  if (r.includes('hold') || r.includes('持有')) return 'orange'
  return 'blue'
}

function formatContent(content?: string): string {
  if (!content) return ''
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br/>')
}

onMounted(async () => {
  try {
    report.value = await getReport(taskId)
    pdfUrl.value = getReportPdfUrl(taskId)
  } catch (err: any) {
    message.error('加载报告失败: ' + err.message)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="report-page" style="max-width: 1200px">
    <a-page-header
      style="padding: 0; margin-bottom: 24px"
      title="分析报告"
      @back="$router.back()"
    >
      <template #tags>
        <a-tag v-if="report?.rating" :color="getRatingColor(report.rating)">
          <StarOutlined /> {{ report.rating }}
        </a-tag>
      </template>
      <template #extra>
        <a-space>
          <a-button :href="pdfUrl" type="primary" target="_blank">
            <template #icon><DownloadOutlined /></template>
            导出 PDF
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-spin :spinning="loading">
      <template v-if="report?.status === 'completed'">
        <a-card v-if="report.decision" style="margin-bottom: 16px">
          <div style="display: flex; align-items: center">
            <TrophyOutlined style="font-size: 24px; color: #faad14" />
            <div style="margin-left: 12px">
              <h3 style="margin: 0 0 4px 0">分析决策</h3>
              <p style="margin: 0; font-size: 16px; color: #333; font-weight: 500">
                {{ report.decision }}
              </p>
            </div>
          </div>
        </a-card>

        <a-card>
          <a-tabs v-if="visibleSections.length > 0">
            <a-tab-pane
              v-for="s in visibleSections"
              :key="s.key"
              :tab="s.label"
            >
              <div
                class="report-body"
                v-html="formatContent((report as any)[s.key])"
              />
            </a-tab-pane>
          </a-tabs>

          <a-empty v-else description="暂无报告内容" />
        </a-card>
      </template>

      <a-result
        v-else-if="report"
        status="warning"
        :title="`状态: ${report.status}`"
      >
        <template #extra>
          <a-button type="primary" @click="$router.push('/')">返回分析页</a-button>
        </template>
      </a-result>

      <a-result
        v-else-if="!loading"
        status="error"
        title="报告不存在"
      >
        <template #extra>
          <a-button type="primary" @click="$router.push('/')">返回分析页</a-button>
        </template>
      </a-result>
    </a-spin>
  </div>
</template>

<style scoped>
.report-body {
  padding: 16px;
  line-height: 1.8;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
