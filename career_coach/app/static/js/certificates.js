// Certificates page: grid of earned certificates; clicking one opens a printable
// certificate sheet. Certificates are issued server-side (course completion +
// level milestones); this page just fetches and renders them.
const { createApp } = Vue;

const app = createApp({
  data() {
    return {
      ready: false,
      user: null,
      recipient: "",
      certificates: [],
      selected: null,
      error: "",
    };
  },
  async mounted() {
    try {
      const r = await fetch("/api/auth/me");
      if (!r.ok) return (window.location.href = "/login");
      this.user = await r.json();
    } catch (e) {
      return (window.location.href = "/login");
    }
    await this.load();
    this.ready = true;
  },
  methods: {
    async load() {
      try {
        const r = await fetch("/api/certificates");
        if (r.ok) {
          const data = await r.json();
          this.recipient = data.recipient || (this.user && this.user.name) || "";
          this.certificates = data.certificates || [];
        } else {
          this.error = "Не удалось загрузить сертификаты";
        }
      } catch (e) {
        this.error = "Ошибка соединения";
      }
    },
    open(cert) {
      this.selected = cert;
    },
    printCert() {
      window.print();
    },
    fmtDate(iso) {
      try {
        return new Date(iso).toLocaleDateString("ru-RU", {
          day: "2-digit", month: "long", year: "numeric",
        });
      } catch (e) {
        return iso;
      }
    },
  },
});
app.component("app-topbar", AppTopbar);
app.component("app-sidebar", AppSidebar);
app.mount("#app");
