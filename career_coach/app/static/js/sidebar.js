// Shared left sidebar for standalone pages (goal flow, etc.) — mirrors the
// portal sidebar: goal card + navigation (Дашборд / Цель / Информация).
const AppSidebar = {
  props: {
    active: { type: String, default: "" }, // 'dashboard' | 'goal' | 'info'
  },
  data() {
    return { user: null, goalCourse: null };
  },
  async mounted() {
    try {
      const r = await fetch("/api/auth/me");
      if (r.ok) this.user = await r.json();
    } catch (e) {
      /* anonymous — show the "choose a course" prompt */
    }
    if (this.user && this.user.goal_course_id) {
      try {
        const r = await fetch(`/api/courses/${this.user.goal_course_id}`);
        if (r.ok) this.goalCourse = await r.json();
      } catch (e) {
        /* ignore */
      }
    }
  },
  computed: {
    goalPct() {
      const xp = (this.user && this.user.xp) || 0;
      return Math.min(100, Math.round((xp / 5000) * 100));
    },
  },
  template: `
  <aside class="sidebar">
    <div class="goal-card">
      <span class="goal-label">Моя цель</span>
      <template v-if="goalCourse">
        <a class="goal-text goal-text-link" :href="'/course/' + goalCourse.id">{{ goalCourse.title }}</a>
        <span class="goal-sub" v-if="goalCourse.technology">{{ goalCourse.technology }} · {{ goalCourse.author }}</span>
        <div class="goal-progress"><div class="goal-fill" :style="{ width: goalPct + '%' }"></div></div>
        <span class="goal-pct">{{ goalPct }}% пути пройдено</span>
        <a class="goal-choose" href="/goal">Сменить курс</a>
      </template>
      <template v-else>
        <p class="goal-text">Выберите курс, который хотите пройти</p>
        <a class="goal-choose" href="/goal">Выбрать курс</a>
      </template>
    </div>

    <h2 class="sidebar-title">Навигация</h2>
    <nav class="nav">
      <a class="nav-item" :class="{ active: active === 'dashboard' }" href="/app">
        <span class="nav-ico">🏠</span><span class="nav-label">Дашборд</span>
      </a>
    </nav>

    <nav class="nav nav-bottom">
      <a class="nav-item" :href="goalCourse ? ('/course/' + goalCourse.id + '/view') : '/goal'"><span class="nav-ico">📚</span><span class="nav-label">Уроки</span></a>
      <a class="nav-item" :class="{ active: active === 'goal' }" href="/goal"><span class="nav-ico">🎯</span><span class="nav-label">Цель</span></a>
      <a class="nav-item" href="/quiz"><span class="nav-ico">📝</span><span class="nav-label">Тест</span></a>
      <a class="nav-item" :class="{ active: active === 'notes' }" href="/notes"><span class="nav-ico">🗒️</span><span class="nav-label">Заметки</span></a>
      <a class="nav-item" :class="{ active: active === 'certificates' }" href="/certificates"><span class="nav-ico">🎓</span><span class="nav-label">Сертификаты</span></a>
      <a v-if="user && user.role === 'admin'" class="nav-item" href="/admin/users"><span class="nav-ico">👥</span><span class="nav-label">Пользователи</span></a>
    </nav>
  </aside>
  `,
};
