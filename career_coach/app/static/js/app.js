// Vue 3 SPA (CDN global build). Skeleton only: state is local placeholder
// data, the chat hits the stub /api/chat endpoint. No mode/XP logic yet.
const { createApp, nextTick } = Vue;

createApp({
  data() {
    return {
      // current user (loaded from /api/auth/me)
      user: null,
      ready: false,
      // meta (loaded from /api/meta)
      goal: "",
      commands: [],
      // IT directions (loaded from /api/categories)
      categories: [],
      savingDirection: false,
      savingPlanned: false,
      // gamification placeholders
      xp: 0,
      level: 0,
      streak: 0,
      topicsLearned: 0,
      challengesSolved: 0,
      // navigation
      view: "dashboard",
      menuOpen: false,
      // personal info form
      info: { full_name: "", birth_date: "", bio: "" },
      savingInfo: false,
      infoSaved: false,
      // chat
      messages: [
        {
          who: "coach",
          text: "Привет! Выбери режим слева или просто напиши сообщение. (LLM пока не подключён — это каркас.)",
        },
      ],
      draft: "",
      // dashboard featured lessons
      featured: [
        { command: "/learn", ico: "📖", name: "Режим обучения", desc: "Разбор темы шаг за шагом" },
        { command: "/quiz", ico: "❓", name: "Квиз", desc: "Проверка знаний, +10 XP за ответ" },
        { command: "/challenge", ico: "⚔️", name: "Код-челлендж", desc: "Задача на код, +100 XP за решение" },
      ],
    };
  },

  computed: {
    xpInLevel() {
      return this.xp % 100;
    },
    xpPct() {
      return this.xpInLevel;
    },
    goalPct() {
      // Real progress toward the goal: Level 50 = 50 × 100 = 5000 XP total.
      const TARGET_XP = 50 * 100;
      return Math.min(100, Math.round((this.xp / TARGET_XP) * 100));
    },
    chosenCategory() {
      if (!this.user || !this.user.direction) return null;
      return this.categories.find((c) => c.slug === this.user.direction) || null;
    },
    goalText() {
      // Personal goal derived from the chosen direction; null prompts a choice.
      const c = this.chosenCategory;
      return c ? `Освоить направление «${c.title}» и вырасти в IT` : null;
    },
    initials() {
      const src = (this.user && (this.user.full_name || this.user.name)) || "";
      const parts = src.trim().split(/\s+/).filter(Boolean);
      if (parts.length === 0) return "?";
      if (parts.length === 1) return parts[0][0].toUpperCase();
      return (parts[0][0] + parts[1][0]).toUpperCase();
    },
    achievements() {
      const u = this.user || {};
      const planned = u.planned || [];
      return [
        { ico: "🐣", title: "Начало пути", desc: "Аккаунт создан", unlocked: true },
        { ico: "🧭", title: "Направление выбрано", desc: "Выбрано, что учите сейчас", unlocked: !!u.direction },
        { ico: "🗺️", title: "Есть план", desc: "Добавлено направление в план", unlocked: planned.length > 0 },
        { ico: "⭐", title: "Первые XP", desc: "Набрано 10+ XP", unlocked: (u.xp || 0) >= 10 },
        { ico: "🏅", title: "Уровень 1", desc: "Достигнут 1-й уровень", unlocked: (u.level || 0) >= 1 },
        { ico: "📝", title: "О себе", desc: "Заполнена информация о себе", unlocked: !!u.bio },
      ];
    },
  },

  async mounted() {
    // Auth guard: redirect to /login if no valid session.
    try {
      const res = await fetch("/api/auth/me");
      if (!res.ok) {
        window.location.href = "/login";
        return;
      }
      this.user = await res.json();
      this.xp = this.user.xp;
      this.level = this.user.level;
    } catch (e) {
      window.location.href = "/login";
      return;
    }

    try {
      const res = await fetch("/api/meta");
      const data = await res.json();
      this.goal = data.goal;
      this.commands = data.commands;
    } catch (e) {
      this.goal = "Стать Python-разработчиком";
    }

    try {
      const res = await fetch("/api/categories");
      const data = await res.json();
      this.categories = data.categories;
    } catch (e) {
      this.categories = [];
    }
    this.ready = true;
  },

  methods: {
    go(view) {
      this.view = view;
      if (view === "chat") this.scrollChat();
    },
    toggleMenu() {
      this.menuOpen = !this.menuOpen;
    },
    openInfo() {
      this.menuOpen = false;
      this.infoSaved = false;
      // Prefill form from the loaded user.
      this.info.full_name = this.user.full_name || "";
      this.info.birth_date = this.user.birth_date || "";
      this.info.bio = this.user.bio || "";
      this.view = "info";
    },
    openGoal() {
      this.menuOpen = false;
      this.view = "goal";
    },
    isPlanned(slug) {
      return (this.user.planned || []).includes(slug);
    },
    async togglePlanned(slug) {
      const current = this.user.planned || [];
      const next = current.includes(slug)
        ? current.filter((s) => s !== slug)
        : [...current, slug];
      this.savingPlanned = true;
      try {
        const res = await fetch("/api/auth/profile", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ planned: next }),
        });
        if (res.ok) this.user = await res.json();
      } catch (e) {
        /* ignore */
      } finally {
        this.savingPlanned = false;
      }
    },
    async saveInfo() {
      this.savingInfo = true;
      this.infoSaved = false;
      try {
        const res = await fetch("/api/auth/profile", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            full_name: this.info.full_name || null,
            birth_date: this.info.birth_date || null,
            bio: this.info.bio || null,
          }),
        });
        if (res.ok) {
          this.user = await res.json();
          this.infoSaved = true;
        }
      } catch (e) {
        /* ignore */
      } finally {
        this.savingInfo = false;
      }
    },
    async logout() {
      await fetch("/api/auth/logout", { method: "POST" });
      window.location.href = "/";
    },
    async chooseDirection(slug) {
      this.savingDirection = true;
      try {
        const res = await fetch("/api/auth/profile", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ direction: slug }),
        });
        if (res.ok) this.user = await res.json();
      } catch (e) {
        /* ignore */
      } finally {
        this.savingDirection = false;
      }
    },
    async send() {
      const text = this.draft.trim();
      if (!text) return;
      this.messages.push({ who: "user", text });
      this.draft = "";
      this.scrollChat();
      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text }),
        });
        const data = await res.json();
        this.messages.push({ who: "coach", text: data.reply });
      } catch (e) {
        this.messages.push({ who: "coach", text: "Ошибка соединения с сервером." });
      }
      this.scrollChat();
    },
    scrollChat() {
      nextTick(() => {
        const box = this.$refs.chatBox;
        if (box) box.scrollTop = box.scrollHeight;
      });
    },
  },
}).mount("#app");
