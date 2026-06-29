// Vue 3 app for the registration / login page.
const { createApp } = Vue;

createApp({
  data() {
    return {
      mode: "login", // 'login' | 'register'
      form: { name: "", email: "", password: "" },
      error: "",
      loading: false,
    };
  },
  methods: {
    setMode(mode) {
      this.mode = mode;
      this.error = "";
    },
    async submit() {
      this.error = "";
      this.loading = true;
      const url = this.mode === "login" ? "/api/auth/login" : "/api/auth/register";
      const body =
        this.mode === "login"
          ? { email: this.form.email, password: this.form.password }
          : this.form;
      try {
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (res.ok) {
          window.location.href = "/app";
          return;
        }
        const data = await res.json().catch(() => ({}));
        this.error = this.formatError(data.detail) || "Что-то пошло не так";
      } catch (e) {
        this.error = "Ошибка соединения с сервером";
      } finally {
        this.loading = false;
      }
    },
    formatError(detail) {
      if (!detail) return "";
      if (typeof detail === "string") return detail;
      // FastAPI validation errors come as an array
      if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; ");
      return "";
    },
  },
}).mount("#app");
