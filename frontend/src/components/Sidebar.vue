<template>
  <aside class="hidden w-[280px] shrink-0 border-r border-slate-200/70 bg-[linear-gradient(180deg,#f8fbff_0%,#eef6ff_100%)] p-6 lg:block">
    <div class="mb-8 rounded-[28px] border border-sky-100 bg-white/70 p-5">
      <div class="flex items-center gap-3">
        <img
          :src="pinkDolphinLogo"
          alt="Pink Dolphin"
          class="h-11 w-11 rounded-2xl object-cover shadow-[0_12px_28px_rgba(0,113,227,0.16)]"
        />
        <div>
          <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600"></p>
          <h1 class="mt-1 text-lg font-semibold tracking-[-0.03em] text-slate-950">Pink Dolphin</h1>
        </div>
      </div>
      <!-- <p class="mt-4 text-sm leading-7 text-slate-500">面向个人使用的邮箱监听、风险识别与复核工作台</p> -->
    </div>

    <nav class="space-y-2">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="block rounded-2xl px-4 py-3 transition"
        :class="route.path === item.path
          ? 'bg-[linear-gradient(180deg,#1d9bff_0%,#0071e3_100%)] text-white shadow-[0_12px_24px_rgba(0,113,227,0.2)]'
          : 'bg-white/70 text-slate-600 hover:bg-white'"
      >
        <div class="text-sm font-medium tracking-[-0.01em]">{{ item.label }}</div>
        <div class="mt-1 text-xs" :class="route.path === item.path ? 'text-white/75' : 'text-slate-500'">{{ item.hint }}</div>
      </RouterLink>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

import pinkDolphinLogo from '@/assets/PinkDolphin.jpg'
import type { NavItem } from '@/types/navigation'

const route = useRoute()

const navItems: NavItem[] = [
  { label: '仪表盘', path: '/dashboard', hint: '我的邮箱风险摘要' },
  { label: '邮箱监听', path: '/mailboxes', hint: '绑定并管理多个邮箱' },
  { label: '我的邮件', path: '/emails', hint: '邮件检索、筛选与分析' },
  { label: '规则管理', path: '/rules', hint: '检测规则与动作策略' },
  { label: '处置记录', path: '/actions', hint: '系统动作记录' },
  { label: '隐私白名单', path: '/allowlists', hint: '白名单与 URL/附件/LLM 隐私开关' },
  { label: '配置管理', path: '/config-management', hint: '查看并修改 backend/.env' },
  { label: '问题日志', path: '/issue-logs', hint: '查看日志' },
]
</script>
