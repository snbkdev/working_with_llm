"""Initial catalog data — seeded into the DB on first run if empty.

Hierarchy: category → subcategory → technology → course (with author).
Subcategories may carry a "technologies" list; each technology a "courses" list.
Subcategories without "technologies" simply show no courses yet in the UI.
"""

# Реальные видео-курсы с YouTube (проверенные ID каналов freeCodeCamp и др.).
# Каждый урок проигрывает видео по "youtube_id" с начала. Уроки — это оглавление
# (главы) одного длинного видео: точных таймкодов глав у нас нет, поэтому урок не
# перематывает видео, а показывает, что в нём разбирается.
# Курс привязывается к существующей технологии по пути category/subcategory/technology.


def _yt(category, subcategory, technology, *, id, title, author, duration, description, chapters):
    """Собрать запись видео-курса. Это одно длинное видео, поэтому курс = один
    урок с полным видео; разбираемые темы перечислены в описании урока (реальных
    таймкодов глав у нас нет, дробить на отдельные уроки нечестно)."""
    return {
        "category": category, "subcategory": subcategory, "technology": technology,
        "youtube_id": id,
        "course": {
            "title": title, "author": author, "duration": duration,
            "url": f"https://www.youtube.com/watch?v={id}", "description": description,
        },
        "lessons": [
            {"title": "Полный видеокурс", "description": "В курсе: " + " · ".join(chapters)},
        ],
    }


