// Shared top bar for the standalone pages (goal flow, course pages).
// Registered on each page's Vue app as <app-topbar>. Provides: back button,
// brand→home, global tabs (Дашборд / Цель) and the profile menu (avatar + logout).
const AppTopbar = {
  props: {
    active: { type: String, default: "" }, // 'dashboard' | 'goal'
    showBack: { type: Boolean, default: true },
  },
  data() {
    return { user: null, menuOpen: false };
  },
  async mounted() {
    try {
      const r = await fetch("/api/auth/me");
      if (r.ok) this.user = await r.json();
    } catch (e) {
      /* anonymous — show "Войти" */
    }
  },
  computed: {
    initials() {
      const src = (this.user && (this.user.full_name || this.user.name)) || "";
      const p = src.trim().split(/\s+/).filter(Boolean);
      if (!p.length) return "?";
      return (p.length === 1 ? p[0][0] : p[0][0] + p[1][0]).toUpperCase();
    },
  },
  methods: {
    goBack() {
      if (window.history.length > 1) window.history.back();
      else window.location.href = "/app";
    },
    async logout() {
      try {
        await fetch("/api/auth/logout", { method: "POST" });
      } catch (e) {
        /* ignore */
      }
      window.location.href = "/";
    },
  },
  template: `
  <header class="topbar">
    <div class="topbar-left">
      <button v-if="showBack" class="topbar-back" @click="goBack" title="Назад">←</button>
      <a class="brand" href="/app">
        <span class="brand-logo">🦆</span>
        <span class="brand-name">Duckie</span>
      </a>
    </div>
    <div class="topbar-right">
      <div v-if="user" class="profile-wrap">
        <button class="profile" :class="{ active: menuOpen }" @click="menuOpen = !menuOpen">
          <img v-if="user.avatar" class="avatar-circle avatar-img" :src="user.avatar" alt="avatar">
          <span v-else class="avatar-circle">{{ initials }}</span>
          <span class="profile-name">{{ user.name }}</span>
          <span class="profile-caret">▾</span>
        </button>
        <div v-if="menuOpen" class="profile-menu">
          <a class="profile-menu-item" href="/app">🏠 На главную</a>
          <a v-if="user.is_admin" class="profile-menu-item" href="/admin">🛠️ Админка</a>
          <button class="profile-menu-item danger" @click="logout">🚪 Выход</button>
        </div>
      </div>
      <a v-else class="btn-secondary" href="/login">Войти</a>
    </div>
  </header>
  <div v-if="menuOpen" class="menu-backdrop" @click="menuOpen = false"></div>
  `,
};
