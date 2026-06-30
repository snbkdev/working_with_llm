// Course info page: header, learning plan, and "make this my goal" action.
const { createApp } = Vue;

createApp({
  data() {
    return {
      course: null,
      user: null,
      loading: true,
      saving: false,
      error: "",
    };
  },
  computed: {
    accent() {
      return (this.course && this.course.category && this.course.category.color) || "#5d3fd3";
    },
    isGoal() {
      return !!(this.user && this.course && this.user.goal_course_id === this.course.id);
    },
  },
  async mounted() {
    const m = window.location.pathname.match(/\/course\/(\d+)/);
    const id = m && m[1];
    if (!id) {
      this.error = "Курс не указан";
      this.loading = false;
      return;
    }
    // Goal-setting needs a logged-in user; bounce to login if there's no session.
    try {
      const meRes = await fetch("/api/auth/me");
      if (!meRes.ok) {
        window.location.href = "/login";
        return;
      }
      this.user = await meRes.json();
    } catch (e) {
      window.location.href = "/login";
      return;
    }
    try {
      const res = await fetch(`/api/courses/${id}`);
      if (!res.ok) {
        this.error = res.status === 404 ? "Курс не найден" : "Не удалось загрузить курс";
        return;
      }
      this.course = await res.json();
    } catch (e) {
      this.error = "Ошибка соединения с сервером";
    } finally {
      this.loading = false;
    }
  },
  methods: {
    async toggleGoal() {
      const next = this.isGoal ? null : this.course.id;
      this.saving = true;
      try {
        const res = await fetch("/api/auth/profile", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ goal_course_id: next }),
        });
        if (res.ok) this.user = await res.json();
      } catch (e) {
        /* ignore */
      } finally {
        this.saving = false;
      }
    },
  },
}).mount("#app");