SEED_YT_COURSES = [
    # Python и JavaScript заданы вручную — с подробными главами и таймкодами.
    {
        "category": "backend", "subcategory": "python", "technology": "python-basics",
        "course": {
            "title": "Python для начинающих — полный видеокурс (freeCodeCamp)",
            "author": "freeCodeCamp · Mike Dane",
            "duration": "4 ч 26 мин",
            "url": "https://www.youtube.com/watch?v=rfscVS0vtbw",
            "description": "Бесплатный курс: синтаксис, типы, функции и ООП — одно видео, разбитое на уроки-главы.",
        },
        "lessons": [
            {"title": "Полный видеокурс",
             "description": "В курсе: введение и установка Python · переменные и типы "
                            "данных · строки и числа · списки, кортежи и словари · "
                            "условия и циклы · функции · классы и объекты (ООП)"},
        ],
        "youtube_id": "rfscVS0vtbw",
    },
    {
        "category": "frontend", "subcategory": "javascript", "technology": "js-core",
        "course": {
            "title": "JavaScript — полный видеокурс для начинающих (freeCodeCamp)",
            "author": "freeCodeCamp · Beau Carnes",
            "duration": "3 ч 26 мин",
            "url": "https://www.youtube.com/watch?v=PkZNo7MFNFg",
            "description": "Основы JavaScript с нуля: переменные, функции, объекты и работа с DOM.",
        },
        "lessons": [
            {"title": "Полный видеокурс",
             "description": "В курсе: введение в JavaScript · переменные и операторы · "
                            "функции · массивы и объекты · условия и циклы"},
        ],
        "youtube_id": "PkZNo7MFNFg",
    },

    # Остальные курсы — через хелпер (главы с общими таймкодами).
    _yt("frontend", "react", "react-core", id="bMknfKXIFA8",
        title="React для начинающих — видеокурс (freeCodeCamp)",
        author="freeCodeCamp", duration="1 ч 48 мин",
        description="Основы React: компоненты, пропсы, состояние и хуки.",
        chapters=["Введение в React", "JSX и компоненты", "Пропсы и состояние (useState)",
                  "Хуки и эффекты (useEffect)", "Списки, события и формы"]),
    _yt("frontend", "vue", "vue3", id="FXpIoQ_rT_c",
        title="Vue.js — видеокурс для начинающих (freeCodeCamp)",
        author="freeCodeCamp", duration="3 ч 21 мин",
        description="Vue с нуля: шаблоны, реактивность, компоненты и Composition API.",
        chapters=["Введение во Vue", "Шаблоны и реактивность", "Директивы и события",
                  "Компоненты и пропсы", "Composition API"]),
    _yt("frontend", "html", "html5", id="kUMe1FH4CHE",
        title="HTML — полный видеокурс (freeCodeCamp)",
        author="freeCodeCamp", duration="2 ч 06 мин",
        description="Разметка страниц с нуля: теги, структура, ссылки, формы и семантика.",
        chapters=["Введение в HTML", "Теги и структура страницы", "Текст, ссылки и изображения",
                  "Списки и таблицы", "Формы и семантика"]),
    _yt("frontend", "css", "css3", id="OXGznpKZ_sA",
        title="CSS — полный видеокурс (freeCodeCamp)",
        author="freeCodeCamp", duration="1 ч 25 мин",
        description="Стили с нуля: селекторы, блочная модель, Flexbox и адаптивность.",
        chapters=["Введение в CSS", "Селекторы и свойства", "Блочная модель",
                  "Flexbox", "Адаптивность и медиазапросы"]),
    _yt("databases", "sql-basics", "sql", id="HXV3zeQKqGY",
        title="SQL — полный видеокурс (freeCodeCamp)",
        author="freeCodeCamp · Mike Dane", duration="4 ч 20 мин",
        description="Запросы к базам данных: SELECT, WHERE, JOIN, агрегаты и подзапросы.",
        chapters=["Введение и первая база", "SELECT и фильтрация (WHERE)", "Сортировка и агрегаты",
                  "Объединения таблиц (JOIN)", "Группировка и подзапросы"]),
    _yt("backend", "java", "java-basics", id="A74TOX803D0",
        title="Java для начинающих — полный видеокурс (freeCodeCamp)",
        author="freeCodeCamp", duration="2 ч 30 мин",
        description="Основы Java: синтаксис, типы, циклы, методы и ООП.",
        chapters=["Введение и установка JDK", "Переменные и типы", "Условия и циклы",
                  "Методы и массивы", "Классы и объекты (ООП)"]),
    _yt("backend", "csharp", "csharp-basics", id="GhQdlIFylQ8",
        title="C# — полный видеокурс для начинающих (freeCodeCamp)",
        author="freeCodeCamp", duration="4 ч 30 мин",
        description="Язык C# с нуля: переменные, циклы, методы и объектно-ориентированный подход.",
        chapters=["Введение и установка .NET", "Переменные и типы", "Условия и циклы",
                  "Методы и массивы", "Классы и ООП"]),
    _yt("backend", "go", "go-basics", id="YS4e4q9oBaU",
        title="Go (Golang) — видеокурс для начинающих (freeCodeCamp)",
        author="freeCodeCamp", duration="6 ч 25 мин",
        description="Go с нуля: типы, функции, структуры, интерфейсы и конкурентность.",
        chapters=["Введение и установка Go", "Переменные и типы", "Функции и пакеты",
                  "Структуры и интерфейсы", "Горутины и каналы"]),
    _yt("backend", "php", "php-basics", id="OK_JCtrrv-c",
        title="PHP — полный видеокурс (freeCodeCamp)",
        author="freeCodeCamp", duration="4 ч 37 мин",
        description="PHP с нуля: синтаксис, циклы, функции, массивы и обработка форм.",
        chapters=["Введение в PHP", "Переменные и типы", "Условия и циклы",
                  "Функции и массивы", "Формы и работа с данными"]),
    _yt("backend", "python", "django", id="F5mRW0jo-U4",
        title="Django — полный видеокурс (freeCodeCamp)",
        author="freeCodeCamp", duration="3 ч 44 мин",
        description="Веб-фреймворк Django: проект, модели, представления, шаблоны и админка.",
        chapters=["Введение и установка Django", "Проект и приложения", "Модели и миграции",
                  "Представления и маршруты", "Шаблоны и админка"]),
    _yt("backend", "python", "flask", id="Z1RJmh_OqeA",
        title="Flask — полный видеокурс (freeCodeCamp)",
        author="freeCodeCamp", duration="4 ч 07 мин",
        description="Микрофреймворк Flask: маршруты, шаблоны, формы и работа с БД.",
        chapters=["Введение и первый роут", "Маршруты и шаблоны", "Формы и запросы",
                  "Работа с базой данных", "Финальное приложение"]),
    _yt("devops", "docker", "docker-core", id="fqMOX6JJhGo",
        title="Docker для начинающих — видеокурс (freeCodeCamp)",
        author="freeCodeCamp", duration="2 ч 10 мин",
        description="Контейнеризация с нуля: образы, контейнеры, Dockerfile и Docker Compose.",
        chapters=["Введение в контейнеры", "Установка Docker", "Образы и контейнеры",
                  "Dockerfile", "Docker Compose"]),
    _yt("mobile", "android", "kotlin-android", id="EExSSotojVI",
        title="Kotlin — полный видеокурс для начинающих (freeCodeCamp)",
        author="freeCodeCamp", duration="2 ч 08 мин",
        description="Язык Kotlin с нуля: переменные, функции, классы и ООП.",
        chapters=["Введение и установка", "Переменные и типы", "Условия и циклы",
                  "Функции", "Классы и ООП"]),
]


