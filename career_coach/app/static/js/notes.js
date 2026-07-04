// Notes page: notes organised into per-course tabs. Choosing a course opens its
// tab; inside are all its notes plus a «+ Добавить заметку» button.
const { createApp } = Vue;

const app = createApp({
  data() {
    return {
      ready: false,
      user: null,
      notes: [],
      myCourses: [], // courses available to attach notes to: { id, title }
      openedKeys: [], // tabs opened via the picker but without notes yet
      activeKey: null, // course id (number) or "none"
      creating: false,
      newNote: { title: "", body: "" },
      edit: null, // { id, title, body }
      courseToOpen: "",
      busy: false,
      error: "",
    };
  },
  computed: {
    courseTitleMap() {
      const m = {};
      this.myCourses.forEach((c) => (m[c.id] = c.title));
      this.notes.forEach((n) => {
        if (n.course_id) m[n.course_id] = n.course_title || m[n.course_id] || "Курс";
      });
      return m;
    },
    // Вкладки: курсы, по которым есть заметки, плюс открытые вручную.
    tabs() {
      const keys = [];
      const seen = new Set();
      const add = (k) => {
        const s = String(k);
        if (!seen.has(s)) { seen.add(s); keys.push(k); }
      };
      this.notes.forEach((n) => add(n.course_id || "none"));
      this.openedKeys.forEach((k) => add(k));
      return keys.map((key) => ({
        key,
        course_id: key === "none" ? null : Number(key),
        title: key === "none" ? "Без курса" : this.courseTitleMap[key] || "Курс",
        count: this.notes.filter((n) => String(n.course_id || "none") === String(key)).length,
      }));
    },
    activeTab() {
      return this.tabs.find((t) => String(t.key) === String(this.activeKey)) || null;
    },
    activeNotes() {
      if (this.activeKey == null) return [];
      return this.notes.filter((n) => String(n.course_id || "none") === String(this.activeKey));
    },
    availableCourses() {
      const tabIds = new Set(this.tabs.map((t) => String(t.key)));
      return this.myCourses.filter((c) => !tabIds.has(String(c.id)));
    },
    hasNoneTab() {
      return this.tabs.some((t) => t.key === "none");
    },
  },
  async mounted() {
    try {
      const r = await fetch("/api/auth/me");
      if (!r.ok) return (window.location.href = "/login");
      this.user = await r.json();
    } catch (e) {
      return (window.location.href = "/login");
    }
    await Promise.all([this.loadNotes(), this.loadMyCourses()]);
    if (this.tabs.length) this.activeKey = this.tabs[0].key;
    this.ready = true;
  },
  methods: {
    async loadNotes() {
      try {
        const r = await fetch("/api/notes");
        if (r.ok) this.notes = await r.json();
      } catch (e) {
        /* ignore */
      }
    },
    // «Мои курсы» для вкладок: цель + курсы с пройденными уроками.
    async loadMyCourses() {
      const byId = {};
      try {
        const r = await fetch("/api/progress/lessons");
        if (r.ok) {
          const done = await r.json();
          done.forEach((l) => (byId[l.course_id] = l.course_title));
        }
      } catch (e) {
        /* ignore */
      }
      if (this.user && this.user.goal_course_id) {
        try {
          const r = await fetch(`/api/courses/${this.user.goal_course_id}`);
          if (r.ok) {
            const c = await r.json();
            byId[c.id] = c.title;
          }
        } catch (e) {
          /* ignore */
        }
      }
      this.myCourses = Object.entries(byId).map(([id, title]) => ({ id: Number(id), title }));
      this.myCourses.sort((a, b) => a.title.localeCompare(b.title, "ru"));
    },
    selectTab(key) {
      this.activeKey = key;
      this.creating = false;
      this.edit = null;
    },
    openCourseTab() {
      const val = this.courseToOpen;
      this.courseToOpen = "";
      if (!val) return;
      const key = val === "none" ? "none" : Number(val);
      if (!this.openedKeys.some((k) => String(k) === String(key))) this.openedKeys.push(key);
      this.selectTab(key);
    },
    startCreate() {
      this.newNote = { title: "", body: "" };
      this.edit = null;
      this.creating = true;
    },
    cancelCreate() {
      this.creating = false;
    },
    async addNote() {
      if (!this.newNote.title.trim() && !this.newNote.body.trim()) {
        this.error = "Заметка не может быть пустой";
        return;
      }
      const saved = await this.req("/api/notes", "POST", {
        title: this.newNote.title,
        body: this.newNote.body,
        course_id: this.activeTab ? this.activeTab.course_id : null,
      });
      if (saved) {
        this.notes.unshift(saved);
        this.creating = false;
        this.newNote = { title: "", body: "" };
      }
    },
    startEdit(note) {
      this.creating = false;
      this.edit = { id: note.id, title: note.title, body: note.body };
    },
    cancelEdit() {
      this.edit = null;
    },
    async saveEdit() {
      if (!this.edit) return;
      const updated = await this.req(`/api/notes/${this.edit.id}`, "PATCH", {
        title: this.edit.title,
        body: this.edit.body,
      });
      if (updated) {
        const i = this.notes.findIndex((n) => n.id === updated.id);
        if (i !== -1) this.notes.splice(i, 1, updated);
        this.notes.sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1));
        this.edit = null;
      }
    },
    async deleteNote(note) {
      if (!confirm("Удалить заметку?")) return;
      const ok = await this.req(`/api/notes/${note.id}`, "DELETE");
      if (ok) {
        this.notes = this.notes.filter((n) => n.id !== note.id);
        // если активная вкладка исчезла (была только по заметкам) — переключимся
        if (!this.activeTab && this.tabs.length) this.activeKey = this.tabs[0].key;
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
    fmtDate(iso) {
      try {
        return new Date(iso).toLocaleString("ru-RU", {
          day: "2-digit", month: "2-digit", year: "numeric",
          hour: "2-digit", minute: "2-digit",
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
