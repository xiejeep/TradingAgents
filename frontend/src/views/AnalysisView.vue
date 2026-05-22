<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAnalysisStore } from '@/stores/analysis'
import AnalysisForm from '@/components/AnalysisForm.vue'
import StreamProgress from '@/components/StreamProgress.vue'
import type { AnalysisConfig } from '@/api'

const router = useRouter()
const store = useAnalysisStore()
const loading = ref(false)

async function handleSubmit(config: AnalysisConfig) {
  loading.value = true
  try {
    const taskId = await store.startAnalysis(config)
    store.connectStream(taskId).then(() => {
      loading.value = false
      message.success('分析完成！')
    }).catch((err: any) => {
      loading.value = false
      message.error('分析失败: ' + err.message)
    })
  } catch (err: any) {
    loading.value = false
    message.error('启动分析失败: ' + err.message)
  }
}

function handleViewReport() {
  if (store.taskId) {
    router.push({ name: 'report', params: { taskId: store.taskId } })
  }
}
</script>

<template>
  <div class="analysis-page">
    <div v-if="store.status === 'idle'">
      <h3 style="margin-bottom: 24px">启动新分析</h3>
      <AnalysisForm :loading="loading" @submit="handleSubmit" />
    </div>

    <div v-else-if="store.status === 'running'">
      <StreamProgress />
    </div>

    <div v-else-if="store.status === 'completed'">
      <a-result
        status="success"
        title="分析完成"
        :sub-title="store.decision ? `决策: ${store.decision}` : ''"
      >
        <template #extra>
          <a-space>
            <a-button type="primary" @click="handleViewReport">查看报告</a-button>
            <a-button @click="store.reset()">新分析</a-button>
          </a-space>
        </template>
      </a-result>
      <StreamProgress :compact="true" />
    </div>

    <div v-else-if="store.status === 'error'">
      <a-result
        status="error"
        title="分析失败"
        :sub-title="store.error"
      >
        <template #extra>
          <a-button type="primary" @click="store.reset()">重试</a-button>
        </template>
      </a-result>
    </div>

    <div v-else>
      <a-skeleton active />
    </div>
  </div>
</template>

<style scoped>
.analysis-page {
  max-width: 1200px;
}
</style>
