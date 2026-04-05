<template>
  <aside
    class="hidden shrink-0 border-r border-slate-200/70 bg-[linear-gradient(180deg,#f8fbff_0%,#eef6ff_100%)] duration-300 ease-out lg:flex lg:flex-col"
    :class="collapsed ? 'w-[104px] px-3 py-5' : 'w-[280px] p-6'"
  >
    <div
      class="mb-6 border border-sky-100 bg-white/70 transition-all duration-300"
      :class="collapsed ? 'rounded-[26px] px-3 py-4' : 'rounded-[28px] p-5'"
    >
      <div :class="collapsed ? 'flex flex-col items-center gap-4' : 'flex items-start justify-between gap-3'">
        <div :class="collapsed ? 'flex flex-col items-center gap-3' : 'flex items-center gap-3'">
          <img
            :src="pinkDolphinLogo"
            alt="Pink Dolphin"
            class="object-cover shadow-[0_12px_28px_rgba(0,113,227,0.16)] transition-all duration-300"
            :class="collapsed ? 'h-12 w-12 rounded-[20px]' : 'h-11 w-11 rounded-2xl'"
          />
          <div v-if="!collapsed">
            <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">Security Console</p>
            <h1 class="mt-1 text-lg font-semibold tracking-[-0.03em] text-slate-950">Pink Dolphin</h1>
          </div>
          <div v-else class="text-[10px] font-semibold uppercase tracking-[0.24em] text-sky-600">PD</div>
        </div>

        <button
          class="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-slate-200/80 bg-white/90 text-slate-600 shadow-[0_10px_24px_rgba(16,24,40,0.06)] transition hover:border-sky-200 hover:bg-sky-50 hover:text-sky-700"
          type="button"
          :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'"
          :title="collapsed ? '展开侧边栏' : '收起侧边栏'"
          @click="toggleCollapsed"
        >
          <span class="text-lg leading-none">{{ collapsed ? '›' : '‹' }}</span>
        </button>
      </div>
    </div>

    <nav class="space-y-2">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="block rounded-2xl transition"
        :class="[
          route.path === item.path
            ? 'bg-[linear-gradient(180deg,#1d9bff_0%,#0071e3_100%)] text-white shadow-[0_12px_24px_rgba(0,113,227,0.2)]'
            : 'bg-white/70 text-slate-600 hover:bg-white',
          collapsed ? 'px-0 py-3 text-center' : 'px-4 py-3',
        ]"
        :title="collapsed ? item.label : undefined"
        :aria-label="item.label"
      >
        <template v-if="collapsed">
          <div class="mx-auto flex h-11 w-11 items-center justify-center rounded-[18px] border border-current/10 bg-white/35">
            <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path :d="item.iconPath" />
            </svg>
          </div>
          <span class="sr-only">{{ item.label }}</span>
        </template>
        <template v-else>
          <div class="flex items-start gap-3">
            <div class="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-[18px] border border-current/10 bg-white/35">
              <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path :d="item.iconPath" />
              </svg>
            </div>
            <div class="min-w-0 self-center">
              <div class="text-sm font-medium tracking-[-0.01em]">{{ item.label }}</div>
            </div>
          </div>
        </template>
      </RouterLink>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import pinkDolphinLogo from '@/assets/PinkDolphin.jpg'
import type { NavItem } from '@/types/navigation'

type SidebarNavItem = NavItem & {
  iconPath: string
}

const route = useRoute()
const collapsed = ref(false)
const sidebarCollapsedStorageKey = 'pink-dolphin.sidebar.collapsed'

