from fastapi import APIRouter

router = APIRouter(prefix="/news", tags=["News"])

# Заглушка — потом сделаем админку
NEWS = [
    {
        "id": 1,
        "title": "Добро пожаловать!",
        "image": "/images/news1.jpg",
        "text": "Мы обновили меню и добавили новые блюда.",
        "created_at": "2024-01-01"
    },
    {
        "id": 2,
        "title": "Скидка недели",
        "image": "/images/news2.jpg",
        "text": "Скидка 20% на лагман!",
        "created_at": "2024-01-05"
    }
]

@router.get("")
def get_news():
    return {"success": True, "data": NEWS}
