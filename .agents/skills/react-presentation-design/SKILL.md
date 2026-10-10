---
name: react-presentation-design
description: >-
  Генерация и верстка интерактивных React-презентаций в неорусском стимпанк/хай-тек дизайне
  («Русская сказка 2.0 / Индустрия чудес»). Создание фиксированных 16:9 слайдов,
  интерактивных переходов, карточек активностей, мастер-классов и расписаний без шаблонных клише.
  Используется для создания интерактивных презентаций, питч-деков, маршрутов квестов и выставочных экранов.
---

# React Presentation Deck Designer — «Русская сказка 2.0 / Индустрия чудес»

Инструкция и стандарт разработки интерактивных презентационных деков на **React + Tailwind CSS / CSS Modules / Framer Motion**.

Визуальная парадигма: **Неорусский стимпанк и хай-тек (Folk-Tech)** — органический синтез традиционных русских мотивов (былины, сказки, филигрань, узоры) и передовой инженерии (станки с ЧПУ, шестерни, латунь, микроэлектроника, голографические элементы).

---

## 1. Архитектура и геометрия презентации (16:9 Canvas)

### 1.1. Фиксированный кадр 16:9
Все слайды рендерятся внутри контейнера со строгим соотношением сторон **16:9** без вертикального скролла:

```tsx
// Базовый контейнер сцены слайда
<div className="relative w-full aspect-video max-w-[1920px] max-h-[1080px] bg-[#FBF8F1] text-[#1E1E1E] overflow-hidden p-8 md:p-12 flex flex-col justify-between border-4 md:border-8 border-[#C59A45]/30 shadow-2xl rounded-2xl select-none">
  {/* Декоративные уголки */}
  <BrassCorners />
  {/* Контент: Header, Body, Footer */}
</div>
```

### 1.2. Анатомия слайда
1. **Header (Шапка)**:
   - Партнерский блок / экосистема (например: «Департамент образования и науки Москвы», название фестиваля).
   - Тематическая локация или рубрикатор.
   - Индикатор прогресса / номер слайда (`03 / 12`).
2. **Body (Холст)**:
   - Асимметричные модульные сетки (5/7, 4/8 или акцентные сплиты).
   - Сочетание двух фактур: пергаментный фон для нарратива + темные графитовые панели с неоновыми индикаторами для «железа» и инженерии.
3. **Footer (Tale-Tech Bar)**:
   - Фирменные слоганы («От традиций к большим возможностям», «Знания • Технологии • Люди • Будущее»).
   - Дата, локация, технические маркеры.
4. **Виньетка и фурнитура**:
   - Латунные и золотые уголки, тонкие 1px разделители (`hairline borders`), акцентные рубиновые штрихи.

---

## 2. Дизайн-токены и цветовая палитра

Никаких случайных HEX-цветов. Используется фирменная семантическая система:

| Название токена | Значение HEX | Роль в интерфейсе |
|---|---|---|
| `parchment` | `#FBF8F1` | Благородный пергаментный фон сцены |
| `parchment-card` | `#F4EEDA` | Подложка карточек легенд и нарратива |
| `gold-brass` | `#C59A45` | Латунь, шестерни, филигранные рамки, акценты |
| `gold-bright` | `#E8CA7B` | Светлое золото для мелких пиктограмм и текста на темном фоне |
| `ruby-red` | `#BA1B1D` | Багрянец, яркие бейджи, маркеры важности, акцентные штрихи |
| `ruby-dark` | `#8C1012` | Глубокий бордовый для статусных плашек |
| `panel-graphite` | `#121820` | Индустриальный графит, панели приборов и станков |
| `panel-surface` | `#1C232D` | Внутренние подложки индустриальных блоков |
| `cyber-cyan` | `#00A3FF` | Неоновые индикаторы телеметрии, ЧПУ, статус «онлайн» |
| `ink-main` | `#1E1E1E` | Основной типографический цвет для светлого фона |
| `ink-muted` | `#686662` | Второстепенный текст, подписи и таймкоды |

### Типографическая формула
- **Заголовки и легенды**: Гарнитуры с засечками / акцидентная антиква (`font-serif`, Merriweather, Playfair, Cormorant). Передают дух книги сказок и былин.
- **Инженерные блоки и ТТХ**: Моноширинный или технологичный гротеск (`font-mono` / clean sans). Передают точность станков, программ и телеметрии.
- **Рукописный штрих**: Курсивные акценты («*Технологии вдохновляют!*») с рубиновым росчерком.

---

## 3. Каталог обязательных архетипов слайдов

