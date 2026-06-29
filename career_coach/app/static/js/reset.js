// Vue 3 app for the password-reset page. Reads the token from the URL.
const { createApp } = Vue;

createApp({
  data() {
    return {
      token: new URLSearchParams(window.location.search).get("token") || "",
      password: "",
      confirm: "",
      error: "",
      loading: false,
      done: false,
    };
  },
  methods: {
    async submit() {
      this.error = "";
      if (this.password.length < 6) {
        this.error = "Пароль должен быть не короче 6 символов";
        return;
      }
      if (this.password !== this.confirm) {
        this.error = "Пароли не совпадают";
        return;
      }
      this.loading = true;
      try {
        const res = await fetch("/api/auth/reset-password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token: this.token, password: this.password }),
        });
        if (res.ok) {
          this.done = true;
          return;
        }
        const data = await res.json().catch(() => ({}));
        this.error = (typeof data.detail === "string" && data.detail) || "Не удалось сбросить пароль";
      } catch (e) {
        this.error = "Ошибка соединения с сервером";
      } finally {
        this.loading = false;
      }
    },
  },
}).mount("#app");
