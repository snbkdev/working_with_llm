// "Watch course" page: plays each lesson's video, lets the user mark lessons
// completed, tracks course progress, and offers a self-check quiz after the video.
const { createApp } = Vue;

const app = createApp({
  data() {
    return {
      course: null,
      loading: true,
      current: null,
      user: null,
      completedIds: [], // lesson ids the user has completed
      marking: false,
      selfChecks: [], // self-check questions for the course's technology
      xpToast: "",
    };
  },
  computed: {
    // Lessons that actually have a video attached.
    playable() {
      return (this.course && this.course.lessons || []).filter((l) => l.youtube_id);
    },
    embedUrl() {
      const l = this.current;
      if (!l || !l.youtube_id) return "";
      const params = new URLSearchParams({ rel: "0", modestbranding: "1" });
      if (l.video_start) params.set("start", l.video_start);
      return `https://www.youtube.com/embed/${l.youtube_id}?${params.toString()}`;
    },
    total() {
      return (this.course && this.course.lessons || []).length;
    },
    completedCount() {
      return this.completedIds.length;
    },
    progressPct() {
      return this.total ? Math.round((this.completedCount / this.total) * 100) : 0;
    },
    currentDone() {
      return this.current ? this.isDone(this.current) : false;
    },
  },
  methods: {
    isDone(lesson) {
      return lesson && this.completedIds.includes(lesson.id);
    },
    select(lesson) {
      if (!lesson.youtube_id) return;
      this.current = lesson;
      const url = new URL(window.location.href);
      url.searchParams.set("lesson", lesson.id);
      window.history.replaceState(null, "", url);
    },
    async toggleDone() {
      if (!this.user || !this.current || this.marking) return;
      this.marking = true;
      const id = this.current.id;
      const done = this.isDone(this.current);
      try {
        const res = await fetch(`/api/progress/lessons/${id}`, {
          method: done ? "DELETE" : "POST",
        });
        if (res.ok) {
          const data = await res.json();
          if (data.completed && !this.completedIds.includes(id)) {
            this.completedIds.push(id);
          } else if (!data.completed) {
            this.completedIds = this.completedIds.filter((x) => x !== id);
          }
        }
      } catch (e) {
        /* ignore */
      } finally {
        this.marking = false;
      }
    },
    // --- Self-check (reuses the quiz question bank + answer endpoint) ---
    async answerSelf(q, optionId) {
      if (q.done) return;
      try {
        const res = await fetch("/api/quiz/answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question_id: q.id, option_id: optionId }),
        });
        if (!res.ok) return;
        const data = await res.json();
        q.picked = optionId;
        q.feedback = data;
        if (data.correct) {
          q.done = true;
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
    showToast(text) {
      this.xpToast = text;
      clearTimeout(this._t);
      this._t = setTimeout(() => (this.xpToast = ""), 2500);
    },
    async loadProgress(courseId) {
      try {
        const res = await fetch(`/api/progress/courses/${courseId}`);
        if (res.ok) {
          const data = await res.json();
          this.completedIds = data.completed_lesson_ids || [];
        }
      } catch (e) {
        /* ignore */
      }
    },
    async loadSelfCheck(techId) {
      if (!techId) return;
      try {
        const res = await fetch(`/api/quiz/topics/${techId}/questions`);
        if (res.ok) {
          const data = await res.json();
          this.selfChecks = data.map((q) => ({ ...q, picked: null, feedback: null, done: false }));
        }
      } catch (e) {
        /* ignore */
      }
    },
  },
  async mounted() {
    const m = window.location.pathname.match(/\/course\/(\d+)\/view/);
    const id = m && m[1];
    if (id) {
      try {
        const res = await fetch(`/api/courses/${id}`);
        if (res.ok) this.course = await res.json();
      } catch (e) {
        /* leave course null */
      }
    }
    if (this.course) {
      const wanted = Number(new URLSearchParams(window.location.search).get("lesson"));
      this.current =
        this.playable.find((l) => l.id === wanted) || this.playable[0] || null;

      // Logged-in extras: completion state + self-check questions.
      try {
        const res = await fetch("/api/auth/me");
        if (res.ok) this.user = await res.json();
      } catch (e) {
        /* anonymous */
      }
      if (this.user) {
        await this.loadProgress(this.course.id);
        await this.loadSelfCheck(this.course.technology_id);
      }
    }
    this.loading = false;
  },
});
app.component("app-topbar", AppTopbar);
app.mount("#app");
