import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getHistory,
  getHistoryDetail,
  type HistoryEntry,
  type HistoryDetailResponse,
} from '@/api'

export const useHistoryStore = defineStore('history', () => {
  const entries = ref<HistoryEntry[]>([])
  const total = ref(0)
  const loading = ref(false)
  const currentEntry = ref<HistoryDetailResponse | null>(null)
  const detailLoading = ref(false)

  async function fetchHistory(params: {
    ticker?: string
    limit?: number
    offset?: number
  }) {
    loading.value = true
    try {
      const res = await getHistory(params)
      entries.value = res.entries
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(entryId: string) {
    detailLoading.value = true
    try {
      currentEntry.value = await getHistoryDetail(entryId)
    } finally {
      detailLoading.value = false
    }
  }

  return {
    entries,
    total,
    loading,
    currentEntry,
    detailLoading,
    fetchHistory,
    fetchDetail,
  }
})
