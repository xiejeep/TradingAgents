import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  createAnalysis,
  createWebSocket,
  type AnalysisConfig,
  type StreamMessage,
} from '@/api'

export const useAnalysisStore = defineStore('analysis', () => {
  const taskId = ref<string | null>(null)
  const status = ref<'idle' | 'running' | 'completed' | 'error'>('idle')
  const error = ref<string | null>(null)
  const messages = ref<StreamMessage[]>([])
  const ws = ref<WebSocket | null>(null)

  const reportSections = ref<Record<string, string>>({})
  const debateStates = ref<Record<string, any>>({})
  const agentMessages = ref<Array<{ agent_type: string; content: string; timestamp: string }>>([])
  const toolCalls = ref<Array<{ name: string; args: Record<string, string>; timestamp: string }>>([])
  const decision = ref<string>('')

  function reset() {
    taskId.value = null
    status.value = 'idle'
    error.value = null
    messages.value = []
    reportSections.value = {}
    debateStates.value = {}
    agentMessages.value = []
    toolCalls.value = []
    decision.value = ''
    disconnect()
  }

  function disconnect() {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }

  async function startAnalysis(config: AnalysisConfig): Promise<string> {
    reset()
    status.value = 'running'

    const result = await createAnalysis(config)
    taskId.value = result.task_id
    return result.task_id
  }

  function connectStream(tid: string): Promise<void> {
    disconnect()
    taskId.value = tid

    const socket = createWebSocket(tid)
    ws.value = socket

    return new Promise<void>((resolve, reject) => {
      socket.onopen = () => {
        status.value = 'running'
      }

      socket.onmessage = (event) => {
        try {
          const msg: StreamMessage = JSON.parse(event.data)
          messages.value.push(msg)

          switch (msg.type) {
            case 'report_update':
              if (msg.data?.section && msg.data?.content) {
                reportSections.value[msg.data.section] = msg.data.content
              }
              break
            case 'debate_update':
              if (msg.data?.key && msg.data?.state) {
                debateStates.value[msg.data.key] = msg.data.state
              }
              break
            case 'decision_update':
              if (msg.data?.key === 'final_trade_decision' && msg.data?.content) {
                decision.value = msg.data.content
              }
              break
            case 'agent_message':
              if (msg.data) {
                agentMessages.value.push({
                  agent_type: msg.data.agent_type,
                  content: msg.data.content,
                  timestamp: msg.data.timestamp,
                })
              }
              break
            case 'tool_call':
              if (msg.data) {
                toolCalls.value.push({
                  name: msg.data.name,
                  args: msg.data.args,
                  timestamp: msg.data.timestamp,
                })
              }
              break
            case 'complete':
              status.value = 'completed'
              if (msg.data?.decision) {
                decision.value = msg.data.decision
              }
              disconnect()
              resolve()
              break
            case 'error':
              status.value = 'error'
              error.value = msg.data?.message || '未知错误'
              disconnect()
              reject(new Error(msg.data?.message))
              break
          }
        } catch {
          // ignore parse errors
        }
      }

      socket.onerror = () => {
        status.value = 'error'
        error.value = 'WebSocket 连接失败'
        reject(new Error('WebSocket 连接失败'))
      }

      socket.onclose = () => {
        if (ws.value) {
          ws.value = null
        }
      }
    })
  }

  return {
    taskId,
    status,
    error,
    messages,
    reportSections,
    debateStates,
    agentMessages,
    toolCalls,
    decision,
    reset,
    disconnect,
    startAnalysis,
    connectStream,
  }
})
