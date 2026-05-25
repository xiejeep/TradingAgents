<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  DownloadOutlined,
  TrophyOutlined,
  StarOutlined,
} from '@ant-design/icons-vue'
import { getReport, getReportPdfUrl, getHistoryDetail, getHistoryPdfUrl, type ReportData } from '@/api'
import { marked } from 'marked'

const route = useRoute()
const taskId = route.params.taskId as string

const loading = ref(true)
const report = ref<ReportData | null>(null)
const historyReport = ref<string | null>(null)
const historySections = ref<Record<string, string> | null>(null)
const decision = ref<string>('')
const rating = ref<string>('')
const pdfUrl = ref<string>('')
const source = ref<'task' | 'history' | null>(null)

marked.setOptions({ breaks: true, gfm: true })

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

const visibleHistorySections = computed(() =>
  sections.filter((s) => historySections.value?.[s.key])
)

function getRatingColor(r?: string): string {
  if (!r) return 'default'
  const rl = r.toLowerCase()
  if (rl.includes('buy') || rl.includes('买入') || rl.includes('strong')) return 'green'
  if (rl.includes('sell') || rl.includes('卖出')) return 'red'
  if (rl.includes('hold') || rl.includes('持有')) return 'orange'
  return 'blue'
}

function renderMarkdown(content: string): string {
  return marked.parse(content) as string
}

onMounted(async () => {
  try {
    const taskResult = await getReport(taskId)
    if (taskResult.error) throw new Error(taskResult.error)
    report.value = taskResult
    decision.value = taskResult.decision || ''
    rating.value = taskResult.rating || ''
    pdfUrl.value = getReportPdfUrl(taskId)
    source.value = 'task'
  } catch {
    try {
      const historyResult = await getHistoryDetail(taskId)
      if ((historyResult as any).error) throw new Error((historyResult as any).error)
      historyReport.value = historyResult.report_content
      decision.value = historyResult.entry?.decision || ''
      rating.value = historyResult.entry?.rating || ''
      pdfUrl.value = getHistoryPdfUrl(taskId)
      source.value = 'history'

      const sectionKeys = sections.map((s) => s.key)
      const extracted: Record<string, string> = {}
      const raw = historyResult as Record<string, any>
      for (const key of sectionKeys) {
        if (raw[key]) {
          extracted[key] = raw[key]
        }
      }
      if (Object.keys(extracted).length > 0) {
        historySections.value = extracted
      }
    } catch (err: any) {
      message.error('加载报告失败: ' + (err?.message || '未知错误'))
    }
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="report-page">
    <a-page-header
      style="padding: 0; margin-bottom: 24px"
      title="分析报告"
      @back="$router.back()"
    >
      <template #tags>
        <a-tag v-if="rating" :color="getRatingColor(rating)">
          <StarOutlined /> {{ rating }}
        </a-tag>
        <a-tag v-if="source === 'history'" color="default">历史记录</a-tag>
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
      <template v-if="source === 'task' && report?.status === 'completed'">
        <div v-if="decision" class="decision-box">
          <TrophyOutlined class="decision-icon" />
          <div>
            <h3 class="decision-title">分析决策</h3>
            <p class="decision-text">{{ decision }}</p>
          </div>
        </div>

        <a-card>
          <a-tabs v-if="visibleSections.length > 0">
            <a-tab-pane
              v-for="s in visibleSections"
              :key="s.key"
              :tab="s.label"
            >
              <div
                class="markdown-body"
                v-html="renderMarkdown((report as any)[s.key])"
              />
            </a-tab-pane>
          </a-tabs>
          <a-empty v-else description="暂无报告内容" />
        </a-card>
      </template>

      <template v-else-if="source === 'history'">
        <div v-if="decision" class="decision-box">
          <TrophyOutlined class="decision-icon" />
          <div>
            <h3 class="decision-title">分析决策</h3>
            <p class="decision-text">{{ decision }}</p>
          </div>
        </div>

        <template v-if="historySections">
          <a-card>
            <a-tabs>
              <a-tab-pane
                v-for="s in visibleHistorySections"
                :key="s.key"
                :tab="s.label"
              >
                <div
                  class="markdown-body"
                  v-html="renderMarkdown(historySections[s.key])"
                />
              </a-tab-pane>
            </a-tabs>
          </a-card>
        </template>
        <a-card v-else-if="historyReport">
          <div
            class="markdown-body"
            v-html="renderMarkdown(historyReport)"
          />
        </a-card>
      </template>

      <template v-else-if="source === 'task' && report">
        <a-result status="warning" :title="`状态: ${report.status}`">
          <template #extra>
            <a-button type="primary" @click="$router.push('/')">返回分析页</a-button>
          </template>
        </a-result>
      </template>

      <a-result
        v-else-if="!loading && !source"
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
.report-page {
  max-width: 1200px;
}
.decision-box {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #f0f5ff, #e6f7ff);
  border: 1px solid #91d5ff;
  border-radius: 8px;
  padding: 20px 24px;
  margin-bottom: 16px;
}
.decision-icon {
  font-size: 28px;
  color: #faad14;
  margin-right: 16px;
  flex-shrink: 0;
}
.decision-title {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #666;
}
.decision-text {
  margin: 0;
  font-size: 18px;
  color: #1a1a1a;
  font-weight: 600;
}
</style>
