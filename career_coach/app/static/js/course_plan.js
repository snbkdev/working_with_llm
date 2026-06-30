// Course learning-plan page: renders the lessons of a course.
const { createApp } = Vue;

const app = createApp({
  data() {
    return { course: null, loading: true, error: "" };
  },
  async mounted() {
    const m = window.location.pathname.match(/\/course\/(\d+)\/plan/);
    const id = m && m[1];
    if (!id) {
      this.error = "Курс не указан";
      this.loading = false;
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
});
app.component("app-topbar", AppTopbar);
app.mount("#app");
