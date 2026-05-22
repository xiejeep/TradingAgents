<script setup lang="ts">
import { computed, ref, h } from 'vue'
import {
  LoadingOutlined,
  CheckCircleOutlined,
  RobotOutlined,
  ToolOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue'
import { useAnalysisStore } from '@/stores/analysis'

const props = withDefaults(defineProps<{ compact?: boolean }>(), { compact: false })
const store = useAnalysisStore()

const reportSections = computed(() => [
  { key: 'market_report', label: '行情分析师', content: store.reportSections.market_report },
  { key: 'sentiment_report', label: '情绪分析师', content: store.reportSections.sentiment_report },
  { key: 'news_report', label: '新闻分析师', content: store.reportSections.news_report },
  { key: 'fundamentals_report', label: '基本面分析师', content: store.reportSections.fundamentals_report },
])

const activeSection = ref<string>('market_report')

const latestToolCalls = computed(() => {
  return store.toolCalls.slice(-5)
})

const sectionsWithContent = computed(() =>
  reportSections.value.filter((s) => s.content)
)

function getAgentLabel(type: string): string {
  const map: Record<string, string> = {
    ai: 'AI 分析师',
    human: '请求',
    tool: '工具结果',
  }
  return map[type] || type
}
</script>

<template>
  <div class="stream-progress">
    <a-card v-if="store.status === 'running'" style="margin-bottom: 16px">
      <div class="running-status">
        <LoadingOutlined :spin="true" />
        <span style="margin-left: 8px; font-size: 16px">分析进行中...</span>
        <a-tag color="processing" style="margin-left: 12px">
          {{ store.messages.length }} 条消息
        </a-tag>
      </div>
    </a-card>

    <a-row v-if="!compact" :gutter="16">
      <a-col :span="14">
        <a-card
          title="分析报告"
          size="small"
          :tab-list="sectionsWithContent.map(s => ({ key: s.key, tab: s.label }))"
          :active-tab-key="activeSection"
          @tabChange="(k: string) => activeSection = k"
          style="margin-bottom: 16px"
        >
          <div class="report-content">
            <pre v-if="store.reportSections[activeSection]" style="white-space: pre-wrap; word-break: break-word; font-family: inherit; margin: 0; font-size: 14px; line-height: 1.8">{{ store.reportSections[activeSection] }}</pre>
            <a-empty v-else description="等待分析师产出报告..." />
          </div>
        </a-card>
      </a-col>

      <a-col :span="10">
        <a-card title="Agent 消息" size="small" style="margin-bottom: 16px">
          <div v-if="store.agentMessages.length === 0" style="text-align: center; padding: 24px; color: #999">
            等待 Agent 消息...
          </div>
          <a-list
            v-else
            :data-source="store.agentMessages.slice(-10).reverse()"
            size="small"
            :split="false"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-card size="small" style="width: 100%">
                  <template #title>
                    <a-tag>{{ getAgentLabel(item.agent_type) }}</a-tag>
                    <span style="font-size: 12px; color: #999; margin-left: 8px">{{ item.timestamp }}</span>
                  </template>
                  <p style="white-space: pre-wrap; word-break: break-word; margin: 0; font-size: 13px; max-height: 200px; overflow-y: auto">
                    {{ item.content?.slice(0, 500) }}
                  </p>
                </a-card>
              </a-list-item>
            </template>
          </a-list>
        </a-card>

        <a-card title="工具调用" size="small">
          <div v-if="latestToolCalls.length === 0" style="text-align: center; padding: 24px; color: #999">
            暂无工具调用
          </div>
          <a-timeline v-else>
            <a-timeline-item
              v-for="(tc, idx) in latestToolCalls"
              :key="idx"
              color="blue"
            >
              <a-tag color="blue">{{ tc.name }}</a-tag>
              <span v-if="tc.args" style="font-size: 12px; color: #999">
                {{ Object.values(tc.args).join(', ').slice(0, 80) }}
              </span>
            </a-timeline-item>
          </a-timeline>
        </a-card>
      </a-col>
    </a-row>

    <div v-else>
      <a-card
        v-if="sectionsWithContent.length > 0"
        title="分析报告"
        size="small"
        :tab-list="sectionsWithContent.map(s => ({ key: s.key, tab: s.label }))"
        :active-tab-key="activeSection"
        @tabChange="(k: string) => activeSection = k"
        style="margin-bottom: 16px"
      >
        <div class="report-content">
          <pre style="white-space: pre-wrap; word-break: break-word; font-family: inherit; margin: 0; font-size: 14px; line-height: 1.8">{{ store.reportSections[activeSection] }}</pre>
        </div>
      </a-card>

      <a-collapse v-if="store.agentMessages.length > 0" style="margin-top: 16px">
        <a-collapse-panel header="Agent 消息记录" key="agents">
          <a-list
            :data-source="store.agentMessages.slice().reverse()"
            size="small"
            :split="false"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-card size="small" style="width: 100%">
                  <template #title>
                    <a-tag>{{ getAgentLabel(item.agent_type) }}</a-tag>
                    <span style="font-size: 12px; color: #999; margin-left: 8px">{{ item.timestamp }}</span>
                  </template>
                  <p style="white-space: pre-wrap; word-break: break-word; margin: 0; font-size: 13px; max-height: 200px; overflow-y: auto">
                    {{ item.content?.slice(0, 500) }}
                  </p>
                </a-card>
              </a-list-item>
            </template>
          </a-list>
        </a-collapse-panel>
      </a-collapse>
    </div>
  </div>
</template>

<style scoped>
.running-status {
  display: flex;
  align-items: center;
}
.report-content {
  min-height: 300px;
  max-height: 600px;
  overflow-y: auto;
}
</style>
