<template>
  <header class="sticky top-0 z-20 border-b border-slate-200/60 bg-[rgba(245,247,251,0.72)] px-6 py-4 backdrop-blur">
    <div class="view-shell flex items-center justify-between gap-4">
      <div>
        <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">Personal Security</p>
        <h2 class="mt-1 text-lg font-semibold tracking-[-0.03em] text-slate-950">个人邮箱风险监测</h2>
      </div>
      <div class="flex items-center gap-3">
        <div
          class="rounded-full px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.14em]"
          :class="systemStore.backendAvailable ? 'bg-sky-50 text-sky-700' : 'bg-red-50 text-red-600'"
        >
          {{ systemStore.backendAvailable ? 'Backend Online' : 'Backend Offline' }}
        </div>
        <div class="flex h-10 items-center rounded-full border border-slate-200/80 bg-white/90 px-4 text-sm text-slate-800 shadow-[0_8px_20px_rgba(16,24,40,0.04)]">
          <span class="text-slate-500">当前账号:</span>
          <span class="ml-2 font-medium">{{ authStore.username }}</span>
        </div>

        <div ref="menuRef" class="relative">
          <button
            class="flex h-10 items-center rounded-full border border-slate-200/80 bg-white/90 px-4 text-sm text-slate-800 shadow-[0_8px_20px_rgba(16,24,40,0.04)] transition hover:bg-slate-50"
            type="button"
            @click="toggleMenu"
          >
            更多
          </button>
          <div
            v-if="menuOpen"
            class="absolute right-0 top-[calc(100%+0.5rem)] z-30 w-48 rounded-2xl border border-slate-200 bg-white p-2 shadow-[0_16px_40px_rgba(16,24,40,0.12)]"
          >
            <button class="block w-full rounded-xl px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50" type="button" @click="openPasswordDialog">
              修改账号密码
            </button>
            <button class="block w-full rounded-xl px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50" type="button" @click="logout">
              退出
            </button>
          </div>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="dialogOpen" class="fixed inset-0 z-[100] bg-slate-950/25">
        <div class="fixed left-1/2 top-1/2 w-full max-w-md -translate-x-1/2 -translate-y-1/2 px-4">
          <div class="rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_20px_60px_rgba(16,24,40,0.18)]">
            <div class="flex items-start justify-between gap-4">
              <div>
                <h3 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">修改账号密码</h3>
                <p class="mt-2 text-sm leading-6 text-slate-500">修改后，下次登录请使用新的账号和密码。</p>
              </div>
              <button class="btn-secondary" type="button" @click="closeDialog">关闭</button>
            </div>

            <form class="mt-6 space-y-4" @submit.prevent="submitPasswordChange">
              <div>
                <label class="mb-2 block text-sm font-medium text-slate-600">当前账号</label>
                <input v-model="form.current_username" class="field" autocomplete="username" />
              </div>
              <div>
                <label class="mb-2 block text-sm font-medium text-slate-600">当前密码</label>
                <input v-model="form.current_password" class="field" type="password" autocomplete="current-password" />
              </div>
              <div>
                <label class="mb-2 block text-sm font-medium text-slate-600">新账号</label>
                <input v-model="form.new_username" class="field" autocomplete="username" />
              </div>
              <div>
                <label class="mb-2 block text-sm font-medium text-slate-600">新密码</label>
                <input v-model="form.new_password" class="field" type="password" autocomplete="new-password" />
              </div>

              <p v-if="message" class="text-sm text-sky-600">{{ message }}</p>
              <p v-if="authStore.error" class="text-sm text-red-600">{{ authStore.error }}</p>

              <div class="flex justify-end gap-3">
                <button class="btn-secondary" type="button" @click="closeDialog">取消</button>
                <button class="btn-primary" type="submit" :disabled="authStore.loading">
                  {{ authStore.loading ? '保存中...' : '保存修改' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Teleport>
  </header>
</template>

<script setup lang="ts">
import { Teleport, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useSystemStore } from '@/stores/system'

const router = useRouter()
const authStore = useAuthStore()
const systemStore = useSystemStore()
const menuOpen = ref(false)
const dialogOpen = ref(false)
const message = ref<string | null>(null)
const menuRef = ref<HTMLElement | null>(null)

const form = reactive({
  current_username: authStore.username,
  current_password: '',
  new_username: authStore.username,
  new_password: '',
})

function toggleMenu(): void {
  menuOpen.value = !menuOpen.value
}

function handlePointerDown(event: MouseEvent): void {
  if (!menuOpen.value) return
  const target = event.target as Node | null
  if (menuRef.value && target && !menuRef.value.contains(target)) {
    menuOpen.value = false
  }
}

function openPasswordDialog(): void {
  menuOpen.value = false
  dialogOpen.value = true
  message.value = null
  form.current_username = authStore.username
  form.new_username = authStore.username
  form.current_password = ''
  form.new_password = ''
}

function closeDialog(): void {
  dialogOpen.value = false
}

async function submitPasswordChange(): Promise<void> {
  message.value = null
  try {
    await authStore.changePassword({
      current_username: form.current_username.trim(),
      current_password: form.current_password,
      new_username: form.new_username.trim(),
      new_password: form.new_password,
    })
    message.value = '账号密码已更新'
    form.current_password = ''
    form.new_password = ''
  } catch {
    // handled by store
  }
}

function logout(): void {
  menuOpen.value = false
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  document.addEventListener('mousedown', handlePointerDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', handlePointerDown)
})
</script>
