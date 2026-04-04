<template>
  <div class="panel">
    <div class="panel-body flex min-h-48 flex-col items-center justify-center gap-4 text-center">
      <div class="h-10 w-10 animate-spin rounded-full border-2 border-sky-100 border-t-sky-600"></div>
      <div class="text-sm text-slate-500">{{ message }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    message?: string
  }>(),
  {
    message: 'Loading...',
  },
)
</script>
