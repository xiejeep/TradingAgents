<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  SearchOutlined,
  ReloadOutlined,
  FileTextOutlined,
  DownloadOutlined,
} from '@ant-design/icons-vue'
import { useHistoryStore } from '@/stores/history'
import { getHistoryPdfUrl } from '@/api'
import HistoryTable from '@/components/HistoryTable.vue'

const router = useRouter()
const store = useHistoryStore()

const tickerFilter = ref<string>('')
const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
})

async function loadHistory() {
  await store.fetchHistory({
    ticker: tickerFilter.value || undefined,
    limit: pagination.value.pageSize,
    offset: (pagination.value.current - 1) * pagination.value.pageSize,
  })
  pagination.value.total = store.total
}

function handleSearch() {
  pagination.value.current = 1
  loadHistory()
}

function handleReset() {
  tickerFilter.value = ''
  pagination.value.current = 1
  loadHistory()
}

function handleViewReport(entryId: string) {
  router.push({ name: 'report', params: { taskId: entryId } })
}

function handleDownloadPdf(entryId: string) {
  window.open(getHistoryPdfUrl(entryId), '_blank')
}

function handlePageChange(page: number, pageSize: number) {
  pagination.value.current = page
  pagination.value.pageSize = pageSize
  loadHistory()
}

onMounted(() => {
  loadHistory()
})
</script>

<template>
  <div class="history-page" style="max-width: 1200px">
    <h3 style="margin-bottom: 16px">历史分析记录</h3>

    <a-card style="margin-bottom: 16px">
      <a-space>
        <a-input-search
          v-model:value="tickerFilter"
          placeholder="按股票代码筛选"
          style="width: 280px"
          @search="handleSearch"
        />
        <a-button @click="handleReset">
          <template #icon><ReloadOutlined /></template>
          重置
        </a-button>
      </a-space>
    </a-card>

    <a-card>
      <a-table
        :columns="[
          { title: '股票代码', dataIndex: 'ticker', key: 'ticker', width: 120 },
          { title: '分析日期', dataIndex: 'analysis_date', key: 'analysis_date', width: 130 },
          { title: '完成时间', dataIndex: 'completed_at', key: 'completed_at', width: 180 },
          { title: '决策/评级', key: 'decision', width: 220 },
          { title: '操作', key: 'actions', width: 200 },
        ]"
        :data-source="store.entries"
        :loading="store.loading"
        :pagination="pagination"
        row-key="id"
        @change="(pg: any) => handlePageChange(pg.current, pg.pageSize)"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'completed_at'">
            {{ new Date(record.completed_at).toLocaleString('zh-CN') }}
          </template>
          <template v-if="column.key === 'decision'">
            <a-space>
              <a-tag
                v-if="record.rating"
                :color="
                  record.rating.includes('买入') || record.rating.includes('Buy') ? 'green' :
                  record.rating.includes('卖出') || record.rating.includes('Sell') ? 'red' :
                  'blue'
                "
              >
                {{ record.rating }}
              </a-tag>
              <span style="font-size: 13px; color: #666">{{ record.decision?.slice(0, 30) }}</span>
            </a-space>
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button size="small" type="primary" @click="handleViewReport(record.id)">
                <template #icon><FileTextOutlined /></template>
                查看
              </a-button>
              <a-button size="small" @click="handleDownloadPdf(record.id)">
                <template #icon><DownloadOutlined /></template>
                PDF
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>

      <a-empty v-if="!store.loading && store.entries.length === 0" description="暂无历史记录" />
    </a-card>
  </div>
</template>
