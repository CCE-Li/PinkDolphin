<template>
  <span class="inline-flex rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.12em]" :class="classes">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ level: string | null | undefined }>()

const label = computed(() => props.level ?? 'unknown')
const classes = computed(() => {
  switch (props.level) {
    case 'critical':
      return 'bg-red-100 text-red-700'
    case 'high':
      return 'bg-amber-100 text-amber-700'
    case 'medium':
      return 'bg-blue-100 text-blue-700'
    case 'low':
      return 'bg-sky-100 text-sky-700'
    default:
      return 'bg-slate-100 text-slate-600'
  }
})
</script>
