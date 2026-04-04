<template>
  <div class="panel border-red-200 bg-red-50/50">
    <div class="panel-body">
      <p class="text-lg font-medium tracking-[-0.03em] text-red-700">请求失败</p>
      <p class="mt-2 text-sm leading-7 text-slate-600">{{ message }}</p>
      <button v-if="retryable" class="btn-secondary mt-4" type="button" @click="$emit('retry')">重试</button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineEmits<{
  retry: []
}>()

withDefaults(
  defineProps<{
    message: string
    retryable?: boolean
  }>(),
  {
    retryable: true,
  },
)
</script>
