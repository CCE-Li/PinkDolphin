<template>
  <div class="rounded-[24px] border border-slate-200/80 bg-white/90 p-5 shadow-[0_12px_30px_rgba(16,24,40,0.04)]">
    <div class="flex items-center justify-between gap-3">
      <div>
        <h4 class="text-sm font-semibold tracking-[-0.02em] text-slate-950">{{ result.analyzer_name }}</h4>
        <p class="mt-1 text-xs leading-6 text-slate-500">{{ result.summary }}</p>
      </div>
      <div class="flex items-center gap-2">
        <RiskBadge :level="result.severity" />
        <div class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-sm text-slate-700">Score {{ result.score }}</div>
      </div>
    </div>
    <div class="mt-4 grid gap-4 lg:grid-cols-2">
      <div>
        <p class="text-[11px] font-semibold uppercase tracking-[0.16em] text-sky-600">Signals</p>
        <div class="mt-2 flex flex-wrap gap-2">
          <span
            v-for="signal in result.signals"
            :key="signal"
            class="rounded-full bg-sky-50 px-3 py-1 text-xs text-sky-700"
          >
            {{ signal }}
          </span>
          <span v-if="!result.signals.length" class="text-sm text-slate-500">No signals</span>
        </div>
      </div>
      <div>
        <p class="text-[11px] font-semibold uppercase tracking-[0.16em] text-sky-600">Evidence</p>
        <pre class="mt-2 max-h-48 overflow-auto rounded-2xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">{{ evidenceText }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import RiskBadge from '@/components/RiskBadge.vue'
import type { AnalyzerResultItem } from '@/types/api'

const props = defineProps<{
  result: AnalyzerResultItem
}>()

const evidenceText = computed(() => JSON.stringify(props.result.evidence, null, 2))
</script>
