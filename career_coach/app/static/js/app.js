// Vue 3 SPA (CDN global build). Skeleton only: state is local placeholder
// data, the chat hits the stub /api/chat endpoint. No mode/XP logic yet.
const { createApp, nextTick } = Vue;

createApp({
  data() {
    return {
      // meta (loaded from /api/meta)
      goal: "",
      commands: [],
      // gamification placeholders
      xp: 0,
      level: 0,
      streak: 0,
      topicsLearned: 0,
      challengesSolved: 0,
      // navigation
      view: "dashboard",
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
      // placeholder: derived from level progress toward Level 50
      return Math.round((this.level / 50) * 100) || 8;
    },
  },

  async mounted() {
    try {
      const res = await fetch("/api/meta");
      const data = await res.json();
      this.goal = data.goal;
      this.commands = data.commands;
    } catch (e) {
      this.goal = "Стать Python-разработчиком";
    }
  },

  methods: {
    go(view) {
      this.view = view;
      if (view === "chat") this.scrollChat();
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
