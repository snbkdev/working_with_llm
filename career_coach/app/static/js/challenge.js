// Code-challenge page: pick a topic, choose a challenge, solve it yourself and
// submit the resulting value. The server compares it to the expected answer.
const { createApp } = Vue;

const app = createApp({
  data() {
    return {
      ready: false,
      view: "topics", // 'topics' | 'list' | 'solve'
      topics: [],
      topic: null, // active topic
      challenges: [],
      challenge: null, // active challenge
      draft: "", // scratch code (not checked)
      answer: "",
      showHint: false,
      feedback: null,
      submitting: false,
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
    diffLabel(d) {
      return { easy: "Лёгкая", medium: "Средняя", hard: "Сложная" }[d] || d;
    },
    async loadTopics() {
      try {
        const r = await fetch("/api/challenges/topics");
        if (r.ok) this.topics = await r.json();
      } catch (e) {
        /* ignore */
      }
    },
    async openTopic(t) {
      this.loading = true;
      this.topic = t;
      this.challenges = [];
      try {
        const r = await fetch(`/api/challenges/topics/${t.technology_id}`);
        if (r.ok) this.challenges = await r.json();
        this.view = "list";
      } catch (e) {
        /* ignore */
      } finally {
        this.loading = false;
      }
    },
    openChallenge(c) {
      this.challenge = c;
      this.draft = c.starter_code || "";
      this.answer = "";
      this.feedback = null;
      this.showHint = false;
      this.view = "solve";
    },
    async submit() {
      if (this.submitting || !this.challenge || this.challenge.solved) return;
      if (!this.answer.trim()) return;
      this.submitting = true;
      try {
        const r = await fetch("/api/challenges/submit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ challenge_id: this.challenge.id, answer: this.answer }),
        });
        if (!r.ok) return;
        const data = await r.json();
        this.feedback = data;
        this.xp = data.xp;
        this.level = data.level;
        if (data.correct) {
          this.challenge.solved = true;
          // reflect the solved state in the list too
          const inList = this.challenges.find((c) => c.id === this.challenge.id);
          if (inList) inList.solved = true;
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
      } finally {
        this.submitting = false;
      }
    },
    backToList() {
      this.view = "list";
      this.challenge = null;
      this.feedback = null;
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
