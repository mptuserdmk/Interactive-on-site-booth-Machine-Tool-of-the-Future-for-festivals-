from typing import Dict, Any, List
from app.quiz.combinations import combination_manager

QUESTIONS = [
    {
        "id": "element",
        "step": 1,
        "title": "ВЫБЕРИ СТИХИЮ",
        "subtitle": "Что ближе твоему будущему производству?",
        "options": [
            {"id": "space", "name": "Космос", "icon": "🚀", "hint": "Орбитальные комплексы и спутники"},
            {"id": "atom", "name": "Атом", "icon": "⚛️", "hint": "Квантовая физика и чистая энергия"},
            {"id": "robots", "name": "Роботы", "icon": "🤖", "hint": "Кибернетика и искусственный интеллект"},
            {"id": "medicine", "name": "Медицина", "icon": "🧬", "hint": "Биотехнологии и бионика"},
            {"id": "metal", "name": "Металл", "icon": "⚙️", "hint": "Лазеры и сверхпрочные сплавы"}
        ]
    },
    {
        "id": "power",
        "step": 2,
        "title": "ВЫБЕРИ СУПЕРСИЛУ",
        "subtitle": "Какое главное качество инженера ведёт тебя вперёд?",
        "options": [
            {"id": "precision", "name": "Точность", "icon": "🎯", "hint": "Наносекундный расчёт без права на ошибку"},
            {"id": "speed", "name": "Скорость", "icon": "⚡", "hint": "Сверхбыстрое реагирование и запуск"},
            {"id": "power", "name": "Сила", "icon": "💪", "hint": "Управление мегаваттами чистой мощи"},
            {"id": "mind", "name": "Ум", "icon": "🧠", "hint": "Стратегический расчёт и нейросети"},
            {"id": "care", "name": "Забота", "icon": "🛡️", "hint": "Абсолютная безопасность и экология"}
        ]
    },
    {
        "id": "color",
        "step": 3,
        "title": "ВЫБЕРИ ЦВЕТ",
        "subtitle": "Какой оттенок отразит энергетику твоего станка?",
        "options": [
            {"id": "azure", "name": "Лазурный", "hex": "#00d2ff", "glow": "rgba(0, 210, 255, 0.7)"},
            {"id": "gold", "name": "Золотой", "hex": "#ffd700", "glow": "rgba(255, 215, 0, 0.7)"},
            {"id": "emerald", "name": "Изумрудный", "hex": "#00ff88", "glow": "rgba(0, 255, 136, 0.7)"},
            {"id": "white", "name": "Белый", "hex": "#ffffff", "glow": "rgba(255, 255, 255, 0.7)"}
        ]
    }
]

_VALID_ANSWERS = {q["id"]: {opt["id"] for opt in q["options"]} for q in QUESTIONS}


def get_questions_schema() -> List[Dict[str, Any]]:
    return QUESTIONS


def is_valid_answer(question_type: str, answer_id: str) -> bool:
    return answer_id in _VALID_ANSWERS.get(question_type, set())

def resolve_answers(element: str, power: str, color: str) -> Dict[str, Any]:
    combo = combination_manager.find(element, power, color)
    if not combo:
        raise ValueError(f"Invalid choice combination: {element} + {power} + {color}")
    return combo