# Курсы, которые добавляются простой YouTube-ССЫЛКОЙ (без ручных таймкодов).
# Чтобы добавить курс: укажите направление (category/subcategory/technology —
# слаги из SEED_CATEGORIES), название, автора и список уроков, где каждый урок —
# это просто ссылка на видео. Ссылка может быть любой:
#   https://youtu.be/ID   |   https://www.youtube.com/watch?v=ID&t=1m30s   |   ID
# Таймкод (t=/start=) распознаётся автоматически. Курс появится под направлением,
# урок будет проигрывать видео по ссылке.
SEED_LINK_COURSES = [
    {
        "category": "backend", "subcategory": "python", "technology": "fastapi",
        "title": "FastAPI — разработка API (freeCodeCamp)",
        "author": "freeCodeCamp · Sanjeev Thiyagarajan", "duration": "19 ч",
        "description": "Полный курс по FastAPI: маршруты, Pydantic, база данных и аутентификация.",
        "lessons": [
            {"title": "Полный курс FastAPI", "url": "https://youtu.be/0sOvCWFmrtA"},
        ],
    },
    {
        "category": "backend", "subcategory": "java", "technology": "spring-boot",
        "title": "Spring Boot — полный курс (Amigoscode)",
        "author": "Amigoscode", "duration": "5 ч 40 мин",
        "description": "Spring Boot с нуля: REST, JPA, зависимости и структура приложения.",
        "lessons": [
            {"title": "Полный курс Spring Boot", "url": "https://www.youtube.com/watch?v=9SGDpanrc8U"},
        ],
    },
    {
        "category": "data-science", "subcategory": "data-analysis", "technology": "pandas",
        "title": "Анализ данных на Python: NumPy и Pandas",
        "author": "freeCodeCamp · Keith Galli", "duration": "5 ч",
        "description": "Два видео-урока: обзорный курс анализа данных и практический Pandas.",
        "lessons": [
            {"title": "Анализ данных: NumPy, Pandas, Matplotlib", "url": "https://youtu.be/r-uOLxNrNk8"},
            {"title": "Практика Pandas (Keith Galli)", "url": "https://www.youtube.com/watch?v=vmEHCJofslg"},
        ],
    },
    {
        "category": "ui-ux", "subcategory": "figma", "technology": "figma-core",
        "title": "Figma за 24 минуты (AJ&Smart)",
        "author": "AJ&Smart", "duration": "24 мин",
        "description": "Быстрый старт в Figma: интерфейс, фреймы, компоненты и авто-лейаут.",
        "lessons": [
            {"title": "Введение в Figma", "url": "https://youtu.be/FTFaQWZBqQ8"},
        ],
    },
    {
        "category": "devops", "subcategory": "linux", "technology": "linux-admin",
        "title": "Linux для начинающих (freeCodeCamp)",
        "author": "freeCodeCamp", "duration": "5 ч 18 мин",
        "description": "Основы Linux: терминал, файловая система, права и процессы.",
        "lessons": [
            {"title": "Полный курс Linux", "url": "https://www.youtube.com/watch?v=sWbUDq4S6Y8"},
        ],
    },
    {
        "category": "gamedev", "subcategory": "unity", "technology": "unity-core",
        "title": "Unity для начинающих (freeCodeCamp)",
        "author": "freeCodeCamp", "duration": "5 ч 32 мин",
        "description": "Разработка игр на Unity и C#: сцены, объекты, скрипты и физика.",
        "lessons": [
            {"title": "Полный курс Unity", "url": "https://youtu.be/gB1F9G0JXOo"},
        ],
    },
]


