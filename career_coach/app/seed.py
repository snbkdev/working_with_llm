"""Initial catalog data — seeded into the DB on first run if empty.

Hierarchy: category → subcategory → technology → course (with author).
Subcategories may carry a "technologies" list; each technology a "courses" list.
Subcategories without "technologies" simply show no courses yet in the UI.
"""

SEED_CATEGORIES = [
    {
        "slug": "backend", "title": "Backend", "icon": "🛠️", "color": "#5d3fd3",
        "description": "Серверная разработка и языки программирования",
        "subcategories": [
            {
                "slug": "python", "title": "Python",
                "description": "Синтаксис, ООП, стандартная библиотека",
                "technologies": [
                    {
                        "slug": "python-basics", "title": "Python (основы языка)",
                        "description": "Изучение самого языка без фреймворков",
                        "courses": [
                            {"title": "Python с нуля до Junior", "author": "Сергей Балакирев",
                             "duration": "30 ч", "url": "", "description": "Синтаксис, ООП, проекты"},
                            {"title": "Поколение Python: курс для начинающих", "author": "Тимур Гуев",
                             "duration": "20 ч", "url": "", "description": "Фундамент языка, много практики"},
                            {"title": "Python Pro: продвинутый уровень", "author": "Артём Егоров",
                             "duration": "25 ч", "url": "", "description": "Декораторы, генераторы, асинхронность"},
                        ],
                    },
                    {
                        "slug": "fastapi", "title": "FastAPI",
                        "description": "Современный async-фреймворк для API",
                        "courses": [
                            {"title": "FastAPI с нуля до продакшена", "author": "Артём Шумейко",
                             "duration": "14 ч", "url": "", "description": "REST API, async, тесты, деплой"},
                            {"title": "FastAPI: полный курс", "author": "Tim Ruscica (Tech With Tim)",
                             "duration": "8 ч", "url": "", "description": "Маршруты, Pydantic, базы данных"},
                            {"title": "Production-Ready FastAPI", "author": "Sebastián Ramírez",
                             "duration": "6 ч", "url": "", "description": "Лучшие практики от автора фреймворка"},
                        ],
                    },
                    {
                        "slug": "django", "title": "Django",
                        "description": "Батарейки в комплекте, ORM, админка",
                        "courses": [
                            {"title": "Django для профессионалов", "author": "William S. Vincent",
                             "duration": "12 ч", "url": "", "description": "Проекты, деплой, безопасность"},
                            {"title": "Django + DRF: REST API", "author": "Сергей Балакирев",
                             "duration": "10 ч", "url": "", "description": "Django REST Framework на практике"},
                        ],
                    },
                    {
                        "slug": "flask", "title": "Flask",
                        "description": "Лёгкий микрофреймворк",
                        "courses": [
                            {"title": "Flask Mega-Tutorial", "author": "Miguel Grinberg",
                             "duration": "16 ч", "url": "", "description": "Классический пошаговый курс"},
                            {"title": "Flask с нуля", "author": "Corey Schafer",
                             "duration": "7 ч", "url": "", "description": "Блог-приложение шаг за шагом"},
                        ],
                    },
                ],
            },
            {
                "slug": "java", "title": "Java", "description": "JVM, ООП, экосистема",
                "technologies": [
                    {
                        "slug": "java-basics", "title": "Java (основы языка)",
                        "description": "Изучение самого языка без фреймворков",
                        "courses": [
                            {"title": "Java для начинающих", "author": "Сергей Кахоров",
                             "duration": "28 ч", "url": "", "description": "Синтаксис, ООП, коллекции"},
                            {"title": "Программирование на Java", "author": "Тимофей Хирьянов",
                             "duration": "22 ч", "url": "", "description": "Академический курс с практикой"},
                        ],
                    },
                    {
                        "slug": "spring-boot", "title": "Spring Boot",
                        "description": "Промышленный фреймворк для Java",
                        "courses": [
                            {"title": "Spring Boot: полный курс", "author": "Сергей Кахоров",
                             "duration": "20 ч", "url": "", "description": "REST, JPA, Security"},
                            {"title": "Spring Boot in Action", "author": "Amigoscode",
                             "duration": "9 ч", "url": "", "description": "Практический backend на Java"},
                        ],
                    },
                ],
            },
            {
                "slug": "go", "title": "Go", "description": "Горутины, простота, производительность",
                "technologies": [
                    {
                        "slug": "go-basics", "title": "Go (основы)",
                        "description": "Язык, конкурентность, стандартная библиотека",
                        "courses": [
                            {"title": "Learn Go Programming", "author": "Jon Calhoun",
                             "duration": "11 ч", "url": "", "description": "От синтаксиса до веб-сервисов"},
                            {"title": "Golang с нуля", "author": "Nic Jackson",
                             "duration": "8 ч", "url": "", "description": "Горутины, каналы, HTTP"},
                        ],
                    },
                ],
            },
            {
                "slug": "csharp", "title": "C#", "description": ".NET и язык C#",
                "technologies": [
                    {
                        "slug": "csharp-basics", "title": "C# (основы языка)",
                        "description": "Изучение самого языка без фреймворков",
                        "courses": [
                            {"title": "C# Basics для начинающих", "author": "Mosh Hamedani",
                             "duration": "10 ч", "url": "", "description": "Синтаксис и основы ООП"},
                            {"title": "Программирование на C#", "author": "Дмитрий Охрименко",
                             "duration": "18 ч", "url": "", "description": "Язык от азов до практики"},
                        ],
                    },
                    {
                        "slug": "aspnet", "title": "ASP.NET Core",
                        "description": "Веб-фреймворк на .NET",
                        "courses": [
                            {"title": "C# и ASP.NET Core с нуля", "author": "Сергей Нежинский",
                             "duration": "16 ч", "url": "", "description": "От синтаксиса до веб-API"},
                            {"title": "C# Advanced", "author": "Mosh Hamedani",
                             "duration": "9 ч", "url": "", "description": "Глубокое погружение в C#"},
                        ],
                    },
                ],
            },
            {
                "slug": "php", "title": "PHP", "description": "Веб-бэкенд на PHP",
                "technologies": [
                    {
                        "slug": "php-basics", "title": "PHP (основы языка)",
                        "description": "Изучение самого языка без фреймворков",
                        "courses": [
                            {"title": "PHP для начинающих", "author": "Юрий Прудник",
                             "duration": "14 ч", "url": "", "description": "Синтаксис, формы, работа с БД"},
                        ],
                    },
                    {
                        "slug": "laravel", "title": "Laravel",
                        "description": "Самый популярный PHP-фреймворк",
                        "courses": [
                            {"title": "Laravel с нуля", "author": "Brad Schiff",
                             "duration": "12 ч", "url": "", "description": "MVC, Eloquent, Blade"},
                            {"title": "PHP и Laravel на практике", "author": "Виктор Грязин",
                             "duration": "10 ч", "url": "", "description": "Реальные проекты"},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "slug": "databases", "title": "Базы данных", "icon": "🗄️", "color": "#0ea5e9",
        "description": "Хранение данных и работа с СУБД",
        "subcategories": [
            {
                "slug": "sql-basics", "title": "SQL основы",
                "description": "SELECT, JOIN, агрегаты",
                "technologies": [
                    {
                        "slug": "sql", "title": "SQL",
                        "description": "Язык запросов к реляционным БД",
                        "courses": [
                            {"title": "SQL для начинающих", "author": "Владимир Жадан",
                             "duration": "6 ч", "url": "", "description": "Запросы, JOIN, группировки"},
                            {"title": "The Complete SQL Bootcamp", "author": "Jose Portilla",
                             "duration": "9 ч", "url": "", "description": "PostgreSQL и аналитика"},
                        ],
                    },
                ],
            },
            {
                "slug": "postgresql", "title": "PostgreSQL",
                "description": "Возможности и администрирование",
                "technologies": [
                    {
                        "slug": "postgres", "title": "PostgreSQL",
                        "description": "Продвинутая работа и администрирование",
                        "courses": [
                            {"title": "PostgreSQL с нуля", "author": "Hettie Dombrovskaya",
                             "duration": "10 ч", "url": "", "description": "Индексы, планы, оптимизация"},
                        ],
                    },
                ],
            },
            {
                "slug": "db-design", "title": "Проектирование БД",
                "description": "Нормализация, схемы, связи",
                "technologies": [
                    {
                        "slug": "data-modeling", "title": "Моделирование данных",
                        "description": "Нормальные формы, ER-диаграммы",
                        "courses": [
                            {"title": "Проектирование баз данных", "author": "Илья Космодемьянский",
                             "duration": "7 ч", "url": "", "description": "Схемы, связи, нормализация"},
                        ],
                    },
                ],
            },
            {
                "slug": "db-optimization", "title": "Оптимизация",
                "description": "Индексы, планы запросов",
                "technologies": [
                    {
                        "slug": "query-tuning", "title": "Оптимизация запросов",
                        "description": "Индексы, EXPLAIN, планы выполнения",
                        "courses": [
                            {"title": "SQL Performance Explained", "author": "Markus Winand",
                             "duration": "8 ч", "url": "", "description": "Как работают индексы"},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "slug": "frontend", "title": "Frontend", "icon": "🎨", "color": "#f59e0b",
        "description": "Интерфейсы в браузере",
        "subcategories": [
            {
                "slug": "html", "title": "HTML", "description": "Разметка и семантика",
                "technologies": [
                    {
                        "slug": "html5", "title": "HTML5",
                        "description": "Семантика, формы, доступность",
                        "courses": [
                            {"title": "HTML и CSS с нуля", "author": "Владилен Минин",
                             "duration": "6 ч", "url": "", "description": "Базовая верстка страниц"},
                        ],
                    },
                ],
            },
            {
                "slug": "css", "title": "CSS", "description": "Стили, верстка, адаптив",
                "technologies": [
                    {
                        "slug": "css3", "title": "CSS / Flexbox / Grid",
                        "description": "Современная верстка и адаптив",
                        "courses": [
                            {"title": "Современный CSS", "author": "Kevin Powell",
                             "duration": "9 ч", "url": "", "description": "Flexbox, Grid, анимации"},
                        ],
                    },
                ],
            },
            {
                "slug": "javascript", "title": "JavaScript",
                "description": "Язык, DOM, события",
                "technologies": [
                    {
                        "slug": "js-core", "title": "JavaScript (ядро)",
                        "description": "Язык, асинхронность, DOM",
                        "courses": [
                            {"title": "JavaScript с нуля", "author": "Владилен Минин",
                             "duration": "12 ч", "url": "", "description": "ES6+, промисы, fetch"},
                            {"title": "The Complete JavaScript Course", "author": "Jonas Schmedtmann",
                             "duration": "20 ч", "url": "", "description": "Глубокий курс с проектами"},
                        ],
                    },
                ],
            },
            {
                "slug": "vue", "title": "Vue", "description": "Реактивность и компоненты",
                "technologies": [
                    {
                        "slug": "vue3", "title": "Vue 3",
                        "description": "Composition API, реактивность",
                        "courses": [
                            {"title": "Vue 3: полный курс", "author": "Maximilian Schwarzmüller",
                             "duration": "14 ч", "url": "", "description": "Компоненты, роутер, Pinia"},
                        ],
                    },
                ],
            },
            {
                "slug": "react", "title": "React", "description": "Компоненты, хуки, JSX",
                "technologies": [
                    {
                        "slug": "react-core", "title": "React",
                        "description": "Хуки, состояние, контекст",
                        "courses": [
                            {"title": "React с нуля", "author": "Владилен Минин",
                             "duration": "13 ч", "url": "", "description": "Хуки, роутер, запросы"},
                            {"title": "React — The Complete Guide", "author": "Maximilian Schwarzmüller",
                             "duration": "40 ч", "url": "", "description": "Большой курс с проектами"},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "slug": "data-science", "title": "Data Science / ML", "icon": "📊", "color": "#10b981",
        "description": "Анализ данных и машинное обучение",
        "subcategories": [
            {
                "slug": "data-analysis", "title": "Анализ данных",
                "description": "Pandas, NumPy, визуализация",
                "technologies": [
                    {
                        "slug": "pandas", "title": "Pandas",
                        "description": "Обработка табличных данных",
                        "courses": [
                            {"title": "Pandas на практике", "author": "Глеб Михайлов",
                             "duration": "8 ч", "url": "", "description": "DataFrame, группировки, графики"},
                        ],
                    },
                ],
            },
            {
                "slug": "ml", "title": "Машинное обучение",
                "description": "Классические модели",
                "technologies": [
                    {
                        "slug": "sklearn", "title": "scikit-learn",
                        "description": "Классические ML-модели",
                        "courses": [
                            {"title": "Машинное обучение с нуля", "author": "Андрей Созыкин",
                             "duration": "15 ч", "url": "", "description": "Регрессия, классификация, метрики"},
                            {"title": "Machine Learning A-Z", "author": "Kirill Eremenko",
                             "duration": "30 ч", "url": "", "description": "Полный курс по ML"},
                        ],
                    },
                ],
            },
            {
                "slug": "deep-learning", "title": "Нейросети", "description": "Глубокое обучение",
                "technologies": [
                    {
                        "slug": "pytorch", "title": "PyTorch",
                        "description": "Глубокое обучение на PyTorch",
                        "courses": [
                            {"title": "Глубокое обучение на PyTorch", "author": "Сергей Николенко",
                             "duration": "14 ч", "url": "", "description": "Сети, обучение, практика"},
                        ],
                    },
                    {
                        "slug": "tensorflow", "title": "TensorFlow",
                        "description": "Нейросети на TensorFlow/Keras",
                        "courses": [
                            {"title": "TensorFlow Developer", "author": "Daniel Bourke",
                             "duration": "20 ч", "url": "", "description": "От основ до продакшена"},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "slug": "devops", "title": "DevOps", "icon": "⚙️", "color": "#ef4444",
        "description": "Инфраструктура и автоматизация",
        "subcategories": [
            {
                "slug": "linux", "title": "Linux", "description": "Командная строка, основы",
                "technologies": [
                    {
                        "slug": "linux-admin", "title": "Linux",
                        "description": "CLI, права, процессы, bash",
                        "courses": [
                            {"title": "Linux для начинающих", "author": "Дмитрий Кудрявцев",
                             "duration": "10 ч", "url": "", "description": "Терминал, файлы, службы"},
                        ],
                    },
                ],
            },
            {
                "slug": "docker", "title": "Docker", "description": "Контейнеризация",
                "technologies": [
                    {
                        "slug": "docker-core", "title": "Docker",
                        "description": "Контейнеры, образы, compose",
                        "courses": [
                            {"title": "Docker практический курс", "author": "Bret Fisher",
                             "duration": "10 ч", "url": "", "description": "Образы, тома, сети, compose"},
                            {"title": "Docker с нуля", "author": "Слёрм",
                             "duration": "6 ч", "url": "", "description": "Базовая контейнеризация"},
                        ],
                    },
                ],
            },
            {
                "slug": "cicd", "title": "CI/CD", "description": "Пайплайны сборки и доставки",
                "technologies": [
                    {
                        "slug": "github-actions", "title": "GitHub Actions",
                        "description": "Автоматизация сборки и деплоя",
                        "courses": [
                            {"title": "CI/CD с GitHub Actions", "author": "Антон Брайчук",
                             "duration": "6 ч", "url": "", "description": "Пайплайны от и до"},
                        ],
                    },
                ],
            },
            {
                "slug": "cloud", "title": "Облака", "description": "AWS, GCP, инфраструктура",
                "technologies": [
                    {
                        "slug": "aws", "title": "AWS",
                        "description": "Облачная инфраструктура Amazon",
                        "courses": [
                            {"title": "AWS для разработчиков", "author": "Stephane Maarek",
                             "duration": "18 ч", "url": "", "description": "EC2, S3, Lambda и др."},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "slug": "mobile", "title": "Мобильная разработка", "icon": "📱", "color": "#ec4899",
        "description": "Приложения для смартфонов",
        "subcategories": [
            {
                "slug": "android", "title": "Android (Kotlin)",
                "description": "Нативная Android-разработка",
                "technologies": [
                    {
                        "slug": "kotlin-android", "title": "Kotlin / Jetpack Compose",
                        "description": "Современная Android-разработка",
                        "courses": [
                            {"title": "Android-разработка на Kotlin", "author": "Денис Неклюдов",
                             "duration": "20 ч", "url": "", "description": "Compose, архитектура, API"},
                        ],
                    },
                ],
            },
            {
                "slug": "ios", "title": "iOS (Swift)", "description": "Нативная iOS-разработка",
                "technologies": [
                    {
                        "slug": "swift-ios", "title": "Swift / SwiftUI",
                        "description": "Приложения для iOS на Swift",
                        "courses": [
                            {"title": "iOS-разработка на Swift", "author": "Paul Hudson",
                             "duration": "22 ч", "url": "", "description": "SwiftUI, 100 дней практики"},
                        ],
                    },
                ],
            },
            {
                "slug": "flutter", "title": "Flutter", "description": "Кроссплатформа на Dart",
                "technologies": [
                    {
                        "slug": "flutter-core", "title": "Flutter",
                        "description": "UI на Dart для iOS и Android",
                        "courses": [
                            {"title": "Flutter с нуля", "author": "Angela Yu",
                             "duration": "28 ч", "url": "", "description": "Виджеты, состояние, публикация"},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "slug": "gamedev", "title": "GameDev", "icon": "🎮", "color": "#8b5cf6",
        "description": "Разработка игр",
        "subcategories": [
            {
                "slug": "unity", "title": "Unity", "description": "Движок Unity, C#",
                "technologies": [
                    {
                        "slug": "unity-core", "title": "Unity",
                        "description": "2D/3D-игры на C#",
                        "courses": [
                            {"title": "Unity для начинающих", "author": "GameDev tv",
                             "duration": "18 ч", "url": "", "description": "Механики, физика, UI"},
                        ],
                    },
                ],
            },
            {
                "slug": "unreal", "title": "Unreal Engine",
                "description": "Движок Unreal, C++/Blueprints",
                "technologies": [
                    {
                        "slug": "ue5", "title": "Unreal Engine 5",
                        "description": "Blueprints, C++, графика",
                        "courses": [
                            {"title": "Unreal Engine 5 с нуля", "author": "GameDev tv",
                             "duration": "16 ч", "url": "", "description": "Механики и уровни"},
                        ],
                    },
                ],
            },
            {
                "slug": "game-design", "title": "Game Design", "description": "Геймдизайн и механики",
                "technologies": [
                    {
                        "slug": "gd-basics", "title": "Основы геймдизайна",
                        "description": "Механики, баланс, нарратив",
                        "courses": [
                            {"title": "Геймдизайн: теория и практика", "author": "Сергей Гимельрейх",
                             "duration": "8 ч", "url": "", "description": "Как проектировать игры"},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "slug": "ui-ux", "title": "UI/UX-дизайн", "icon": "🎯", "color": "#f43f5e",
        "description": "Проектирование интерфейсов",
        "subcategories": [
            {
                "slug": "ux-basics", "title": "Основы UX", "description": "Исследования, сценарии",
                "technologies": [
                    {
                        "slug": "ux-research", "title": "UX-исследования",
                        "description": "Сценарии, интервью, юзабилити",
                        "courses": [
                            {"title": "Основы UX/UI дизайна", "author": "Эльдар Ишмухаметов",
                             "duration": "9 ч", "url": "", "description": "Исследования и принципы"},
                        ],
                    },
                ],
            },
            {
                "slug": "figma", "title": "Figma", "description": "Макеты и компоненты",
                "technologies": [
                    {
                        "slug": "figma-core", "title": "Figma",
                        "description": "Макеты, компоненты, прототипы",
                        "courses": [
                            {"title": "Figma с нуля", "author": "Артур Абраров",
                             "duration": "7 ч", "url": "", "description": "Интерфейсы, авто-лейаут, библиотеки"},
                        ],
                    },
                ],
            },
            {
                "slug": "prototyping", "title": "Прототипирование",
                "description": "Интерактивные прототипы",
                "technologies": [
                    {
                        "slug": "prototyping-tools", "title": "Прототипирование",
                        "description": "Интерактив в Figma/ProtoPie",
                        "courses": [
                            {"title": "Интерактивные прототипы", "author": "Михаил Греков",
                             "duration": "5 ч", "url": "", "description": "Анимация и переходы"},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "slug": "3d-graphics", "title": "3D и графика", "icon": "🧊", "color": "#06b6d4",
        "description": "3D-моделирование и графика",
        "subcategories": [
            {
                "slug": "blender", "title": "Blender", "description": "Моделирование в Blender",
                "technologies": [
                    {
                        "slug": "blender-core", "title": "Blender",
                        "description": "Моделирование, материалы, рендер",
                        "courses": [
                            {"title": "Blender для начинающих", "author": "Blender Guru",
                             "duration": "12 ч", "url": "", "description": "Знаменитый курс «Пончик»"},
                        ],
                    },
                ],
            },
            {
                "slug": "texturing", "title": "Текстурирование", "description": "Материалы и текстуры",
                "technologies": [
                    {
                        "slug": "substance", "title": "Substance Painter",
                        "description": "PBR-текстуры и материалы",
                        "courses": [
                            {"title": "Текстурирование в Substance Painter", "author": "FlippedNormals",
                             "duration": "10 ч", "url": "", "description": "Материалы для 3D-моделей"},
                        ],
                    },
                ],
            },
            {
                "slug": "rendering", "title": "Рендеринг", "description": "Свет, камеры, рендер",
                "technologies": [
                    {
                        "slug": "blender-render", "title": "Рендеринг в Blender",
                        "description": "Свет, камеры, Cycles/Eevee",
                        "courses": [
                            {"title": "Рендер и свет в Blender", "author": "Blender Guru",
                             "duration": "8 ч", "url": "", "description": "Освещение и финальный рендер"},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "slug": "qa", "title": "QA / Тестирование", "icon": "🧪", "color": "#22c55e",
        "description": "Контроль качества ПО",
        "subcategories": [
            {
                "slug": "qa-basics", "title": "Основы тестирования",
                "description": "Теория, виды тестов",
                "technologies": [
                    {
                        "slug": "testing-theory", "title": "Теория тестирования",
                        "description": "Виды тестов, процессы QA",
                        "courses": [
                            {"title": "Основы тестирования ПО", "author": "Святослав Куликов",
                             "duration": "7 ч", "url": "", "description": "Фундамент для старта в QA"},
                        ],
                    },
                ],
            },
            {
                "slug": "manual", "title": "Ручное тестирование",
                "description": "Тест-кейсы, баг-репорты",
                "technologies": [
                    {
                        "slug": "manual-testing", "title": "Ручное тестирование",
                        "description": "Тест-кейсы, чек-листы, баг-репорты",
                        "courses": [
                            {"title": "Ручное тестирование с нуля", "author": "Артём Русов",
                             "duration": "9 ч", "url": "", "description": "Практика составления тестов"},
                        ],
                    },
                ],
            },
            {
                "slug": "automation", "title": "Автотесты", "description": "Selenium, Playwright",
                "technologies": [
                    {
                        "slug": "playwright", "title": "Playwright",
                        "description": "E2E-автотесты для веба",
                        "courses": [
                            {"title": "Playwright с нуля", "author": "Артём Ерошенко",
                             "duration": "9 ч", "url": "", "description": "Автотесты UI на практике"},
                        ],
                    },
                ],
            },
            {
                "slug": "api-testing", "title": "API-тестирование", "description": "Postman, REST",
                "technologies": [
                    {
                        "slug": "postman", "title": "Postman",
                        "description": "Тестирование REST API",
                        "courses": [
                            {"title": "Тестирование API", "author": "Валентин Яковенко",
                             "duration": "6 ч", "url": "", "description": "Postman, коллекции, автотесты"},
                        ],
                    },
                ],
            },
        ],
    },
]
