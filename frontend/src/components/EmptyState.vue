<template>
  <div class="panel">
    <div class="panel-body py-12 text-center">
      <p class="text-lg font-medium tracking-[-0.03em] text-slate-950">{{ title }}</p>
      <p class="mt-2 text-sm leading-7 text-slate-500">{{ description }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description: string
}>()
</script>