# Банк вопросов для тестов (QUIZ MODE), привязка к технологии по пути.
# У каждого варианта: text, correct (по умолчанию False), explanation — объяснение,
# почему вариант верный/неверный. Порядок вариантов на экране перемешивается.
SEED_QUESTIONS = [
    {
        "category": "backend", "subcategory": "python", "technology": "python-basics",
        "questions": [
            {
                "text": "Как правильно объявить переменную со строкой в Python?",
                "options": [
                    {"text": 'name = "Иван"', "correct": True,
                     "explanation": "Верно: имя = значение, строка в кавычках."},
                    {"text": 'String name = "Иван";', "explanation": "Это синтаксис Java, не Python."},
                    {"text": 'var name = "Иван"', "explanation": "var — это JavaScript, в Python его нет."},
                    {"text": 'let name = "Иван"', "explanation": "let — тоже JavaScript, не Python."},
                ],
            },
            {
                "text": "Какой тип данных вернёт выражение 3 / 2 в Python 3?",
                "options": [
                    {"text": "float (1.5)", "correct": True,
                     "explanation": "В Python 3 оператор / всегда даёт float."},
                    {"text": "int (1)", "explanation": "Целочисленное деление — это //, а не /."},
                    {"text": "str ('1.5')", "explanation": "Деление возвращает число, а не строку."},
                    {"text": "Ошибка", "explanation": "Деление чисел допустимо, ошибки не будет."},
                ],
            },
            {
                "text": "Как объявить функцию в Python?",
                "options": [
                    {"text": "def greet():", "correct": True,
                     "explanation": "Функции объявляются ключевым словом def."},
                    {"text": "function greet() {}", "explanation": "Это синтаксис JavaScript."},
                    {"text": "func greet() {}", "explanation": "func — это Go/Swift, не Python."},
                    {"text": "void greet() {}", "explanation": "Так объявляют методы в Java/C#."},
                ],
            },
            {
                "text": "Какая структура данных изменяемая (mutable)?",
                "options": [
                    {"text": "list", "correct": True,
                     "explanation": "Списки можно изменять после создания."},
                    {"text": "tuple", "explanation": "Кортежи неизменяемые."},
                    {"text": "str", "explanation": "Строки в Python неизменяемые."},
                    {"text": "frozenset", "explanation": "frozenset — неизменяемое множество."},
                ],
            },
            {
                "text": "Как узнать длину списка nums?",
                "options": [
                    {"text": "len(nums)", "correct": True,
                     "explanation": "Встроенная функция len() возвращает количество элементов."},
                    {"text": "nums.length", "explanation": ".length — это JavaScript, не Python."},
                    {"text": "nums.size()", "explanation": "У списка нет метода size()."},
                    {"text": "count(nums)", "explanation": "Глобальной функции count() нет; есть метод list.count(x)."},
                ],
            },
            {
                "text": "Какой индекс у первого элемента списка?",
                "options": [
                    {"text": "0", "correct": True,
                     "explanation": "Индексация в Python начинается с нуля."},
                    {"text": "1", "explanation": "С единицы индексируют в некоторых других языках."},
                    {"text": "-1", "explanation": "-1 — это последний элемент, а не первый."},
                    {"text": "None", "explanation": "Индекс — это число, первый элемент имеет индекс 0."},
                ],
            },
            {
                "text": "Какой оператор возводит число в степень?",
                "options": [
                    {"text": "**", "correct": True,
                     "explanation": "2 ** 3 == 8 — двойная звёздочка это степень."},
                    {"text": "^", "explanation": "^ в Python — это побитовое XOR, а не степень."},
                    {"text": "//", "explanation": "// — целочисленное деление."},
                    {"text": "%%", "explanation": "Такого оператора в Python нет."},
                ],
            },
            {
                "text": "Чему равно 7 // 2?",
                "options": [
                    {"text": "3", "correct": True,
                     "explanation": "// — целочисленное деление, дробная часть отбрасывается."},
                    {"text": "3.5", "explanation": "3.5 даёт обычное деление /, а не //."},
                    {"text": "4", "explanation": "// округляет вниз, а не вверх."},
                    {"text": "1", "explanation": "1 — это остаток (7 % 2), а не результат деления."},
                ],
            },
            {
                "text": "Как добавить элемент в конец списка nums?",
                "options": [
                    {"text": "nums.append(x)", "correct": True,
                     "explanation": "append() добавляет элемент в конец списка."},
                    {"text": "nums.push(x)", "explanation": "push() — это JavaScript, в Python его нет."},
                    {"text": "nums.add(x)", "explanation": "add() есть у множеств (set), не у списков."},
                    {"text": "nums.insert(x)", "explanation": "insert требует индекс: insert(i, x)."},
                ],
            },
            {
                "text": "Что вернёт \"Hello\".lower()?",
                "options": [
                    {"text": "\"hello\"", "correct": True,
                     "explanation": "lower() переводит все буквы в нижний регистр."},
                    {"text": "\"HELLO\"", "explanation": "В верхний регистр переводит upper()."},
                    {"text": "\"Hello\"", "explanation": "lower() меняет регистр, строка не остаётся прежней."},
                    {"text": "Ошибка", "explanation": "lower() — корректный метод строк."},
                ],
            },
            {
                "text": "Как правильно объявить словарь?",
                "options": [
                    {"text": "d = {}", "correct": True,
                     "explanation": "Фигурные скобки создают пустой словарь."},
                    {"text": "d = []", "explanation": "Квадратные скобки создают список."},
                    {"text": "d = ()", "explanation": "Круглые скобки создают кортеж."},
                    {"text": "d = <>", "explanation": "Такого синтаксиса в Python нет."},
                ],
            },
            {
                "text": "Как проверить, есть ли ключ \"id\" в словаре d?",
                "options": [
                    {"text": "\"id\" in d", "correct": True,
                     "explanation": "Оператор in проверяет наличие ключа в словаре."},
                    {"text": "d.has(\"id\")", "explanation": "Метода has() у словаря нет."},
                    {"text": "d.contains(\"id\")", "explanation": "contains() — это не Python."},
                    {"text": "has_key(d, \"id\")", "explanation": "Глобальной has_key нет (метод убрали в Python 3)."},
                ],
            },
            {
                "text": "Что вернёт bool(\"\") (пустая строка)?",
                "options": [
                    {"text": "False", "correct": True,
                     "explanation": "Пустая строка считается «ложной» (falsy)."},
                    {"text": "True", "explanation": "True вернёт непустая строка."},
                    {"text": "\"\"", "explanation": "bool() возвращает True или False, а не строку."},
                    {"text": "Ошибка", "explanation": "bool() принимает любой объект без ошибки."},
                ],
            },
            {
                "text": "Чему равен срез \"python\"[1:4]?",
                "options": [
                    {"text": "\"yth\"", "correct": True,
                     "explanation": "Берутся символы с индексами 1, 2, 3 (4 не включается)."},
                    {"text": "\"pyth\"", "explanation": "Срез начинается с индекса 1, а не 0."},
                    {"text": "\"ytho\"", "explanation": "Правая граница 4 не включается в срез."},
                    {"text": "\"yt\"", "explanation": "Это был бы срез [1:3]."},
                ],
            },
            {
                "text": "Как перебрать числа от 0 до 4 включительно?",
                "options": [
                    {"text": "for i in range(5)", "correct": True,
                     "explanation": "range(5) даёт 0, 1, 2, 3, 4."},
                    {"text": "for i in range(1, 5)", "explanation": "Это 1, 2, 3, 4 — без нуля."},
                    {"text": "for i in range(4)", "explanation": "Это 0, 1, 2, 3 — без четырёх."},
                    {"text": "for i in [0..4]", "explanation": "Синтаксиса [0..4] в Python нет."},
                ],
            },
            {
                "text": "Как преобразовать строку \"42\" в целое число?",
                "options": [
                    {"text": "int(\"42\")", "correct": True,
                     "explanation": "int() преобразует строку в целое число."},
                    {"text": "str(42)", "explanation": "str() наоборот делает из числа строку."},
                    {"text": "parseInt(\"42\")", "explanation": "parseInt — это JavaScript."},
                    {"text": "\"42\".toInt()", "explanation": "Метода toInt() у строк нет."},
                ],
            },
            {
                "text": "Сколько элементов в множестве {1, 2, 2, 3}?",
                "options": [
                    {"text": "3", "correct": True,
                     "explanation": "Множество хранит только уникальные значения, дубли убираются."},
                    {"text": "4", "explanation": "Повторяющаяся 2 в множестве не дублируется."},
                    {"text": "2", "explanation": "Уникальных значений три: 1, 2, 3."},
                    {"text": "Ошибка", "explanation": "Повторы в литерале множества допустимы, ошибки нет."},
                ],
            },
            {
                "text": "Как оформить однострочный комментарий в Python?",
                "options": [
                    {"text": "# комментарий", "correct": True,
                     "explanation": "Комментарии начинаются с символа #."},
                    {"text": "// комментарий", "explanation": "// — это C/JavaScript."},
                    {"text": "/* комментарий */", "explanation": "/* */ — тоже не Python."},
                    {"text": "-- комментарий", "explanation": "-- используется в SQL, не в Python."},
                ],
            },
            {
                "text": "Что вернёт type(3.0)?",
                "options": [
                    {"text": "<class 'float'>", "correct": True,
                     "explanation": "Число с точкой — это тип float."},
                    {"text": "<class 'int'>", "explanation": "int был бы у 3 без точки."},
                    {"text": "<class 'double'>", "explanation": "Типа double в Python нет, дробные — это float."},
                    {"text": "<class 'number'>", "explanation": "Общего типа number в Python нет."},
                ],
            },
            {
                "text": "Чему равно \"ab\" * 3?",
                "options": [
                    {"text": "\"ababab\"", "correct": True,
                     "explanation": "Умножение строки на число повторяет её."},
                    {"text": "\"ab3\"", "explanation": "Число не приписывается к строке."},
                    {"text": "6", "explanation": "Строка не превращается в число."},
                    {"text": "Ошибка", "explanation": "str * int — допустимая операция."},
                ],
            },
            {
                "text": "Что делает оператор == ?",
                "options": [
                    {"text": "Сравнивает значения", "correct": True,
                     "explanation": "== проверяет равенство значений и возвращает bool."},
                    {"text": "Присваивает значение", "explanation": "Присваивание — это одиночное =."},
                    {"text": "Сравнивает, один ли это объект", "explanation": "Идентичность объектов проверяет is."},
                    {"text": "Объявляет переменную", "explanation": "Переменную объявляют присваиванием =."},
                ],
            },
        ],
    },
    {
        "category": "frontend", "subcategory": "javascript", "technology": "js-core",
        "questions": [
            {
                "text": "Какое ключевое слово создаёт блочную переменную в современном JS?",
                "options": [
                    {"text": "let", "correct": True,
                     "explanation": "let (и const) создают переменную с блочной областью видимости."},
                    {"text": "var", "explanation": "var имеет функциональную область видимости, не блочную."},
                    {"text": "def", "explanation": "def — это Python."},
                    {"text": "dim", "explanation": "dim — это Visual Basic."},
                ],
            },
            {
                "text": "Что вернёт typeof [] в JavaScript?",
                "options": [
                    {"text": '"object"', "correct": True,
                     "explanation": "Массивы в JS — это объекты, typeof возвращает 'object'."},
                    {"text": '"array"', "explanation": "Отдельного типа 'array' у typeof нет."},
                    {"text": '"list"', "explanation": "Такого типа в JS не существует."},
                    {"text": '"undefined"', "explanation": "Массив определён, это не undefined."},
                ],
            },
            {
                "text": "Как строго сравнить два значения без приведения типов?",
                "options": [
                    {"text": "===", "correct": True,
                     "explanation": "=== сравнивает и значение, и тип, без приведения."},
                    {"text": "==", "explanation": "== приводит типы перед сравнением."},
                    {"text": "=", "explanation": "= — это присваивание, а не сравнение."},
                    {"text": "equals()", "explanation": "У примитивов JS нет метода equals()."},
                ],
            },
            {
                "text": "Как объявить константу в JavaScript?",
                "options": [
                    {"text": "const x = 5", "correct": True,
                     "explanation": "const создаёт переменную, которую нельзя переприсвоить."},
                    {"text": "let x = 5", "explanation": "let создаёт изменяемую переменную, не константу."},
                    {"text": "constant x = 5", "explanation": "Ключевого слова constant в JS нет."},
                    {"text": "final x = 5", "explanation": "final — это Java, не JavaScript."},
                ],
            },
            {
                "text": "Что вернёт typeof null?",
                "options": [
                    {"text": "\"object\"", "correct": True,
                     "explanation": "Это известная историческая особенность JS: typeof null === 'object'."},
                    {"text": "\"null\"", "explanation": "Отдельного типа 'null' у typeof нет."},
                    {"text": "\"undefined\"", "explanation": "undefined и null — разные значения."},
                    {"text": "\"number\"", "explanation": "null — это не число."},
                ],
            },
            {
                "text": "Чему равно 2 + \"2\" в JavaScript?",
                "options": [
                    {"text": "\"22\"", "correct": True,
                     "explanation": "С '+' число приводится к строке, происходит конкатенация."},
                    {"text": "4", "explanation": "Сложения чисел не будет — одна из сторон строка."},
                    {"text": "22", "explanation": "Результат — строка \"22\", а не число."},
                    {"text": "NaN", "explanation": "Конкатенация корректна, NaN не возникает."},
                ],
            },
            {
                "text": "Чему равно \"5\" - 2?",
                "options": [
                    {"text": "3", "correct": True,
                     "explanation": "Оператор '-' приводит строку к числу: 5 - 2 = 3."},
                    {"text": "\"3\"", "explanation": "Результат — число, а не строка."},
                    {"text": "\"52\"", "explanation": "Конкатенация была бы с '+', а не с '-'."},
                    {"text": "NaN", "explanation": "\"5\" успешно приводится к числу 5."},
                ],
            },
            {
                "text": "Как добавить элемент в конец массива arr?",
                "options": [
                    {"text": "arr.push(x)", "correct": True,
                     "explanation": "push() добавляет элемент в конец массива."},
                    {"text": "arr.append(x)", "explanation": "Метода append() у массива нет."},
                    {"text": "arr.add(x)", "explanation": "add() есть у Set, не у массива."},
                    {"text": "arr.pop()", "explanation": "pop() наоборот удаляет последний элемент."},
                ],
            },
            {
                "text": "Что вернёт Boolean(0)?",
                "options": [
                    {"text": "false", "correct": True,
                     "explanation": "0 — «ложное» (falsy) значение."},
                    {"text": "true", "explanation": "true дают ненулевые числа."},
                    {"text": "0", "explanation": "Boolean() возвращает true/false, а не число."},
                    {"text": "NaN", "explanation": "Boolean() не возвращает NaN."},
                ],
            },
            {
                "text": "Чему равно 10 % 3?",
                "options": [
                    {"text": "1", "correct": True,
                     "explanation": "% — остаток от деления: 10 = 3*3 + 1."},
                    {"text": "3", "explanation": "3 — это частное (10 / 3 округлённо), а не остаток."},
                    {"text": "0", "explanation": "10 не делится на 3 без остатка."},
                    {"text": "3.33", "explanation": "% даёт остаток (целое), а не дробное деление."},
                ],
            },
            {
                "text": "Как объявить стрелочную функцию?",
                "options": [
                    {"text": "const f = () => {}", "correct": True,
                     "explanation": "Стрелочная функция: аргументы => тело."},
                    {"text": "const f = function() => {}", "explanation": "Нельзя совмещать function и =>."},
                    {"text": "def f(): {}", "explanation": "def — это Python."},
                    {"text": "func f() {}", "explanation": "func — это Go/Swift, не JS."},
                ],
            },
            {
                "text": "Что вернёт typeof function(){}?",
                "options": [
                    {"text": "\"function\"", "correct": True,
                     "explanation": "Для функций typeof возвращает 'function'."},
                    {"text": "\"object\"", "explanation": "Хотя функции — объекты, typeof выделяет их как 'function'."},
                    {"text": "\"method\"", "explanation": "Типа 'method' у typeof нет."},
                    {"text": "\"undefined\"", "explanation": "Функция определена, это не undefined."},
                ],
            },
            {
                "text": "Что вернёт 1 == \"1\" (нестрогое сравнение)?",
                "options": [
                    {"text": "true", "correct": True,
                     "explanation": "== приводит типы: \"1\" становится числом 1, они равны."},
                    {"text": "false", "explanation": "false было бы при строгом === (разные типы)."},
                    {"text": "NaN", "explanation": "Сравнение возвращает boolean, не NaN."},
                    {"text": "Ошибка", "explanation": "Сравнение допустимо, ошибки нет."},
                ],
            },
            {
                "text": "Как вывести значение в консоль браузера?",
                "options": [
                    {"text": "console.log(x)", "correct": True,
                     "explanation": "console.log() — стандартный вывод в консоль."},
                    {"text": "print(x)", "explanation": "print() — это Python."},
                    {"text": "echo x", "explanation": "echo — это PHP/bash."},
                    {"text": "System.out.println(x)", "explanation": "Это Java."},
                ],
            },
            {
                "text": "Какой метод создаёт новый массив, применяя функцию к каждому элементу?",
                "options": [
                    {"text": "map()", "correct": True,
                     "explanation": "map() возвращает новый массив с преобразованными элементами."},
                    {"text": "forEach()", "explanation": "forEach() просто перебирает и возвращает undefined."},
                    {"text": "filter()", "explanation": "filter() отбирает по условию, а не преобразует."},
                    {"text": "push()", "explanation": "push() добавляет элемент, а не создаёт новый массив."},
                ],
            },
            {
                "text": "Что вернёт [1, 2, 3].indexOf(2)?",
                "options": [
                    {"text": "1", "correct": True,
                     "explanation": "indexOf возвращает индекс первого совпадения; у 2 индекс 1."},
                    {"text": "2", "explanation": "2 — это само значение, а не его индекс."},
                    {"text": "0", "explanation": "0 — индекс элемента 1, а не 2."},
                    {"text": "-1", "explanation": "-1 вернулось бы, если элемента нет в массиве."},
                ],
            },
            {
                "text": "Как получить длину строки s = \"abc\"?",
                "options": [
                    {"text": "s.length", "correct": True,
                     "explanation": "У строк есть свойство length."},
                    {"text": "s.size()", "explanation": "Метода size() у строк нет."},
                    {"text": "len(s)", "explanation": "len() — это Python."},
                    {"text": "s.count", "explanation": "Свойства count у строки нет."},
                ],
            },
            {
                "text": "Для чего нужен JSON.stringify()?",
                "options": [
                    {"text": "Превратить объект в JSON-строку", "correct": True,
                     "explanation": "stringify сериализует объект в строку JSON."},
                    {"text": "Разобрать JSON-строку в объект", "explanation": "Разбором занимается JSON.parse()."},
                    {"text": "Скопировать массив", "explanation": "Это не задача JSON.stringify."},
                    {"text": "Округлить число", "explanation": "К числам и округлению отношения не имеет."},
                ],
            },
            {
                "text": "Что вернёт typeof undefined?",
                "options": [
                    {"text": "\"undefined\"", "correct": True,
                     "explanation": "У значения undefined тип тоже 'undefined'."},
                    {"text": "\"object\"", "explanation": "'object' возвращает typeof null, а не undefined."},
                    {"text": "\"null\"", "explanation": "Типа 'null' у typeof нет."},
                    {"text": "\"none\"", "explanation": "Типа 'none' в JS не существует."},
                ],
            },
        ],
    },
]


