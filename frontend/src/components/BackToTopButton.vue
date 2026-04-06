<template>
  <Transition name="back-to-top-fade">
    <button
      v-if="visible"
      class="back-to-top"
      type="button"
      :aria-label="label"
      :title="label"
      @click="scrollToTop"
    >
      <span class="back-to-top-icon" aria-hidden="true"></span>
      <span class="back-to-top-text">{{ label }}</span>
    </button>
  </Transition>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    label?: string
    threshold?: number
  }>(),
  {
    label: '返回顶部',
    threshold: 520,
  },
)

const visible = ref(false)

function updateVisibility(): void {
  visible.value = window.scrollY > props.threshold
}

function scrollToTop(): void {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  window.scrollTo({
    top: 0,
    behavior: prefersReducedMotion ? 'auto' : 'smooth',
  })
}

onMounted(() => {
  updateVisibility()
  window.addEventListener('scroll', updateVisibility, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', updateVisibility)
})
</script>

<style scoped>
.back-to-top {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 40;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  border: 1px solid rgba(0, 113, 227, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
  color: #0369a1;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.02em;
  padding: 12px 16px;
  transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease, background-color 180ms ease;
}

.back-to-top:hover {
  border-color: rgba(0, 113, 227, 0.22);
  background: rgba(239, 248, 255, 0.98);
  box-shadow: 0 22px 44px rgba(14, 116, 144, 0.16);
  transform: translateY(-2px);
}

.back-to-top-icon {
  height: 12px;
  width: 12px;
  border-top: 2px solid currentColor;
  border-left: 2px solid currentColor;
  transform: rotate(45deg) translate(1px, 1px);
}

.back-to-top-text {
  line-height: 1;
}

.back-to-top-fade-enter-active,
.back-to-top-fade-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}

.back-to-top-fade-enter-from,
.back-to-top-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 768px) {
  .back-to-top {
    right: 16px;
    bottom: 16px;
    padding: 12px 14px;
  }

  .back-to-top-text {
    display: none;
  }
}
</style>
