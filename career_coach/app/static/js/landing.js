// Vue 3 app for the public landing page. No auth required; if the visitor
// already has a session, CTAs point to the portal instead of /login.
const { createApp } = Vue;

createApp({
  data() {
    return {
      tagline: "Твой путь в IT",
      categories: [],
      authed: false,
    };
  },
  async mounted() {
    try {
      const res = await fetch("/api/categories");
      const data = await res.json();
      this.tagline = data.tagline;
      this.categories = data.categories;
    } catch (e) {
      /* keep defaults */
    }
    // Soft auth check — only to switch CTA labels, page stays public.
    try {
      const me = await fetch("/api/auth/me");
      this.authed = me.ok;
    } catch (e) {
      this.authed = false;
    }
  },
}).mount("#app");