# Код-челленджи (CODE CHALLENGE MODE). Пользователь решает задачу сам (есть
# черновик кода, он не проверяется) и присылает получившийся результат — сервер
# сверяет его с эталоном (`answer`) без запуска кода. `answer_kind`: 'number' |
# 'text'; несколько допустимых ответов можно перечислить через '|'.
SEED_CHALLENGES = [
    {
        "category": "backend", "subcategory": "python", "technology": "python-basics",
        "challenges": [
            {
                "title": "Сумма от 1 до N", "difficulty": "easy",
                "prompt": "Посчитайте сумму всех целых чисел от 1 до N включительно "
                          "и введите получившееся число.",
                "sample_input": "N = 100",
                "starter_code": "def solve(n):\n    return sum(range(1, n + 1))\n\nprint(solve(100))",
                "hint": "Сумма арифметической прогрессии: n * (n + 1) / 2.",
                "answer": "5050", "answer_kind": "number",
                "explanation": "sum(range(1, 101)) = 100 * 101 / 2 = 5050.",
            },
            {
                "title": "Факториал числа", "difficulty": "easy",
                "prompt": "Вычислите факториал N (произведение всех чисел от 1 до N) "
                          "и введите результат.",
                "sample_input": "N = 6",
                "starter_code": "import math\n\nprint(math.factorial(6))",
                "hint": "6! = 1·2·3·4·5·6.",
                "answer": "720", "answer_kind": "number",
                "explanation": "6! = 720.",
            },
            {
                "title": "Сколько гласных", "difficulty": "medium",
                "prompt": "Посчитайте количество гласных букв (a, e, i, o, u) в слове "
                          "«education» и введите число.",
                "sample_input": 'word = "education"',
                "starter_code": 'word = "education"\nvowels = "aeiou"\n'
                                'print(sum(1 for ch in word if ch in vowels))',
                "hint": "Пройдитесь по буквам и считайте те, что входят в «aeiou».",
                "answer": "5", "answer_kind": "number",
                "explanation": "Гласные в «education»: e, u, a, i, o — всего 5.",
            },
            {
                "title": "Разворот строки", "difficulty": "medium",
                "prompt": "Разверните строку «python» задом наперёд и введите результат.",
                "sample_input": 's = "python"',
                "starter_code": 's = "python"\nprint(s[::-1])',
                "hint": "Срез со шагом -1: s[::-1].",
                "answer": "nohtyp", "answer_kind": "text",
                "explanation": "«python»[::-1] = «nohtyp».",
            },
        ],
    },
    {
        "category": "frontend", "subcategory": "javascript", "technology": "js-core",
        "challenges": [
            {
                "title": "Сумма массива", "difficulty": "easy",
                "prompt": "Посчитайте сумму элементов массива [5, 8, 13, 21] и введите "
                          "получившееся число.",
                "sample_input": "arr = [5, 8, 13, 21]",
                "starter_code": "const arr = [5, 8, 13, 21];\n"
                                "console.log(arr.reduce((a, b) => a + b, 0));",
                "hint": "Используйте reduce для накопления суммы.",
                "answer": "47", "answer_kind": "number",
                "explanation": "5 + 8 + 13 + 21 = 47.",
            },
            {
                "title": "Чётные числа", "difficulty": "medium",
                "prompt": "Сколько чётных чисел в массиве [1, 2, 3, 4, 5]? Введите число "
                          "(результат [1,2,3,4,5].filter(x => x % 2 === 0).length).",
                "sample_input": "arr = [1, 2, 3, 4, 5]",
                "starter_code": "const arr = [1, 2, 3, 4, 5];\n"
                                "console.log(arr.filter(x => x % 2 === 0).length);",
                "hint": "Чётные — это 2 и 4.",
                "answer": "2", "answer_kind": "number",
                "explanation": "Чётные числа: 2 и 4 — их 2.",
            },
            {
                "title": "Подсчёт символа", "difficulty": "medium",
                "prompt": "Сколько раз буква «a» встречается в строке «javascript is "
                          "amazing»? Введите число.",
                "sample_input": 's = "javascript is amazing"',
                "starter_code": 'const s = "javascript is amazing";\n'
                                'console.log(s.split("").filter(c => c === "a").length);',
                "hint": "Разбейте строку на символы и посчитайте совпадения.",
                "answer": "4", "answer_kind": "number",
                "explanation": "«jAvAscript is AmAzing» — буква «a» встречается 4 раза.",
            },
        ],
    },
]


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
