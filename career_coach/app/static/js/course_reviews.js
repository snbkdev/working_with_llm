// Standalone "course reviews" page. Reads the course id from the URL
// (/course/<id>/reviews) and renders the course header + its reviews.
const { createApp } = Vue;

createApp({
  data() {
    return {
      course: null,
      loading: true,
      error: "",
    };
  },
  async mounted() {
    const m = window.location.pathname.match(/\/course\/(\d+)\/reviews/);
    const id = m && m[1];
    if (!id) {
      this.error = "Курс не указан";
      this.loading = false;
      return;
    }
    try {
      const res = await fetch(`/api/courses/${id}/reviews`);
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
    stars(n) {
      return "★".repeat(n) + "☆".repeat(Math.max(0, 5 - n));
    },
  },
}).mount("#app");
