<template>
  <div class="flex min-h-screen items-center justify-center bg-transparent px-4 py-10">
    <div class="w-full max-w-[1120px] overflow-hidden rounded-[36px] border border-slate-200/70 bg-white/70 shadow-[0_24px_80px_rgba(16,24,40,0.08)] backdrop-blur">
      <div class="grid lg:grid-cols-[1.1fr,0.9fr]">
        <section class="border-b border-slate-200/70 bg-[radial-gradient(circle_at_top,rgba(0,113,227,0.12),transparent_32%),linear-gradient(180deg,rgba(255,255,255,0.98)_0%,rgba(255,255,255,0.82)_100%)] px-8 py-10 lg:border-b-0 lg:border-r lg:px-12 lg:py-14">
          <p class="inline-flex rounded-full bg-sky-50 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">Apple Style Console</p>
          <h1 class="mt-6 text-5xl font-semibold leading-[0.95] tracking-[-0.06em] text-slate-950 lg:text-7xl">
            Pink<br />
            <span class="text-sky-600">Dolphin</span>
          </h1>
          <p class="mt-6 max-w-xl text-base leading-8 text-slate-500 lg:text-lg">
            针对钓鱼邮件识别与处置场景打造的安全管理台。
          </p>
          <div class="mt-10 grid gap-4 sm:grid-cols-3">
            <div class="rounded-[24px] border border-sky-100 bg-white/80 p-5">
              <div class="text-3xl font-semibold tracking-[-0.05em] text-slate-950">6</div>
              <div class="mt-2 text-sm text-slate-500">分析器协同判定</div>
            </div>
            <div class="rounded-[24px] border border-sky-100 bg-white/80 p-5">
              <div class="text-3xl font-semibold tracking-[-0.05em] text-slate-950">5</div>
              <div class="mt-2 text-sm text-slate-500">处置动作</div>
            </div>
            <div class="rounded-[24px] border border-sky-100 bg-white/80 p-5">
              <div class="text-3xl font-semibold tracking-[-0.05em] text-slate-950">闭环</div>
              <div class="mt-2 text-sm text-slate-500">检测到治理</div>
            </div>
          </div>
        </section>

        <section class="px-8 py-10 lg:px-12 lg:py-14">
          <!-- <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">Security Console</p> -->
          <!-- <h2 class="mt-3 text-3xl font-semibold tracking-[-0.05em] text-slate-950">管理员登录</h2>
          <p class="mt-3 text-sm leading-7 text-slate-500">使用默认管理员账号进入前端管理台。</p> -->
          <form class="mt-8 space-y-4" @submit.prevent="submit">
          <div>
            <label class="mb-2 block text-sm font-medium text-slate-600">用户名</label>
            <input v-model="form.username" class="field" autocomplete="username" />
          </div>
          <div>
            <label class="mb-2 block text-sm font-medium text-slate-600">密码</label>
            <input v-model="form.password" class="field" type="password" autocomplete="current-password" />
          </div>
          <p v-if="!systemStore.backendAvailable" class="text-sm leading-7 text-red-600">后端不可用，暂时无法登录。</p>
          <p v-else-if="authStore.error" class="text-sm text-red-600">{{ authStore.error }}</p>
          <button class="btn-primary w-full" type="submit" :disabled="authStore.loading || !systemStore.backendAvailable">
            {{ authStore.loading ? '登录中...' : systemStore.backendAvailable ? '登录' : '等待后端恢复' }}
          </button>
        </form>
          <!-- <div class="mt-6 rounded-[24px] border border-sky-100 bg-sky-50/70 p-5 text-sm text-slate-600">
            <div>默认账号：<span class="font-medium text-slate-900">admin</span></div>
            <div class="mt-2">默认密码：<span class="font-medium text-slate-900">admin123</span></div>
          </div> -->
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useSystemStore } from '@/stores/system'

const router = useRouter()
const authStore = useAuthStore()
const systemStore = useSystemStore()
const form = reactive({ username: 'admin', password: '' })

async function submit(): Promise<void> {
  if (!systemStore.backendAvailable) return
  try {
    await authStore.login(form)
    await router.push('/dashboard')
  } catch {
    // handled by store
  }
}
</script>
