from aiogram.fsm.state import StatesGroup, State

class AdForm(StatesGroup):
    photos = State()         # Шаг 1: Фотографии (сначала вовлекаем юзера)
    size_category = State()  # Шаг 2: Категория (Одежда/Обувь/Аксессуары)
    price = State()          # Шаг 3: Цена
    title = State()          # Шаг 4: Название и описание
    size = State()           # Шаг 5: Размер (зависит от категории)
    condition = State()      # Шаг 6: Состояние (Новое/Б/У)
    defect = State()         # Шаг 7: Наличие дефектов
    confirm = State()        # Шаг 8: Проверка и публикация

class Register(StatesGroup):
    language = State()
    phone = State()