### Архетип 1: Title / Cover Slide
- **Назначение**: Главный титульный экран презентации или секции.
- **Состав**:
  - Монументальный заголовок («Русская сказка 2.0: Индустрия чудес»).
  - Бейдж категории («Интерактивный путеводитель фестиваля»).
  - Центральный декоративный арт (анимированная латунная шестеренка с орнаментом).
  - Даты, локация, статус доступа.

### Архетип 2: Concept Slide («Раньше vs Сейчас»)
- **Назначение**: Концептуальное сопоставление сказочного чуда и реальной инженерной профессии.
- **Структура**:
  - Левая колонка («Сказка / Былина»): самоходная печка, щучье веление, ковер-самолет (пергамент, золотой курсив).
  - Правая колонка («Индустрия 2.0 / Хай-тек»): беспилотный транспорт, роботизированные ячейки, композитные материалы (графитовая панель, cyan-индикаторы).

### Архетип 3: Quest Station / Мастер-класс (Masterclass Slide)
- **Назначение**: Паспорт интерактивной зоны / мастер-класса.
- **Обязательные поля**:
  1. Название локации («Лукоморье Технопарка», «Кузница Данилы-Мастера»).
  2. Роль участника (бейдж: «Оператор 5-осевого фрезера», «Биоинженер»).
  3. Блок «Сказочная легенда» (краткий сюжет погружения).
  4. Блок «Инженерная практика» (список 2–3 конкретных действий руками).
  5. Плашка «🎁 Участник уносит с собой» (конкретный физический артефакт).
  6. Индустриальный визуал с шестернями/схемой.

### Архетип 4: Metrics & Logistics Matrix
- **Назначение**: Масштаб мероприятия и ключевые показатели.
- **Сетка**: 3–4 крупных числа с латунным градиентом, микро-подписями и прогресс-барами.

### Архетип 5: Interactive Schedule / Маршрутный лист
- **Назначение**: Тайминг смены групп, перемещение между локациями.
- **Интерактив**: Подсветка текущего слота, переключение потоков («Поток Садко», «Поток Ильи Муромца»).

---

## 4. Анти-паттерны (Anti-Slop Guidelines)

При генерации презентаций категорически **запрещено**:
1. ❌ **Generic AI Gradients**: Никаких размытых сине-фиолетовых градиентов (`bg-gradient-to-r from-purple-500 to-indigo-500`).
2. ❌ **Эмодзи в качестве иконок**: Никаких 🚀, ✨, 🎉 в инженерных плашках. Используйте векторные inline SVG шестеренок, кристаллов, циркулей, микросхем или стилизованные моноширинные глифы.
3. ❌ **Стеклянный китч (Over-glassmorphism)**: Никаких прозрачных карточек с `backdrop-blur-xl`, плавающих в пустоте.
4. ❌ **Скругления 9999px**: Никаких овальных pill-кнопок повсюду; радиусы выверены (`rounded-lg` или строгие скошенные уголки).
5. ❌ **Пустой текст**: Запрещены фразы «Мы меняем мир», «Инновации для всех». Текст должен быть предметным: реальные названия станков (HAAS, Fanuc), сплавов (Д16Т, латунь ЛС59), профессий и артефактов.

---

## 5. Канонические React-компоненты

### 5.1. Декоративные латунные уголки (`BrassCorners.tsx`)
```tsx
export const BrassCorners: React.FC = () => (
  <>
    <div className="absolute top-3 left-3 w-6 h-6 md:w-8 md:h-8 border-t-2 border-l-2 border-[#C59A45] pointer-events-none" />
    <div className="absolute top-3 right-3 w-6 h-6 md:w-8 md:h-8 border-t-2 border-r-2 border-[#C59A45] pointer-events-none" />
    <div className="absolute bottom-3 left-3 w-6 h-6 md:w-8 md:h-8 border-b-2 border-l-2 border-[#C59A45] pointer-events-none" />
    <div className="absolute bottom-3 right-3 w-6 h-6 md:w-8 md:h-8 border-b-2 border-r-2 border-[#C59A45] pointer-events-none" />
  </>
);
```

