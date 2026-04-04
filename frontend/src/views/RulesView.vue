<template>
  <section class="space-y-6">
    <div class="flex justify-end">
      <button class="btn-primary" type="button" @click="openCreate">新增规则</button>
    </div>
    <LoadingState v-if="loading" message="正在加载规则..." />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <div v-else class="grid gap-6 xl:grid-cols-[1.1fr,0.9fr]">
      <div class="table-shell">
        <table class="table-base">
          <thead>
            <tr>
              <th>规则</th>
              <th>条件</th>
              <th>严重级别</th>
              <th>分数修正</th>
              <th>状态</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rule in rules" :key="rule.id">
              <td>
                <div class="font-medium text-slate-900">{{ rule.name }}</div>
                <div class="mt-1 text-xs text-slate-500">{{ rule.description || '--' }}</div>
              </td>
              <td class="text-slate-600">{{ rule.condition_type }} = {{ rule.condition_value }}</td>
              <td><RiskBadge :level="rule.severity" /></td>
              <td>{{ rule.score_modifier }}</td>
              <td>{{ rule.is_active ? 'enabled' : 'disabled' }}</td>
              <td><button class="btn-secondary" type="button" @click="openEdit(rule)">编辑</button></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="panel">
        <div class="panel-header">
          <h2 class="text-lg font-semibold text-slate-900">{{ editingRule ? '编辑规则' : '新增规则' }}</h2>
        </div>
        <div class="panel-body">
          <RuleForm
            :initial-value="editingRule"
            :submit-label="editingRule ? '更新规则' : '创建规则'"
            :disabled="submitting"
            @submit="saveRule"
            @cancel="resetForm"
          />
          <p v-if="formMessage" class="mt-4 text-sm text-sky-600">{{ formMessage }}</p>
          <p v-if="formError" class="mt-4 text-sm text-red-300">{{ formError }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { rulesApi } from '@/api/modules/rules'
import ErrorState from '@/components/ErrorState.vue'
import LoadingState from '@/components/LoadingState.vue'
import RiskBadge from '@/components/RiskBadge.vue'
import RuleForm from '@/components/RuleForm.vue'
import type { RuleItem, RulePayload } from '@/types/api'

const loading = ref(true)
const error = ref<string | null>(null)
const rules = ref<RuleItem[]>([])
const editingRule = ref<RuleItem | null>(null)
const submitting = ref(false)
const formMessage = ref<string | null>(null)
const formError = ref<string | null>(null)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    rules.value = await rulesApi.list()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load rules'
  } finally {
    loading.value = false
  }
}

function openCreate(): void {
  editingRule.value = null
  formMessage.value = null
  formError.value = null
}

function openEdit(rule: RuleItem): void {
  editingRule.value = rule
  formMessage.value = null
  formError.value = null
}

function resetForm(): void {
  editingRule.value = null
}

async function saveRule(payload: RulePayload): Promise<void> {
  submitting.value = true
  formError.value = null
  formMessage.value = null
  try {
    if (editingRule.value) {
      await rulesApi.update(editingRule.value.id, payload)
      formMessage.value = '规则已更新'
    } else {
      await rulesApi.create(payload)
      formMessage.value = '规则已创建'
    }
    editingRule.value = null
    await load()
  } catch (err) {
    formError.value = err instanceof Error ? err.message : 'Save failed'
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>
