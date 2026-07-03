// Vue 3 SPA (CDN global build). Portal shell: dashboard + personal info.
// The goal flow (category → … → course) now lives on its own pages (/goal, /course/…).
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
      // the chosen goal course, loaded when the user has one
      goalCourse: null,
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
      // avatar upload
      uploadingAvatar: false,
      avatarError: "",
      // mentor application
      mentorNote: "",
      requestingMentor: false,
      // chat
      messages: [
        {
          who: "coach",
          text: "Привет! Выбери режим слева или просто напиши сообщение. (LLM пока не подключён — это каркас.)",
        },
      ],
      draft: "",
      // короткое всплывающее уведомление о начислении XP
      xpToast: "",
      // dashboard featured lessons ('href' → переход, 'action' → начисление XP)
      featured: [
        { command: "/learn", ico: "📖", name: "Режим обучения", desc: "Разбор темы шаг за шагом", href: null, action: null },
        { command: "/quiz", ico: "❓", name: "Квиз", desc: "Проверка знаний, +10 XP за верный ответ", href: "/quiz", action: null },
        { command: "/challenge", ico: "⚔️", name: "Код-челлендж", desc: "Задача на код, +100 XP за решение", href: "/challenge", action: null },
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
    initials() {
      const src = (this.user && (this.user.full_name || this.user.name)) || "";
      const parts = src.trim().split(/\s+/).filter(Boolean);
      if (parts.length === 0) return "?";
      if (parts.length === 1) return parts[0][0].toUpperCase();
      return (parts[0][0] + parts[1][0]).toUpperCase();
    },
    achievements() {
      const u = this.user || {};
      return [
        { ico: "🐣", title: "Начало пути", desc: "Аккаунт создан", unlocked: true },
        { ico: "🎯", title: "Цель выбрана", desc: "Выбран курс-цель", unlocked: !!u.goal_course_id },
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

    // Resolve the chosen goal course (for the sidebar card), if any.
    if (this.user.goal_course_id) {
      try {
        const res = await fetch(`/api/courses/${this.user.goal_course_id}`);
        if (res.ok) this.goalCourse = await res.json();
      } catch (e) {
        /* ignore */
      }
    }

    // Real dashboard counters: sum solved items across quiz/challenge topics.
    this.loadProgressCounters();

    this.ready = true;

    // Allow deep-linking straight to the profile view via /app?view=info.
    if (new URLSearchParams(window.location.search).get("view") === "info") {
      this.openInfo();
    }
  },

  methods: {
    go(view) {
      this.view = view;
      if (view === "chat") this.scrollChat();
    },
    async loadProgressCounters() {
      // "Тем изучено" — сколько тем квиза начато; "Челленджей решено" — сумма
      // решённых задач по всем темам. Ошибки тихо игнорируем.
      try {
        const [qr, cr] = await Promise.all([
          fetch("/api/quiz/topics"),
          fetch("/api/challenges/topics"),
        ]);
        if (qr.ok) {
          const topics = await qr.json();
          this.topicsLearned = topics.filter((t) => t.solved > 0).length;
        }
        if (cr.ok) {
          const topics = await cr.json();
          this.challengesSolved = topics.reduce((n, t) => n + (t.solved || 0), 0);
        }
      } catch (e) {
        /* ignore */
      }
    },
    openFeatured(item) {
      if (item.href) {
        window.location.href = item.href;
      } else if (item.action) {
        this.award(item.action);
      }
    },
    async award(action) {
      // Начисление XP за действие. Суммы считает сервер (config.XP_REWARDS);
      // здесь только показываем обновлённый прогресс.
      try {
        const res = await fetch("/api/auth/xp/award", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action }),
        });
        if (!res.ok) return;
        const data = await res.json();
        this.xp = data.xp;
        this.level = data.level;
        if (this.user) {
          this.user.xp = data.xp;
          this.user.level = data.level;
        }
        if (data.leveled_up) {
          this.showXpToast(`+${data.awarded} XP · Уровень ${data.level}! 🎉`);
        } else if (data.awarded > 0) {
          this.showXpToast(`+${data.awarded} XP`);
        } else {
          this.showXpToast("Достигнут максимум — уровень 50 💎");
        }
      } catch (e) {
        /* ignore */
      }
    },
    showXpToast(text) {
      this.xpToast = text;
      clearTimeout(this._xpToastTimer);
      this._xpToastTimer = setTimeout(() => {
        this.xpToast = "";
      }, 2500);
    },
    toggleMenu() {
      this.menuOpen = !this.menuOpen;
    },
    openInfo() {
      this.menuOpen = false;
      this.infoSaved = false;
      this.avatarError = "";
      // Prefill form from the loaded user.
      this.info.full_name = this.user.full_name || "";
      this.info.birth_date = this.user.birth_date || "";
      this.info.bio = this.user.bio || "";
      this.view = "info";
    },
    async uploadAvatar(event) {
      const file = event.target.files && event.target.files[0];
      event.target.value = ""; // allow re-selecting the same file later
      if (!file) return;
      if (!file.type.startsWith("image/")) {
        this.avatarError = "Можно загружать только изображения";
        return;
      }
      if (file.size > 2 * 1024 * 1024) {
        this.avatarError = "Файл слишком большой (максимум 2 МБ)";
        return;
      }
      this.avatarError = "";
      this.uploadingAvatar = true;
      try {
        const form = new FormData();
        form.append("file", file);
        const res = await fetch("/api/auth/avatar", { method: "POST", body: form });
        if (res.ok) {
          this.user = await res.json();
        } else {
          const data = await res.json().catch(() => ({}));
          this.avatarError = data.detail || "Не удалось загрузить файл";
        }
      } catch (e) {
        this.avatarError = "Ошибка соединения с сервером";
      } finally {
        this.uploadingAvatar = false;
      }
    },
    async removeAvatar() {
      this.avatarError = "";
      this.uploadingAvatar = true;
      try {
        const res = await fetch("/api/auth/avatar", { method: "DELETE" });
        if (res.ok) this.user = await res.json();
      } catch (e) {
        this.avatarError = "Ошибка соединения с сервером";
      } finally {
        this.uploadingAvatar = false;
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
    async requestMentor() {
      this.requestingMentor = true;
      try {
        const res = await fetch("/api/auth/mentor-request", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ note: this.mentorNote.trim() || null }),
        });
        if (res.ok) {
          this.user = await res.json();
          this.mentorNote = "";
        }
      } catch (e) {
        /* ignore */
      } finally {
        this.requestingMentor = false;
      }
    },
    async cancelMentorRequest() {
      this.requestingMentor = true;
      try {
        const res = await fetch("/api/auth/mentor-request", { method: "DELETE" });
        if (res.ok) this.user = await res.json();
      } catch (e) {
        /* ignore */
      } finally {
        this.requestingMentor = false;
      }
    },
    async logout() {
      await fetch("/api/auth/logout", { method: "POST" });
      window.location.href = "/";
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
