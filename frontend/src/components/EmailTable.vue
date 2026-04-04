<template>
  <div class="table-shell">
    <table class="table-base">
      <thead>
        <tr>
          <th>主题</th>
          <th>Message ID</th>
          <th>风险</th>
          <th>得分</th>
          <th>状态</th>
          <th>接收邮箱账号</th>
          <th>时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="email in items"
          :key="email.id"
          class="cursor-pointer transition hover:bg-sky-50/60 focus-within:bg-sky-50/60"
          tabindex="0"
          @click="$emit('select', email.id)"
          @keydown.enter="$emit('select', email.id)"
          @keydown.space.prevent="$emit('select', email.id)"
        >
          <td class="max-w-sm">
            <div class="font-medium tracking-[-0.02em] text-slate-950">{{ email.subject || '(No Subject)' }}</div>
          </td>
          <td class="max-w-xs truncate text-slate-500">{{ email.message_id || '--' }}</td>
          <td><RiskBadge :level="email.latest_risk_level" /></td>
          <td>{{ email.latest_score ?? '--' }}</td>
          <td class="text-slate-600">{{ email.status }}</td>
          <td class="text-slate-600">{{ email.mailbox_email_address || '--' }}</td>
          <td class="text-slate-500">{{ formatDateTime(email.created_at) }}</td>
          <td>
            <button
              class="rounded-xl border border-red-200 px-3 py-1.5 text-sm text-red-600 transition hover:bg-red-50"
              type="button"
              @click.stop="$emit('delete', email)"
              @keydown.enter.stop
              @keydown.space.stop
            >
              删除
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import RiskBadge from '@/components/RiskBadge.vue'
import type { EmailListItem } from '@/types/api'
import { formatDateTime } from '@/utils/format'

defineEmits<{
  select: [id: string]
  delete: [email: EmailListItem]
}>()

defineProps<{
  items: EmailListItem[]
}>()
</script>
