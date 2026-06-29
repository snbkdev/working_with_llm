"""Initial catalog data — seeded into the DB on first run if empty."""

SEED_CATEGORIES = [
    {
        "slug": "backend", "title": "Backend", "icon": "🛠️", "color": "#5d3fd3",
        "description": "Серверная разработка и языки программирования",
        "subcategories": [
            {"slug": "python", "title": "Python", "description": "Синтаксис, ООП, стандартная библиотека"},
            {"slug": "java", "title": "Java", "description": "JVM, ООП, экосистема"},
            {"slug": "go", "title": "Go", "description": "Горутины, простота, производительность"},
            {"slug": "csharp", "title": "C#", "description": ".NET и язык C#"},
            {"slug": "php", "title": "PHP", "description": "Веб-бэкенд на PHP"},
        ],
    },
    {
        "slug": "databases", "title": "Базы данных", "icon": "🗄️", "color": "#0ea5e9",
        "description": "Хранение данных и работа с СУБД",
        "subcategories": [
            {"slug": "sql-basics", "title": "SQL основы", "description": "SELECT, JOIN, агрегаты"},
            {"slug": "postgresql", "title": "PostgreSQL", "description": "Возможности и администрирование"},
            {"slug": "db-design", "title": "Проектирование БД", "description": "Нормализация, схемы, связи"},
            {"slug": "db-optimization", "title": "Оптимизация", "description": "Индексы, планы запросов"},
        ],
    },
    {
        "slug": "frontend", "title": "Frontend", "icon": "🎨", "color": "#f59e0b",
        "description": "Интерфейсы в браузере",
        "subcategories": [
            {"slug": "html", "title": "HTML", "description": "Разметка и семантика"},
            {"slug": "css", "title": "CSS", "description": "Стили, верстка, адаптив"},
            {"slug": "javascript", "title": "JavaScript", "description": "Язык, DOM, события"},
            {"slug": "vue", "title": "Vue", "description": "Реактивность и компоненты"},
            {"slug": "react", "title": "React", "description": "Компоненты, хуки, JSX"},
        ],
    },
    {
        "slug": "data-science", "title": "Data Science / ML", "icon": "📊", "color": "#10b981",
        "description": "Анализ данных и машинное обучение",
        "subcategories": [
            {"slug": "data-analysis", "title": "Анализ данных", "description": "Pandas, NumPy, визуализация"},
            {"slug": "ml", "title": "Машинное обучение", "description": "Классические модели"},
            {"slug": "deep-learning", "title": "Нейросети", "description": "Глубокое обучение"},
        ],
    },
    {
        "slug": "devops", "title": "DevOps", "icon": "⚙️", "color": "#ef4444",
        "description": "Инфраструктура и автоматизация",
        "subcategories": [
            {"slug": "linux", "title": "Linux", "description": "Командная строка, основы"},
            {"slug": "docker", "title": "Docker", "description": "Контейнеризация"},
            {"slug": "cicd", "title": "CI/CD", "description": "Пайплайны сборки и доставки"},
            {"slug": "cloud", "title": "Облака", "description": "AWS, GCP, инфраструктура"},
        ],
    },
    {
        "slug": "mobile", "title": "Мобильная разработка", "icon": "📱", "color": "#ec4899",
        "description": "Приложения для смартфонов",
        "subcategories": [
            {"slug": "android", "title": "Android (Kotlin)", "description": "Нативная Android-разработка"},
            {"slug": "ios", "title": "iOS (Swift)", "description": "Нативная iOS-разработка"},
            {"slug": "flutter", "title": "Flutter", "description": "Кроссплатформа на Dart"},
        ],
    },
    {
        "slug": "gamedev", "title": "GameDev", "icon": "🎮", "color": "#8b5cf6",
        "description": "Разработка игр",
        "subcategories": [
            {"slug": "unity", "title": "Unity", "description": "Движок Unity, C#"},
            {"slug": "unreal", "title": "Unreal Engine", "description": "Движок Unreal, C++/Blueprints"},
            {"slug": "game-design", "title": "Game Design", "description": "Геймдизайн и механики"},
        ],
    },
    {
        "slug": "ui-ux", "title": "UI/UX-дизайн", "icon": "🎯", "color": "#f43f5e",
        "description": "Проектирование интерфейсов",
        "subcategories": [
            {"slug": "ux-basics", "title": "Основы UX", "description": "Исследования, сценарии"},
            {"slug": "figma", "title": "Figma", "description": "Макеты и компоненты"},
            {"slug": "prototyping", "title": "Прототипирование", "description": "Интерактивные прототипы"},
        ],
    },
    {
        "slug": "3d-graphics", "title": "3D и графика", "icon": "🧊", "color": "#06b6d4",
        "description": "3D-моделирование и графика",
        "subcategories": [
            {"slug": "blender", "title": "Blender", "description": "Моделирование в Blender"},
            {"slug": "texturing", "title": "Текстурирование", "description": "Материалы и текстуры"},
            {"slug": "rendering", "title": "Рендеринг", "description": "Свет, камеры, рендер"},
        ],
    },
    {
        "slug": "qa", "title": "QA / Тестирование", "icon": "🧪", "color": "#22c55e",
        "description": "Контроль качества ПО",
        "subcategories": [
            {"slug": "qa-basics", "title": "Основы тестирования", "description": "Теория, виды тестов"},
            {"slug": "manual", "title": "Ручное тестирование", "description": "Тест-кейсы, баг-репорты"},
            {"slug": "automation", "title": "Автотесты", "description": "Selenium, Playwright"},
            {"slug": "api-testing", "title": "API-тестирование", "description": "Postman, REST"},
        ],
    },
]
