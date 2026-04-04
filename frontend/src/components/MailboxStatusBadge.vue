<template>
  <span class="inline-flex rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.08em]" :class="classes">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string | null | undefined }>()

const label = computed(() => props.status ?? 'unknown')
const classes = computed(() => {
  switch (props.status) {
    case 'listening':
      return 'bg-cyan-100 text-cyan-700'
    case 'idle':
      return 'bg-sky-100 text-sky-700'
    case 'error':
      return 'bg-red-100 text-red-700'
    case 'disabled':
      return 'bg-slate-200 text-slate-600'
    default:
      return 'bg-slate-100 text-slate-600'
  }
})
</script>

