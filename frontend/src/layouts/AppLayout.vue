<template>
  <div class="app-shell">
    <Sidebar />
    <div class="app-content">
      <Topbar />
      <main class="app-main">
        <div class="view-shell">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import Sidebar from '@/components/Sidebar.vue'
import Topbar from '@/components/Topbar.vue'
</script>
