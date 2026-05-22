<script setup lang="ts">
import { FileTextOutlined, DownloadOutlined } from '@ant-design/icons-vue'
import type { HistoryEntry } from '@/api'

defineProps<{
  entries: HistoryEntry[]
  loading?: boolean
  onView: (id: string) => void
  onDownload: (id: string) => void
}>()
</script>

<template>
  <a-table
    :columns="[
      { title: '股票代码', dataIndex: 'ticker', key: 'ticker' },
      { title: '分析日期', dataIndex: 'analysis_date', key: 'analysis_date' },
      { title: '完成时间', dataIndex: 'completed_at', key: 'completed_at' },
      { title: '操作', key: 'actions' },
    ]"
    :data-source="entries"
    :loading="loading"
    row-key="id"
  >
    <template #bodyCell="{ column, record }">
      <template v-if="column.key === 'completed_at'">
        {{ new Date(record.completed_at).toLocaleString('zh-CN') }}
      </template>
      <template v-if="column.key === 'actions'">
        <a-space>
          <a-button size="small" type="primary" @click="onView(record.id)">
            <template #icon><FileTextOutlined /></template>
            查看
          </a-button>
          <a-button size="small" @click="onDownload(record.id)">
            <template #icon><DownloadOutlined /></template>
            PDF
          </a-button>
        </a-space>
      </template>
    </template>
  </a-table>
</template>
