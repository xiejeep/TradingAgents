<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { ref, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  StockOutlined,
  HistoryOutlined,
  SettingOutlined,
  CopyOutlined,
} from '@ant-design/icons-vue'
import { getLicenseStatus, activateLicense, type LicenseStatus } from '@/api'

const router = useRouter()
const route = useRoute()

const selectedKeys = ref<string[]>([route.path])
const collapsed = ref(false)

const license = ref<LicenseStatus | null>(null)
const activationCode = ref('')
const activating = ref(false)
const activationVisible = ref(false)

onMounted(async () => {
  try {
    license.value = await getLicenseStatus()
    activationVisible.value = !license.value.activated
  } catch {
    // server not ready yet
  }
})

async function doActivate() {
  if (!activationCode.value.trim()) return
  activating.value = true
  try {
    await activateLicense(activationCode.value.trim())
    license.value = await getLicenseStatus()
    activationVisible.value = false
    message.success('激活成功！')
  } catch (err: any) {
    message.error('激活码无效')
  } finally {
    activating.value = false
  }
}

async function copyMachineCode() {
  if (license.value?.machine_code) {
    await navigator.clipboard.writeText(license.value.machine_code)
    message.success('已复制机器码')
  }
}

watch(
  () => route.path,
  (path) => {
    selectedKeys.value = [path]
  }
)

function onMenuClick(info: { key: string }) {
  router.push(info.key)
}
</script>

<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider
      v-model:collapsed="collapsed"
      collapsible
      theme="light"
      style="border-right: 1px solid #f0f0f0"
    >
      <div class="logo">
        <span class="logo-icon">{{ collapsed ? '&#x1F4C8;' : '&#x1F4C8;' }}</span>
        <span v-if="!collapsed" class="logo-text">TradingAgents</span>
      </div>
      <a-menu
        mode="inline"
        :selected-keys="selectedKeys"
        @click="onMenuClick"
      >
        <a-menu-item key="/">
          <template #icon><StockOutlined /></template>
          <span>股票分析</span>
        </a-menu-item>
        <a-menu-item key="/history">
          <template #icon><HistoryOutlined /></template>
          <span>历史记录</span>
        </a-menu-item>
        <a-menu-item key="/settings">
          <template #icon><SettingOutlined /></template>
          <span>API 设置</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <a-layout-header class="header">
        <h2 class="header-title">
          AI 驱动的多智能体股票分析平台
        </h2>
      </a-layout-header>
      <a-layout-content class="content">
        <router-view />
      </a-layout-content>
    </a-layout>

    <a-modal
      :open="activationVisible"
      :closable="false"
      :mask-closable="false"
      title="软件激活"
      :footer="null"
      width="480px"
    >
      <a-result
        status="warning"
        title="未激活"
        sub-title="请输入卖家提供的激活码以解锁全部功能"
      >
        <template #extra>
          <a-card size="small" style="text-align: left; margin-bottom: 16px">
            <div style="display: flex; align-items: center; gap: 8px">
              <p style="margin: 0; font-family: monospace; font-size: 14px; word-break: break-all; flex: 1">
                机器码：{{ license?.machine_code || '加载中...' }}
              </p>
              <a-button size="small" @click="copyMachineCode">
                <template #icon><CopyOutlined /></template>
                复制
              </a-button>
            </div>
          </a-card>
          <a-space direction="vertical" style="width: 100%">
            <a-input
              v-model:value="activationCode"
              placeholder="输入激活码"
              size="large"
              style="font-family: monospace; text-transform: uppercase"
              @press-enter="doActivate"
            />
            <a-button
              type="primary"
              size="large"
              block
              :loading="activating"
              @click="doActivate"
            >
              激活
            </a-button>
          </a-space>
        </template>
      </a-result>
    </a-modal>
  </a-layout>
</template>

<style>
.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 64px;
  gap: 8px;
  border-bottom: 1px solid #f0f0f0;
  overflow: hidden;
}
.logo-icon {
  font-size: 24px;
  flex-shrink: 0;
}
.logo-text {
  font-size: 16px;
  font-weight: 700;
  background: linear-gradient(135deg, #1677ff, #52c41a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  white-space: nowrap;
}
.header {
  background: #fff;
  padding: 0 24px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
  line-height: 64px;
  height: 64px;
}
.header-title {
  margin: 0;
  font-size: 18px;
}
.content {
  margin: 24px;
  padding: 0;
  background: transparent;
  min-height: 280px;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