### 5.2. Слайд станции квеста (`QuestStationSlide.tsx`)
```tsx
import React from 'react';
import { BrassCorners } from './BrassCorners';

export interface QuestStationSlideProps {
  locationTitle: string;
  stationName: string;
  role: string;
  legend: string;
  tasks: string[];
  takeaway: string;
  slideNumber?: string;
}

export const QuestStationSlide: React.FC<QuestStationSlideProps> = ({
  locationTitle,
  stationName,
  role,
  legend,
  tasks,
  takeaway,
  slideNumber = '03 / 12',
}) => {
  return (
    <div className="relative w-full aspect-video bg-[#FBF8F1] text-[#1E1E1E] overflow-hidden p-8 md:p-12 flex flex-col justify-between border-4 md:border-8 border-[#C59A45]/30 shadow-2xl rounded-2xl select-none">
      <BrassCorners />

      {/* Header */}
      <header className="flex justify-between items-center border-b border-[#C59A45]/40 pb-4">
        <div>
          <span className="text-xs font-bold tracking-widest text-[#BA1B1D] uppercase">
            {locationTitle}
          </span>
          <h2 className="text-2xl md:text-3xl font-black tracking-tight text-[#121820] font-serif">
            «{stationName}»
          </h2>
        </div>
        <div className="flex items-center gap-4">
          <span className="px-3 py-1 rounded-md bg-[#BA1B1D]/10 text-[#BA1B1D] text-xs font-bold border border-[#BA1B1D]/30">
            Роль: {role}
          </span>
          <span className="text-xs font-mono text-[#686662]">{slideNumber}</span>
        </div>
      </header>

      {/* Main Body Grid */}
      <main className="grid grid-cols-12 gap-6 my-auto items-stretch">
        <div className="col-span-7 flex flex-col gap-4">
          {/* Легенда */}
          <div className="bg-[#F4EEDA]/80 p-5 rounded-xl border border-[#C59A45]/30 relative">
            <span className="text-[10px] uppercase font-bold tracking-wider text-[#8B651B]">
              Сказочная былина
            </span>
            <p className="mt-1 text-sm italic font-serif leading-relaxed text-[#3B3835]">
              "{legend}"
            </p>
          </div>

          {/* Инженерная практика */}
          <div className="bg-white/95 p-5 rounded-xl border border-[#C59A45]/20 shadow-sm flex-1">
            <span className="text-[10px] uppercase font-bold tracking-wider text-[#BA1B1D]">
              Инженерная практика и манипуляции
            </span>
            <ul className="mt-2 space-y-2">
              {tasks.map((task, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-xs md:text-sm text-[#1E1E1E]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#C59A45] mt-1.5 shrink-0" />
                  <span>{task}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Артефакт с собой */}
          <div className="flex items-center justify-between px-4 py-2.5 bg-[#121820] text-[#E8CA7B] rounded-lg text-xs">
            <span className="font-serif">🎁 Участник уносит в гильдию:</span>
            <span className="font-bold text-white tracking-wide">{takeaway}</span>
          </div>
        </div>

        {/* Технологическая панель (ЧПУ/Стимпанк) */}
        <div className="col-span-5 rounded-xl border-2 border-[#C59A45]/50 bg-[#121820] p-6 flex flex-col justify-between text-white relative overflow-hidden">
          <div className="flex justify-between items-center border-b border-white/10 pb-2">
            <span className="text-[10px] font-mono tracking-widest text-[#00A3FF]">ТЕЛЕМЕТРИЯ СТАНКА</span>
            <span className="w-2 h-2 rounded-full bg-[#00A3FF] animate-pulse" />
          </div>
          <div className="my-auto flex flex-col items-center text-center">
            <svg className="w-20 h-20 text-[#C59A45] animate-spin-slow mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="text-[#E8CA7B] font-mono text-xs uppercase tracking-widest">
              Блок ЧПУ & Латунный привод
            </span>
            <span className="text-[11px] text-white/50 mt-1 font-mono">Точность 0.02 мм • ГОСТ 2.0</span>
          </div>
          <div className="border-t border-white/10 pt-2 flex justify-between text-[10px] font-mono text-[#E8CA7B]">
            <span>СТАТУС: ГОТОВ</span>
            <span>МОЩНОСТЬ: 100%</span>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="flex justify-between items-center pt-3 border-t border-[#C59A45]/30 text-[10px] md:text-[11px] text-[#686662]">
        <span className="tracking-wide">ОТ ТРАДИЦИЙ К БОЛЬШИМ ВОЗМОЖНОСТЯМ</span>
        <span className="font-bold tracking-widest text-[#BA1B1D]">ЗНАНИЯ • ТЕХНОЛОГИИ • ЛЮДИ • БУДУЩЕЕ</span>
        <span>МОСКВА 2026</span>
      </footer>
    </div>
  );
};
```

---

## 6. Чеклист приемки слайда (QA)

Перед сдачей любого слайда или колоды проверьте:
1. Выдержано ли соотношение 16:9 без вылезания контента за пределы экрана?
2. Присутствует ли дуэт текстур: благородный пергамент (`#FBF8F1`) и латунь (`#C59A45`), дополненные графитом (`#121820`)?
3. Читаются ли заголовки как былинно-сказочные, а списки задач — как конкретные инженерные действия?
4. Работает ли навигация (стрелки клавиатуры, клики, свайпы)?
5. Полностью ли исключены AI-slop элементы (эмодзи в кнопках, фиолетовые градиенты, случайные тени)?
