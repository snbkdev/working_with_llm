// Mentor page: add a course (with YouTube-link lessons) under a direction.
const { createApp } = Vue;

createApp({
  data() {
    return {
      ready: false,
      cats: [],
      sel: { catId: "", subId: "", techId: "" },
      form: { title: "", author: "", duration: "", description: "" },
      lessons: [{ title: "", url: "" }],
      error: "",
      busy: false,
      result: null, // { id, title, lessons_added, lessons_skipped }
    };
  },
  computed: {
    currentCat() {
      return this.cats.find((c) => c.id === this.sel.catId) || null;
    },
    subs() {
      return this.currentCat ? this.currentCat.subcategories : [];
    },
    currentSub() {
      return this.subs.find((s) => s.id === this.sel.subId) || null;
    },
    techs() {
      return this.currentSub ? this.currentSub.technologies : [];
    },
    canSubmit() {
      return (
        !!this.sel.techId &&
        this.form.title.trim() &&
        this.lessons.some((l) => l.title.trim() && l.url.trim())
      );
    },
  },
  watch: {
    "sel.catId"() { this.sel.subId = ""; this.sel.techId = ""; },
    "sel.subId"() { this.sel.techId = ""; },
  },
  async mounted() {
    // Access guard: mentors and admins only.
    let me;
    try {
      const res = await fetch("/api/auth/me");
      if (!res.ok) return (window.location.href = "/login");
      me = await res.json();
    } catch (e) {
      return (window.location.href = "/login");
    }
    if (me.role !== "mentor" && me.role !== "admin") {
      return (window.location.href = "/app");
    }
    try {
      const res = await fetch("/api/categories");
      if (res.ok) this.cats = (await res.json()).categories;
    } catch (e) {
      /* leave empty */
    }
    this.ready = true;
  },
  methods: {
    addLesson() {
      this.lessons.push({ title: "", url: "" });
    },
    removeLesson(i) {
      this.lessons.splice(i, 1);
      if (!this.lessons.length) this.addLesson();
    },
    async submit() {
      if (!this.canSubmit || this.busy) return;
      this.error = "";
      this.result = null;
      this.busy = true;
      const lessons = this.lessons
        .filter((l) => l.title.trim() && l.url.trim())
        .map((l) => ({ title: l.title.trim(), url: l.url.trim() }));
      try {
        const res = await fetch("/api/mentor/courses", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            technology_id: this.sel.techId,
            title: this.form.title.trim(),
            author: this.form.author.trim(),
            duration: this.form.duration.trim(),
            description: this.form.description.trim(),
            lessons,
          }),
        });
        const data = await res.json().catch(() => ({}));
        if (res.ok) {
          this.result = data;
          this.form = { title: "", author: "", duration: "", description: "" };
          this.lessons = [{ title: "", url: "" }];
        } else {
          this.error =
            (typeof data.detail === "string" && data.detail) || "Не удалось создать курс";
        }
      } catch (e) {
        this.error = "Ошибка соединения с сервером";
      } finally {
        this.busy = false;
      }
    },
  },
}).mount("#app");
