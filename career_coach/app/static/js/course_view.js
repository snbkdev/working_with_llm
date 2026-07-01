// "Watch course" page: plays each lesson's YouTube video and lists the lessons.
const { createApp } = Vue;

const app = createApp({
  data() {
    return { course: null, loading: true, current: null };
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
  },
  methods: {
    select(lesson) {
      if (!lesson.youtube_id) return;
      this.current = lesson;
      // Reflect the chosen lesson in the URL (shareable / refresh-safe).
      const url = new URL(window.location.href);
      url.searchParams.set("lesson", lesson.id);
      window.history.replaceState(null, "", url);
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
      // Pick the lesson from ?lesson=, else the first one that has a video.
      const wanted = Number(new URLSearchParams(window.location.search).get("lesson"));
      this.current =
        this.playable.find((l) => l.id === wanted) || this.playable[0] || null;
    }
    this.loading = false;
  },
});
app.component("app-topbar", AppTopbar);
app.mount("#app");
