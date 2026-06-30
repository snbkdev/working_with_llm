// Placeholder "watch course" page. Loads course meta for the header + tabs;
// real lesson content will be added later.
const { createApp } = Vue;

const app = createApp({
  data() {
    return { course: null, loading: true };
  },
  async mounted() {
    const m = window.location.pathname.match(/\/course\/(\d+)\/view/);
    const id = m && m[1];
    if (id) {
      try {
        const res = await fetch(`/api/courses/${id}`);
        if (res.ok) this.course = await res.json();
      } catch (e) {
        /* leave course null */
      }
    }
    this.loading = false;
  },
});
app.component("app-topbar", AppTopbar);
app.mount("#app");
