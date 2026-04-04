<template>
  <div class="h-56 w-full">
    <svg viewBox="0 0 420 224" class="h-full w-full" preserveAspectRatio="none" role="img" aria-label="平台数量柱状图">
      <g>
        <line
          v-for="tick in yTicks"
          :key="`grid-${tick.value}`"
          :x1="padding.left"
          :x2="width - padding.right"
          :y1="tick.y"
          :y2="tick.y"
          stroke="#e2e8f0"
          stroke-dasharray="4 4"
          stroke-width="1"
        />
      </g>

      <g>
        <line
          :x1="padding.left"
          :x2="padding.left"
          :y1="padding.top"
          :y2="height - padding.bottom"
          stroke="#94a3b8"
          stroke-width="1.5"
        />
        <line
          :x1="padding.left"
          :x2="width - padding.right"
          :y1="height - padding.bottom"
          :y2="height - padding.bottom"
          stroke="#94a3b8"
          stroke-width="1.5"
        />
      </g>

      <g fill="#94a3b8" font-size="11" text-anchor="end">
        <text
          v-for="tick in yTicks"
          :key="`label-${tick.value}`"
          :x="padding.left - 10"
          :y="tick.y + 4"
        >
          {{ tick.label }}
        </text>
      </g>

      <g v-for="bar in bars" :key="bar.name">
        <rect
          :x="bar.x"
          :y="bar.y"
          :width="bar.width"
          :height="bar.height"
          rx="8"
          ry="8"
          fill="rgba(186, 230, 253, 0.12)"
          stroke="#7dd3fc"
          stroke-width="2"
        />
        <text
          :x="bar.x + bar.width / 2"
          :y="bar.y - 8"
          fill="#475569"
          font-size="12"
          font-weight="600"
          text-anchor="middle"
        >
          {{ bar.value }}
        </text>
        <text
          :x="bar.x + bar.width / 2"
          :y="height - padding.bottom + 22"
          fill="#64748b"
          font-size="12"
          text-anchor="middle"
        >
          {{ bar.name }}
        </text>
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface DataItem {
  name: string
  value: number
}

const props = defineProps<{
  data: DataItem[]
}>()

const width = 420
const height = 224
const padding = {
  top: 18,
  right: 18,
  bottom: 42,
  left: 42,
}

const maxValue = computed(() => Math.max(...props.data.map((item) => item.value), 5))
const yTicks = computed(() => {
  const segments = 5
  return Array.from({ length: segments + 1 }, (_, index) => {
    const value = segments - index
    const y = padding.top + ((height - padding.top - padding.bottom) / segments) * index
    return {
      value,
      y,
      label: String(value),
    }
  })
})

const bars = computed(() => {
  const plotWidth = width - padding.left - padding.right
  const plotHeight = height - padding.top - padding.bottom
  const count = Math.max(props.data.length, 1)
  const slotWidth = plotWidth / count
  const barWidth = Math.min(42, slotWidth * 0.38)

  return props.data.map((item, index) => {
    const ratio = item.value / maxValue.value
    const heightValue = Math.max(plotHeight * ratio, 6)
    const x = padding.left + slotWidth * index + (slotWidth - barWidth) / 2
    const y = height - padding.bottom - heightValue

    return {
      ...item,
      x,
      y,
      width: barWidth,
      height: heightValue,
    }
  })
})
</script>
