// Vue 3 app for the registration / login / forgot-password page.
const { createApp } = Vue;

createApp({
  data() {
    return {
      mode: "login", // 'login' | 'register' | 'forgot'
      form: { name: "", email: "", password: "" },
      error: "",
      loading: false,
      sent: false, // forgot-password confirmation
    };
  },
  computed: {
    submitLabel() {
      if (this.loading) return "Подождите…";
      return {
        login: "Войти",
        register: "Создать аккаунт",
        forgot: "Отправить ссылку",
      }[this.mode];
    },
  },
  methods: {
    setMode(mode) {
      this.mode = mode;
      this.error = "";
      this.sent = false;
    },
    async submit() {
      this.error = "";
      this.loading = true;
      try {
        if (this.mode === "forgot") {
          await fetch("/api/auth/forgot-password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: this.form.email }),
          });
          this.sent = true; // always show success (no account enumeration)
          return;
        }

        const url = this.mode === "login" ? "/api/auth/login" : "/api/auth/register";
        const body =
          this.mode === "login"
            ? { email: this.form.email, password: this.form.password }
            : this.form;
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
      if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; ");
      return "";
    },
  },
}).mount("#app");
