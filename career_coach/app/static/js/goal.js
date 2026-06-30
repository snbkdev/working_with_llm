// Goal drill-down pages. One template renders any level based on the URL:
//   /goal                          → categories
//   /goal/{cat}                    → subcategories
//   /goal/{cat}/{sub}              → technologies
//   /goal/{cat}/{sub}/{tech}       → courses
// Each card is a plain <a> link, so moving a level is a real page navigation.
const { createApp } = Vue;

const app = createApp({
  data() {
    return {
      loading: true,
      error: "",
      items: [],
      crumbs: [],
      title: "",
      subtitle: "",
      accent: "#5d3fd3",
    };
  },
  async mounted() {
    // Path segments after "/goal".
    const segs = window.location.pathname.replace(/^\/goal\/?/, "").split("/").filter(Boolean);
    const [catSlug, subSlug, techSlug] = segs.map(decodeURIComponent);
    try {
      const res = await fetch("/api/categories");
      if (!res.ok) throw new Error();
      const data = await res.json();
      this.build(data.categories || [], catSlug, subSlug, techSlug);
    } catch (e) {
      this.error = "Не удалось загрузить каталог";
    } finally {
      this.loading = false;
    }
  },
  methods: {
    sortTechs(techs) {
      const isCore = (t) => /основ/i.test(t.title) || /основ/i.test(t.description || "");
      return [...(techs || [])].sort((a, b) => (isCore(b) - isCore(a)) || (a.position - b.position));
    },
    build(categories, catSlug, subSlug, techSlug) {
      const cat = catSlug && categories.find((c) => c.slug === catSlug);
      if (catSlug && !cat) return this.notFound("Категория не найдена");
      if (cat) this.accent = cat.color || this.accent;

      // Level 0: categories
      if (!catSlug) {
        this.title = "Выберите направление";
        this.subtitle = "С чего хотите начать путь в IT?";
        this.items = categories.map((c) => ({
          href: `/goal/${c.slug}`, icon: c.icon, title: c.title, desc: c.desc || c.description,
        }));
        return;
      }

      const sub = subSlug && (cat.subcategories || []).find((s) => s.slug === subSlug);
      if (subSlug && !sub) return this.notFound("Подкатегория не найдена");

      // Level 1: subcategories of a category
      if (!subSlug) {
        this.crumbs = [{ href: `/goal/${cat.slug}`, title: cat.title }];
        this.title = cat.title;
        this.subtitle = "Выберите, что именно изучать";
        this.items = (cat.subcategories || []).map((s) => ({
          href: `/goal/${cat.slug}/${s.slug}`, title: s.title, desc: s.description,
        }));
        return;
      }

      const tech = techSlug && this.sortTechs(sub.technologies).find((t) => t.slug === techSlug);
      if (techSlug && !tech) return this.notFound("Технология не найдена");

      // Level 2: technologies of a subcategory
      if (!techSlug) {
        this.crumbs = [
          { href: `/goal/${cat.slug}`, title: cat.title },
          { href: `/goal/${cat.slug}/${sub.slug}`, title: sub.title },
        ];
        this.title = sub.title;
        this.subtitle = "Выберите фреймворк или изучение языка";
        this.items = this.sortTechs(sub.technologies).map((t) => ({
          href: `/goal/${cat.slug}/${sub.slug}/${t.slug}`,
          title: t.title, desc: t.description,
          meta: `${(t.courses || []).length} курс.`,
        }));
        return;
      }

      // Level 3: courses of a technology
      this.crumbs = [
        { href: `/goal/${cat.slug}`, title: cat.title },
        { href: `/goal/${cat.slug}/${sub.slug}`, title: sub.title },
        { href: `/goal/${cat.slug}/${sub.slug}/${tech.slug}`, title: tech.title },
      ];
      this.title = tech.title;
      this.subtitle = "Выберите курс — на следующей странице будет план обучения";
      this.items = (tech.courses || []).map((c) => ({
        href: `/course/${c.id}`,
        title: c.title,
        desc: c.description,
        meta: [c.author, c.duration, c.rating ? `★ ${Number(c.rating).toFixed(1)}` : null]
          .filter(Boolean).join(" · "),
      }));
    },
    notFound(msg) {
      this.error = msg;
    },
  },
});
app.component("app-topbar", AppTopbar);
app.mount("#app");