const navItems: SidebarNavItem[] = [
  {
    label: '仪表盘',
    path: '/dashboard',
    iconPath: 'M4.5 5.25h6v6h-6v-6Zm9 0h6v9h-6v-9Zm-9 9h6v4.5h-6v-4.5Zm9 3h6v1.5h-6v-1.5Z',
  },
  {
    label: '邮箱监听',
    path: '/mailboxes',
    iconPath: 'M3.75 8.25h16.5v8.25A2.25 2.25 0 0 1 18 18.75H6a2.25 2.25 0 0 1-2.25-2.25V8.25Zm0 0L6.75 5.25h10.5l3 3M8.25 12.75h7.5',
  },
  {
    label: '我的邮件',
    path: '/emails',
    iconPath: 'M3.75 6.75h16.5v10.5H3.75V6.75Zm0 .75L12 12.75 20.25 7.5',
  },
  {
    label: '规则管理',
    path: '/rules',
    iconPath: 'M4.5 6h15M7.5 6a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0Zm12 6h-15M15 12a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0Zm4.5 6h-15M10.5 18a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0Z',
  },
  {
    label: '处置记录',
    path: '/actions',
    iconPath: 'M9 4.5h6M9.75 3h4.5A.75.75 0 0 1 15 3.75v1.5a.75.75 0 0 1-.75.75h-4.5A.75.75 0 0 1 9 5.25v-1.5A.75.75 0 0 1 9.75 3Zm-2.25 3.75h9A2.25 2.25 0 0 1 18.75 9v9A2.25 2.25 0 0 1 16.5 20.25h-9A2.25 2.25 0 0 1 5.25 18V9A2.25 2.25 0 0 1 7.5 6.75Zm2.25 6 1.5 1.5 3.75-3.75',
  },
  {
    label: '隐私白名单',
    path: '/allowlists',
    iconPath: 'M12 3.75 5.25 6.75v4.875c0 4.05 2.79 7.728 6.75 8.625 3.96-.897 6.75-4.575 6.75-8.625V6.75L12 3.75Zm-2.25 8.625 1.5 1.5 3.75-3.75',
  },
  {
    label: '配置管理',
    path: '/config-management',
    iconPath: 'M12 8.25A3.75 3.75 0 1 0 12 15.75A3.75 3.75 0 0 0 12 8.25Zm8.25 3.75-.96.555a7.99 7.99 0 0 1-.69 1.665l.555.96-1.5 1.5-.96-.555a7.99 7.99 0 0 1-1.665.69l-.555.96h-2.13l-.555-.96a7.99 7.99 0 0 1-1.665-.69l-.96.555-1.5-1.5.555-.96a7.99 7.99 0 0 1-.69-1.665l-.96-.555v-2.13l.96-.555a7.99 7.99 0 0 1 .69-1.665l-.555-.96 1.5-1.5.96.555a7.99 7.99 0 0 1 1.665-.69l.555-.96h2.13l.555.96a7.99 7.99 0 0 1 1.665.69l.96-.555 1.5 1.5-.555.96a7.99 7.99 0 0 1 .69 1.665l.96.555v2.13Z',
  },
  {
    label: '问题日志',
    path: '/issue-logs',
    iconPath: 'M12 4.5 20.25 18.75H3.75L12 4.5Zm0 4.5v4.5m0 2.25h.008v.008H12v-.008Z',
  },
  {
    label: '使用指南',
    path: '/principles',
    iconPath: 'M6.75 7.5A1.5 1.5 0 1 0 6.75 4.5A1.5 1.5 0 0 0 6.75 7.5Zm10.5 0A1.5 1.5 0 1 0 17.25 4.5A1.5 1.5 0 0 0 17.25 7.5ZM12 19.5A1.5 1.5 0 1 0 12 16.5A1.5 1.5 0 0 0 12 19.5Zm-4.2-12.3 3.15 10.05m5.25-10.05-3.15 10.05M8.25 6h7.5',
  },
]

function toggleCollapsed(): void {
  collapsed.value = !collapsed.value
}

onMounted(() => {
  collapsed.value = window.localStorage.getItem(sidebarCollapsedStorageKey) === '1'
})

watch(collapsed, (value) => {
  window.localStorage.setItem(sidebarCollapsedStorageKey, value ? '1' : '0')
})
</script>
