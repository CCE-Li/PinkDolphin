<template>
  <div class="panel">
    <div class="panel-body">
      <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">{{ title }}</p>
      <div class="mt-4 flex items-end justify-between gap-4">
        <div class="text-4xl font-semibold tracking-[-0.06em] text-slate-950">{{ value }}</div>
        <div class="rounded-full px-3 py-1 text-xs font-semibold" :class="toneClass">{{ subtitle }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  title: string
  value: string | number
  subtitle: string
  tone?: 'neutral' | 'success' | 'warning' | 'danger'
}>()

const toneClass = computed(() => {
  if (props.tone === 'success') return 'bg-sky-50 text-sky-700'
  if (props.tone === 'warning') return 'bg-amber-50 text-amber-700'
  if (props.tone === 'danger') return 'bg-red-50 text-red-700'
  return 'bg-slate-100 text-slate-600'
})
</script>
