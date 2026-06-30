// Placeholder "watch course" page. Shows the course title; real lesson
// content will be added later.
const { createApp } = Vue;

createApp({
  data() {
    return { courseId: null, title: "Просмотр курса", loading: true };
  },
  async mounted() {
    const m = window.location.pathname.match(/\/course\/(\d+)\/view/);
    this.courseId = m && m[1];
    if (this.courseId) {
      try {
        const res = await fetch(`/api/courses/${this.courseId}`);
        if (res.ok) {
          const c = await res.json();
          this.title = c.title;
        }
      } catch (e) {
        /* keep default title */
      }
    }
    this.loading = false;
  },
}).mount("#app");
