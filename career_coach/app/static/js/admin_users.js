// Vue 3 admin page for managing users: roles + mentor applications.
const { createApp } = Vue;

createApp({
  data() {
    return {
      ready: false,
      me: null,
      users: [],
      mentorRequests: [],
      roles: ["user", "mentor", "admin"],
      roleLabels: { user: "Пользователь", mentor: "Ментор", admin: "Админ" },
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
    if (me.role !== "admin") return (window.location.href = "/app");
    this.me = me;
    await this.loadUsers();
    await this.loadMentorRequests();
    this.ready = true;
  },
  methods: {
    async loadUsers() {
      const res = await fetch("/api/admin/users");
      if (res.ok) this.users = await res.json();
    },
    async changeRole(user, role) {
      const updated = await this.req(`/api/admin/users/${user.id}/role`, "PATCH", { role });
      if (updated) {
        user.role = updated.role;
      } else {
        await this.loadUsers(); // revert the <select> to server state on failure
      }
    },
    async loadMentorRequests() {
      const res = await fetch("/api/admin/mentor-requests");
      if (res.ok) this.mentorRequests = await res.json();
    },
    async decideMentor(reqUser, decision) {
      const ok = await this.req(`/api/admin/mentor-requests/${reqUser.id}`, "PATCH", { decision });
      if (ok) {
        await this.loadMentorRequests();
        await this.loadUsers(); // approved user's role changed
      }
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
  },
}).mount("#app");
