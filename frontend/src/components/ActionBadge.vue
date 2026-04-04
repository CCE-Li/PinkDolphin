<template>
  <span class="inline-flex rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.08em]" :class="classes">
    {{ action || 'n/a' }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ action: string | null | undefined }>()

const classes = computed(() => {
  switch (props.action) {
    case 'quarantine':
      return 'bg-red-100 text-red-700'
    case 'move_to_spam':
      return 'bg-amber-100 text-amber-700'
    case 'manual_review':
      return 'bg-blue-100 text-blue-700'
    case 'banner_warning':
      return 'bg-sky-100 text-sky-700'
    case 'allow':
      return 'bg-cyan-100 text-cyan-700'
    default:
      return 'bg-slate-100 text-slate-600'
  }
})
</script>
