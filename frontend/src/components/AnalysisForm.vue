<script setup lang="ts">
import { ref, reactive } from 'vue'
import {
  ThunderboltOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons-vue'
import type { AnalysisConfig } from '@/api'
import { getModels } from '@/api'
import dayjs, { type Dayjs } from 'dayjs'

const emit = defineEmits<{
  submit: [config: AnalysisConfig]
}>()

defineProps<{ loading: boolean }>()

const formRef = ref()

const today = dayjs()

const formState = reactive({
  ticker: 'AAPL',
  analysis_date: today as Dayjs | null,
  data_vendor: 'yfinance',
  output_language: 'Chinese',
  analysts: ['market', 'social', 'news', 'fundamentals'],
  research_depth: 1,
  llm_provider: 'deepseek',
  shallow_thinker: 'deepseek-v4-flash',
  deep_thinker: 'deepseek-v4-pro',
})

const shallowModels = ref<{ label: string; value: string }[]>([])
const deepModels = ref<{ label: string; value: string }[]>([])

const rules = {
  ticker: [{ required: true, message: '请输入股票代码' }],
  analysis_date: [{ required: true, message: '请选择分析日期' }],
}

const analystOptions = [
  { label: '行情分析师', value: 'market' },
  { label: '社交媒体分析师', value: 'social' },
  { label: '新闻分析师', value: 'news' },
  { label: '基本面分析师', value: 'fundamentals' },
]

const vendorOptions = [
  { label: 'Yahoo Finance', value: 'yfinance' },
  { label: 'Alpha Vantage', value: 'alpha_vantage' },
  { label: 'AKShare (A股)', value: 'akshare' },
]

const providerOptions = [
  { label: 'DeepSeek', value: 'deepseek' },
  { label: 'OpenAI', value: 'openai' },
  { label: 'Anthropic', value: 'anthropic' },
  { label: 'Google Gemini', value: 'google' },
  { label: 'xAI', value: 'xai' },
  { label: 'Azure OpenAI', value: 'azure' },
  { label: 'Qwen', value: 'qwen' },
  { label: 'GLM', value: 'glm' },
  { label: 'MiniMax', value: 'minimax' },
  { label: 'OpenRouter', value: 'openrouter' },
]

const languageOptions = [
  { label: '中文', value: 'Chinese' },
  { label: 'English', value: 'English' },
]

async function loadModels(provider: string) {
  try {
    const result = await getModels(provider)
    const models = result.models || []
    shallowModels.value = models
    deepModels.value = models
  } catch {
    shallowModels.value = []
    deepModels.value = []
  }
}

loadModels(formState.llm_provider)

function onProviderChange(provider: string) {
  loadModels(provider)
}

async function onSubmit() {
  try {
    await formRef.value?.validate()
    const dateStr = formState.analysis_date
      ? dayjs(formState.analysis_date).format('YYYY-MM-DD')
      : today.format('YYYY-MM-DD')

    emit('submit', {
      ticker: formState.ticker,
      analysis_date: dateStr,
      data_vendor: formState.data_vendor,
      output_language: formState.output_language,
      analysts: formState.analysts,
      research_depth: formState.research_depth,
      llm_provider: formState.llm_provider,
      shallow_thinker: formState.shallow_thinker,
      deep_thinker: formState.deep_thinker,
      checkpoint_enabled: false,
    })
  } catch {
    // validation failed
  }
}
</script>

<template>
  <a-card>
    <a-form
      ref="formRef"
      :model="formState"
      :rules="rules"
      layout="vertical"
    >
      <a-row :gutter="24">
        <a-col :xs="24" :sm="12" :lg="8">
          <a-form-item label="股票代码" name="ticker">
            <a-input
              v-model:value="formState.ticker"
              placeholder="例如 AAPL, TSLA, 000001.SZ"
              size="large"
            />
          </a-form-item>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="8">
          <a-form-item label="分析日期" name="analysis_date">
            <a-date-picker
              v-model:value="formState.analysis_date"
              style="width: 100%"
              size="large"
              :disabled-date="(d: Dayjs) => d && d.isAfter(today, 'day')"
            />
          </a-form-item>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="8">
          <a-form-item label="数据源">
            <a-select
              v-model:value="formState.data_vendor"
              :options="vendorOptions"
              size="large"
            />
          </a-form-item>
        </a-col>
      </a-row>

      <a-row :gutter="24">
        <a-col :xs="24" :sm="12" :lg="8">
          <a-form-item label="输出语言">
            <a-select
              v-model:value="formState.output_language"
              :options="languageOptions"
              size="large"
            />
          </a-form-item>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="8">
          <a-form-item label="研究深度">
            <a-slider
              v-model:value="formState.research_depth"
              :min="1"
              :max="5"
              :marks="{ 1: '浅', 3: '中', 5: '深' }"
            />
          </a-form-item>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="8">
          <a-form-item label="LLM 模型提供商">
            <a-select
              v-model:value="formState.llm_provider"
              :options="providerOptions"
              size="large"
              @change="onProviderChange"
            />
          </a-form-item>
        </a-col>
      </a-row>

      <a-row :gutter="24">
        <a-col :xs="24" :sm="12" :lg="8">
          <a-form-item label="快速思考模型">
            <a-select
              v-model:value="formState.shallow_thinker"
              :options="shallowModels"
              show-search
              placeholder="选择模型"
              size="large"
            />
          </a-form-item>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="8">
          <a-form-item label="深度思考模型">
            <a-select
              v-model:value="formState.deep_thinker"
              :options="deepModels"
              show-search
              placeholder="选择模型"
              size="large"
            />
          </a-form-item>
        </a-col>
      </a-row>

      <a-form-item label="分析师团队">
        <a-checkbox-group
          v-model:value="formState.analysts"
          :options="analystOptions"
        />
        <a-tooltip title="选择需要参与分析的分析师类型">
          <InfoCircleOutlined style="color: #999; margin-left: 8px" />
        </a-tooltip>
      </a-form-item>

      <a-form-item>
        <a-button
          type="primary"
          size="large"
          :loading="$props.loading"
          @click="onSubmit"
        >
          <template #icon><ThunderboltOutlined /></template>
          开始分析
        </a-button>
      </a-form-item>
    </a-form>
  </a-card>
</template>
