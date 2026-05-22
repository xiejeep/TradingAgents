<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { ref, watch } from 'vue'
import {
  StockOutlined,
  HistoryOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()

const selectedKeys = ref<string[]>([route.path])
const collapsed = ref(false)

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
