from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "static", "images")
UPLOAD_DIR = os.path.abspath(UPLOAD_DIR)

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    # Проверяем тип
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Можно загружать только изображения")

    # Генерируем уникальное имя
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"

    file_path = os.path.join(UPLOAD_DIR, filename)

    # Сохраняем файл
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Возвращаем путь для БД
    return {
        "filename": filename,
        "image_url": f"/static/images/{filename}",
        "image_path": f"/images/{filename}"
    }
