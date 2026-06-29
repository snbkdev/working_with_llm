// Vue 3 admin page for managing the catalog (categories + subcategories).
const { createApp } = Vue;

createApp({
  data() {
    return {
      ready: false,
      categories: [],
      newCat: { icon: "📚", slug: "", title: "", color: "#5d3fd3", description: "" },
      drafts: {}, // per-category new-subcategory drafts, keyed by category id
      error: "",
      busy: false,
    };
  },
  async mounted() {
    // Access guard: must be a logged-in admin.
    let me;
    try {
      const res = await fetch("/api/auth/me");
      if (!res.ok) return (window.location.href = "/login");
      me = await res.json();
    } catch (e) {
      return (window.location.href = "/login");
    }
    if (!me.is_admin) return (window.location.href = "/app");
    await this.loadCatalog();
    this.ready = true;
  },
  methods: {
    draftSub(catId) {
      if (!this.drafts[catId]) this.drafts[catId] = { slug: "", title: "", description: "" };
      return this.drafts[catId];
    },
    async loadCatalog() {
      const res = await fetch("/api/admin/categories");
      if (res.ok) this.categories = await res.json();
    },
    async req(url, method, body) {
      this.error = "";
      this.busy = true;
      try {
        const res = await fetch(url, {
          method,
          headers: body ? { "Content-Type": "application/json" } : {},
          body: body ? JSON.stringify(body) : undefined,
        });
        if (res.ok) return res.status === 204 ? true : await res.json();
        const data = await res.json().catch(() => ({}));
        this.error = (typeof data.detail === "string" && data.detail) || "Ошибка запроса";
        return null;
      } catch (e) {
        this.error = "Ошибка соединения";
        return null;
      } finally {
        this.busy = false;
      }
    },
    async addCategory() {
      const created = await this.req("/api/admin/categories", "POST", this.newCat);
      if (created) {
        this.newCat = { icon: "📚", slug: "", title: "", color: "#5d3fd3", description: "" };
        await this.loadCatalog();
      }
    },
    async saveCategory(cat) {
      const updated = await this.req(`/api/admin/categories/${cat.id}`, "PATCH", {
        slug: cat.slug, title: cat.title, icon: cat.icon,
        color: cat.color, description: cat.description,
      });
      if (updated) this.replaceCat(updated);
    },
    async deleteCategory(cat) {
      if (!confirm(`Удалить категорию «${cat.title}» со всеми подкатегориями?`)) return;
      const ok = await this.req(`/api/admin/categories/${cat.id}`, "DELETE");
      if (ok) this.categories = this.categories.filter((c) => c.id !== cat.id);
    },
    async addSub(cat) {
      const draft = this.draftSub(cat.id);
      const updated = await this.req(
        `/api/admin/categories/${cat.id}/subcategories`, "POST", draft
      );
      if (updated) {
        this.drafts[cat.id] = { slug: "", title: "", description: "" };
        this.replaceCat(updated);
      }
    },
    async saveSub(sub) {
      const updated = await this.req(`/api/admin/subcategories/${sub.id}`, "PATCH", {
        slug: sub.slug, title: sub.title, description: sub.description,
      });
      if (updated) this.replaceCat(updated);
    },
    async deleteSub(sub) {
      const ok = await this.req(`/api/admin/subcategories/${sub.id}`, "DELETE");
      if (ok) await this.loadCatalog();
    },
    replaceCat(updated) {
      const i = this.categories.findIndex((c) => c.id === updated.id);
      if (i !== -1) this.categories[i] = updated;
    },
  },
}).mount("#app");
