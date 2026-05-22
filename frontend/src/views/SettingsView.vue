<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  SaveOutlined,
  CheckCircleFilled,
  CloseCircleFilled,
  EyeInvisibleOutlined,
  EyeOutlined,
} from '@ant-design/icons-vue'
import { getSettings, saveSettings, type KeyStatus } from '@/api'

const loading = ref(false)
const saving = ref(false)
const keyStatus = ref<KeyStatus | null>(null)
const editingKeys = ref<Record<string, string>>({})
const showKeys = ref<Record<string, boolean>>({})

async function loadSettings() {
  loading.value = true
  try {
    keyStatus.value = await getSettings()
  } catch (err: any) {
    message.error('加载设置失败: ' + err.message)
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    await saveSettings(editingKeys.value)
    message.success('设置保存成功')
    editingKeys.value = {}
    await loadSettings()
  } catch (err: any) {
    message.error('保存失败: ' + err.message)
  } finally {
    saving.value = false
  }
}

function startEdit(envVar: string) {
  editingKeys.value[envVar] = editingKeys.value[envVar] ?? ''
}

function toggleShow(envVar: string) {
  showKeys.value[envVar] = !showKeys.value[envVar]
}

function hasEdits(): boolean {
  return Object.values(editingKeys.value).some((v) => v.trim() !== '')
}

onMounted(loadSettings)
</script>

<template>
  <div class="settings-page" style="max-width: 900px">
    <h3 style="margin-bottom: 16px">API 密钥设置</h3>

    <a-spin :spinning="loading">
      <a-alert
        message="密钥仅保存在服务器的 .env 文件中，不会上传到云端。"
        type="info"
        show-icon
        style="margin-bottom: 24px"
      />

      <a-card title="LLM 模型服务商" size="small" style="margin-bottom: 24px">
        <a-row v-if="keyStatus" :gutter="[16, 16]">
          <a-col
            v-for="(info, provider) in keyStatus.llm"
            :key="provider"
            :span="8"
          >
            <a-card size="small" :hoverable="true" style="height: 100%">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px">
                <strong style="text-transform: capitalize">{{ provider }}</strong>
                <a-tag v-if="info.is_set" color="success">
                  <CheckCircleFilled /> 已配置
                </a-tag>
                <a-tag v-else color="error">
                  <CloseCircleFilled /> 未配置
                </a-tag>
              </div>

              <div v-if="info.is_set && !editingKeys[info.env_var]" style="font-size: 12px; color: #999">
                {{ info.masked }}
                <a-button
                  type="link"
                  size="small"
                  style="padding: 0; margin-left: 4px"
                  @click="startEdit(info.env_var)"
                >
                  修改
                </a-button>
              </div>

              <div v-else>
                <a-input-group compact style="width: 100%">
                  <a-input
                    v-model:value="editingKeys[info.env_var]"
                    :placeholder="info.is_set ? '输入新密钥' : '输入密钥'"
                    :type="showKeys[info.env_var] ? 'text' : 'password'"
                    size="small"
                    @focus="startEdit(info.env_var)"
                  />
                  <a-button
                    size="small"
                    @click="toggleShow(info.env_var)"
                  >
                    <EyeOutlined v-if="!showKeys[info.env_var]" />
                    <EyeInvisibleOutlined v-else />
                  </a-button>
                </a-input-group>
              </div>
            </a-card>
          </a-col>
        </a-row>
      </a-card>

      <a-card title="数据服务" size="small" style="margin-bottom: 24px">
        <a-row v-if="keyStatus" :gutter="[16, 16]">
          <a-col
            v-for="(info, vendor) in keyStatus.data"
            :key="vendor"
            :span="8"
          >
            <a-card size="small" :hoverable="true" style="height: 100%">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px">
                <strong style="text-transform: capitalize">{{ vendor.replace('_', ' ') }}</strong>
                <a-tag v-if="info.is_set" color="success">
                  <CheckCircleFilled /> 已配置
                </a-tag>
                <a-tag v-else color="error">
                  <CloseCircleFilled /> 未配置
                </a-tag>
              </div>

              <div v-if="info.is_set && !editingKeys[info.env_var]" style="font-size: 12px; color: #999">
                {{ info.masked }}
                <a-button
                  type="link"
                  size="small"
                  style="padding: 0; margin-left: 4px"
                  @click="startEdit(info.env_var)"
                >
                  修改
                </a-button>
              </div>

              <div v-else>
                <a-input-group compact style="width: 100%">
                  <a-input
                    v-model:value="editingKeys[info.env_var]"
                    :placeholder="info.is_set ? '输入新密钥' : '输入密钥'"
                    :type="showKeys[info.env_var] ? 'text' : 'password'"
                    size="small"
                    @focus="startEdit(info.env_var)"
                  />
                  <a-button
                    size="small"
                    @click="toggleShow(info.env_var)"
                  >
                    <EyeOutlined v-if="!showKeys[info.env_var]" />
                    <EyeInvisibleOutlined v-else />
                  </a-button>
                </a-input-group>
              </div>
            </a-card>
          </a-col>
        </a-row>
      </a-card>

      <div v-if="hasEdits()" style="text-align: center; margin-top: 24px">
        <a-button
          type="primary"
          size="large"
          :loading="saving"
          @click="handleSave"
        >
          <template #icon><SaveOutlined /></template>
          保存所有更改
        </a-button>
      </div>
    </a-spin>
  </div>
</template>
