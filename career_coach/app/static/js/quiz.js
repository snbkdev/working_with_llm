// Quiz page: pick a topic, answer questions, see explanations, earn XP.
const { createApp } = Vue;

const app = createApp({
  data() {
    return {
      ready: false,
      view: "topics", // 'topics' | 'quiz'
      topics: [],
      topic: null, // active topic
      questions: [],
      loading: false,
      xp: 0,
      level: 0,
      xpToast: "",
    };
  },
  async mounted() {
    let me;
    try {
      const r = await fetch("/api/auth/me");
      if (!r.ok) return (window.location.href = "/login");
      me = await r.json();
    } catch (e) {
      return (window.location.href = "/login");
    }
    this.xp = me.xp;
    this.level = me.level;
    await this.loadTopics();
    this.ready = true;
  },
  methods: {
    async loadTopics() {
      try {
        const r = await fetch("/api/quiz/topics");
        if (r.ok) this.topics = await r.json();
      } catch (e) {
        /* ignore */
      }
    },
    async openTopic(t) {
      this.loading = true;
      this.topic = t;
      this.questions = [];
      try {
        const r = await fetch(`/api/quiz/topics/${t.technology_id}/questions`);
        if (r.ok) {
          const data = await r.json();
          this.questions = data.map((q) => ({
            ...q,
            picked: null,
            feedback: null,
            done: false,
          }));
        }
        this.view = "quiz";
      } catch (e) {
        /* ignore */
      } finally {
        this.loading = false;
      }
    },
    async answer(q, optionId) {
      if (q.done) return; // locked after a correct answer
      try {
        const r = await fetch("/api/quiz/answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question_id: q.id, option_id: optionId }),
        });
        if (!r.ok) return;
        const data = await r.json();
        q.picked = optionId;
        q.feedback = data;
        this.xp = data.xp;
        this.level = data.level;
        if (data.correct) {
          q.done = true;
          q.solved = true;
          if (data.awarded > 0) {
            this.showToast(
              data.leveled_up
                ? `+${data.awarded} XP · Уровень ${data.level}! 🎉`
                : `+${data.awarded} XP`
            );
          }
        }
      } catch (e) {
        /* ignore */
      }
    },
    optionClass(q, opt) {
      if (!q.feedback) return "";
      if (opt.id === q.feedback.correct_option_id) return "correct";
      if (opt.id === q.picked) return "wrong";
      return "";
    },
    explanationFor(q, opt) {
      if (!q.feedback) return "";
      return (q.feedback.explanations || {})[String(opt.id)] || "";
    },
    backToTopics() {
      this.view = "topics";
      this.topic = null;
      this.loadTopics(); // refresh solved counts
    },
    showToast(text) {
      this.xpToast = text;
      clearTimeout(this._t);
      this._t = setTimeout(() => (this.xpToast = ""), 2500);
    },
  },
});
app.component("app-topbar", AppTopbar);
app.component("app-sidebar", AppSidebar);
app.mount("#app");
