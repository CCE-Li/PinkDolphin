<template>
  <form class="grid gap-4 md:grid-cols-2" @submit.prevent="submit">
    <div>
      <label class="mb-2 block text-sm font-medium text-slate-600">规则名称</label>
      <input v-model="form.name" class="field" :disabled="disabled || isEdit" required />
    </div>
    <div>
      <label class="mb-2 block text-sm font-medium text-slate-600">条件类型</label>
      <select v-model="form.condition_type" class="field" :disabled="disabled || isEdit">
        <option value="subject_contains">subject_contains</option>
        <option value="body_contains">body_contains</option>
        <option value="sender_domain">sender_domain</option>
        <option value="url_contains">url_contains</option>
      </select>
    </div>
    <div class="md:col-span-2">
      <label class="mb-2 block text-sm font-medium text-slate-600">描述</label>
      <textarea v-model="form.description" class="field min-h-24" />
    </div>
    <div>
      <label class="mb-2 block text-sm font-medium text-slate-600">条件值</label>
      <input v-model="form.condition_value" class="field" :disabled="disabled" required />
    </div>
    <div>
      <label class="mb-2 block text-sm font-medium text-slate-600">分数修正</label>
      <input v-model.number="form.score_modifier" class="field" type="number" :disabled="disabled" required />
    </div>
    <div>
      <label class="mb-2 block text-sm font-medium text-slate-600">严重级别</label>
      <select v-model="form.severity" class="field" :disabled="disabled">
        <option value="low">low</option>
        <option value="medium">medium</option>
        <option value="high">high</option>
        <option value="critical">critical</option>
      </select>
    </div>
    <div>
      <label class="mb-2 block text-sm font-medium text-slate-600">覆盖动作</label>
      <select v-model="form.override_action" class="field" :disabled="disabled">
        <option value="">none</option>
        <option value="allow">allow</option>
        <option value="banner_warning">banner_warning</option>
        <option value="move_to_spam">move_to_spam</option>
        <option value="manual_review">manual_review</option>
        <option value="quarantine">quarantine</option>
      </select>
    </div>
    <label class="inline-flex items-center gap-2 text-sm text-slate-600">
      <input v-model="form.is_active" type="checkbox" />
      启用规则
    </label>
    <div class="md:col-span-2 flex justify-end gap-3">
      <button class="btn-secondary" type="button" @click="$emit('cancel')">取消</button>
      <button class="btn-primary" type="submit" :disabled="disabled">{{ submitLabel }}</button>
    </div>
  </form>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'

import type { RuleItem, RulePayload } from '@/types/api'

const emit = defineEmits<{
  submit: [payload: RulePayload]
  cancel: []
}>()

const props = withDefaults(
  defineProps<{
    initialValue?: RuleItem | null
    disabled?: boolean
    submitLabel?: string
  }>(),
  {
    initialValue: null,
    disabled: false,
    submitLabel: '保存规则',
  },
)

const form = reactive<RulePayload>({
  name: '',
  description: '',
  is_active: true,
  condition_type: 'subject_contains',
  condition_value: '',
  score_modifier: 0,
  severity: 'medium',
  override_action: '',
})

const isEdit = computed(() => Boolean(props.initialValue))

watch(
  () => props.initialValue,
  (value) => {
    if (!value) {
      form.name = ''
      form.description = ''
      form.is_active = true
      form.condition_type = 'subject_contains'
      form.condition_value = ''
      form.score_modifier = 0
      form.severity = 'medium'
      form.override_action = ''
      return
    }
    form.name = value.name
    form.description = value.description
    form.is_active = value.is_active
    form.condition_type = value.condition_type
    form.condition_value = value.condition_value
    form.score_modifier = value.score_modifier
    form.severity = value.severity
    form.override_action = value.override_action ?? ''
  },
  { immediate: true },
)

function submit(): void {
  emit('submit', {
    ...form,
    description: form.description || null,
    override_action: form.override_action || null,
  })
}
</script>
