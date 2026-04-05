import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '@/layouts/AppLayout.vue'
import AuthGuard from '@/components/AuthGuard.vue'
import { useAuthStore } from '@/stores/auth'
import ActionsView from '@/views/ActionsView.vue'
import AllowlistsView from '@/views/AllowlistsView.vue'
import ConfigManagementView from '@/views/ConfigManagementView.vue'
import DashboardView from '@/views/DashboardView.vue'
import EmailDetailView from '@/views/EmailDetailView.vue'
import EmailsView from '@/views/EmailsView.vue'
import IssueLogsView from '@/views/IssueLogsView.vue'
import LoginView from '@/views/LoginView.vue'
import MailboxesView from '@/views/MailboxesView.vue'
import PrinciplesView from '@/views/PrinciplesView.vue'
import RulesView from '@/views/RulesView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { guestOnly: true },
    },
    {
      path: '/',
      component: AuthGuard,
      children: [
        {
          path: '',
          component: AppLayout,
          children: [
            { path: '', redirect: '/dashboard' },
            { path: '/dashboard', name: 'dashboard', component: DashboardView },
            { path: '/mailboxes', name: 'mailboxes', component: MailboxesView },
            { path: '/emails', name: 'emails', component: EmailsView },
            { path: '/emails/:id', name: 'email-detail', component: EmailDetailView, props: true },
            { path: '/rules', name: 'rules', component: RulesView },
            { path: '/actions', name: 'actions', component: ActionsView },
            { path: '/allowlists', name: 'allowlists', component: AllowlistsView },
            { path: '/config-management', name: 'config-management', component: ConfigManagementView },
            { path: '/issue-logs', name: 'issue-logs', component: IssueLogsView },
            { path: '/principles', name: 'principles', component: PrinciplesView },
          ],
        },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (!authStore.isAuthenticated && to.name !== 'login') {
    return { name: 'login' }
  }
  if (authStore.isAuthenticated && to.meta.guestOnly) {
    return { name: 'dashboard' }
  }
  return true
})

export default router
