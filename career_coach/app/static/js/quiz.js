// Quiz page: pick a topic, choose answers for all questions, then press «Сдать».
// Only then are answers graded — with a grade, correct/wrong counts, a breakdown
// of mistakes (link + explanation), and history to track progress over time.
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
      submitting: false,
      submitted: false,
      results: {}, // question_id -> { correct, correct_option_id, picked_option_id, explanations }
      attempt: null, // { correct, total, percent } of the finished run
      history: [], // past attempts for the active topic (newest first)
      xp: 0,
      level: 0,
      xpToast: "",
    };
  },
  computed: {
    answeredCount() {
      return this.questions.filter((q) => q.picked != null).length;
    },
    correctCount() {
      return this.attempt ? this.attempt.correct : 0;
    },
    wrongCount() {
      return this.attempt ? this.attempt.total - this.attempt.correct : 0;
    },
    scorePct() {
      return this.attempt ? this.attempt.percent : 0;
    },
    grade() {
      const p = this.scorePct;
      if (p >= 90) return { ico: "🏆", label: "Отлично", cls: "g-great" };
      if (p >= 75) return { ico: "👍", label: "Хорошо", cls: "g-good" };
      if (p >= 50) return { ico: "🙂", label: "Удовлетворительно", cls: "g-ok" };
      return { ico: "📚", label: "Стоит повторить", cls: "g-low" };
    },
    // Список ошибочных вопросов со ссылкой и пояснением к верному ответу.
    wrongList() {
      const out = [];
      this.questions.forEach((q, i) => {
        const r = this.results[q.id];
        if (r && !r.correct) {
          const correctOpt = q.options.find((o) => o.id === r.correct_option_id);
          out.push({
            id: q.id,
            num: i + 1,
            text: q.text,
            correctText: correctOpt ? correctOpt.text : "",
            explanation: (r.explanations || {})[String(r.correct_option_id)] || "",
          });
        }
      });
      return out;
    },
    // Динамика относительно предыдущей сдачи (history[0] — текущая, [1] — прошлая).
    trend() {
      if (this.history.length < 2) return null;
      const diff = this.history[0].percent - this.history[1].percent;
      if (diff > 0) return { dir: "up", text: `↑ на ${diff}% лучше прошлого раза` };
      if (diff < 0) return { dir: "down", text: `↓ на ${-diff}% хуже прошлого раза` };
      return { dir: "same", text: "= как в прошлый раз" };
    },
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
      this.results = {};
      this.attempt = null;
      this.submitted = false;
      this.history = [];
      try {
        const r = await fetch(`/api/quiz/topics/${t.technology_id}/questions`);
        if (r.ok) {
          const data = await r.json();
          this.questions = data.map((q) => ({ ...q, picked: null }));
        }
        this.view = "quiz";
      } catch (e) {
        /* ignore */
      } finally {
        this.loading = false;
      }
    },
    pick(q, optionId) {
      if (this.submitted) return; // после сдачи менять ответы нельзя
      q.picked = optionId;
    },
    async submit() {
      if (this.submitting || this.submitted || !this.topic) return;
      if (this.answeredCount < this.questions.length) {
        const left = this.questions.length - this.answeredCount;
        if (!confirm(`Без ответа осталось вопросов: ${left}. Сдать тест?`)) return;
      }
      this.submitting = true;
      try {
        const r = await fetch("/api/quiz/submit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            technology_id: this.topic.technology_id,
            answers: this.questions.map((q) => ({ question_id: q.id, option_id: q.picked })),
          }),
        });
        if (!r.ok) return;
        const data = await r.json();
        const map = {};
        (data.results || []).forEach((res) => (map[res.question_id] = res));
        this.results = map;
        this.attempt = { correct: data.correct, total: data.total, percent: data.percent };
        this.submitted = true;
        this.xp = data.xp;
        this.level = data.level;
        if (data.awarded > 0) {
          this.showToast(
            data.leveled_up
              ? `+${data.awarded} XP · Уровень ${data.level}! 🎉`
              : `+${data.awarded} XP`
          );
        }
        await this.loadHistory();
        this.$nextTick(() => {
          const el = document.getElementById("quiz-summary");
          if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      } catch (e) {
        /* ignore */
      } finally {
        this.submitting = false;
      }
    },
    async loadHistory() {
      try {
        const r = await fetch(`/api/quiz/attempts?technology_id=${this.topic.technology_id}`);
        if (r.ok) this.history = await r.json();
      } catch (e) {
        /* ignore */
      }
    },
    retake() {
      if (this.topic) this.openTopic(this.topic); // reload + reshuffle, reset state
    },
    optionClass(q, opt) {
      if (!this.submitted) return q.picked === opt.id ? "picked" : "";
      const r = this.results[q.id];
      if (!r) return "";
      if (opt.id === r.correct_option_id) return "correct";
      if (opt.id === r.picked_option_id) return "wrong";
      return "";
    },
    explanationFor(q, opt) {
      if (!this.submitted) return "";
      const r = this.results[q.id];
      return r ? (r.explanations || {})[String(opt.id)] || "" : "";
    },
    resultOf(q) {
      return this.results[q.id] || null;
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
