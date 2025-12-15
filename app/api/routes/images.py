# app/api/routes/images.py
import os
import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
from typing import Optional

router = APIRouter()

# Критическое исправление пути:
# Было: BASE_DIR = Path(__file__).resolve().parent.parent.parent  # app/api/routes -> app
# Стало: добавить еще один .parent чтобы выйти в project_main
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # app/api/routes -> app -> project_main

FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_DIR = FRONTEND_DIR / "static" / "images"

print(f"=== DEBUG PATH INFO ===")  # Для отладки
print(f"Script: {__file__}")
print(f"BASE_DIR: {BASE_DIR}")
print(f"FRONTEND_DIR: {FRONTEND_DIR}")
print(f"UPLOAD_DIR: {UPLOAD_DIR}")
print(f"UPLOAD_DIR exists: {os.path.exists(UPLOAD_DIR)}")

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/admin/upload_image")
async def upload_image(
    file: UploadFile = File(...),
    filename: Optional[str] = Form(None)
):
    print(f"=== UPLOAD CALLED ===")
    print(f"Uploading to: {UPLOAD_DIR}")
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Файл должен быть изображением")

    # ... остальной код без изменений ...
    # Определяем безопасное имя файла
    if filename and '/' not in filename and '.' in filename:
        safe_name = "".join(c for c in filename if c.isalnum() or c in "._-").rstrip()
        if not safe_name:
            safe_name = None
    else:
        safe_name = None
    
    if not safe_name:
        original_name = file.filename
        if original_name and '.' in original_name:
            ext = os.path.splitext(original_name)[1].lower()
            base_name = os.path.splitext(original_name)[0]
            safe_base = "".join(c for c in base_name if c.isalnum() or c in "._-").rstrip()
            safe_name = f"{safe_base}{ext}" if safe_base else f"{int(time.time()*1000)}{ext}"
        else:
            ext = ".jpg"
            safe_name = f"{int(time.time()*1000)}{ext}"
    
    # Убедимся, что имя уникально
    counter = 1
    original_safe_name = safe_name
    while os.path.exists(os.path.join(UPLOAD_DIR, safe_name)):
        name_without_ext, ext = os.path.splitext(original_safe_name)
        safe_name = f"{name_without_ext}_{counter}{ext}"
        counter += 1
    
    # Сохраняем файл
    filepath = os.path.join(UPLOAD_DIR, safe_name)
    
    try:
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
        print(f"✅ File saved to CORRECT path: {filepath}")
    except Exception as e:
        print(f"❌ Save error: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")
    
    # Путь для БД в формате /images/имя_файла.jpg
    public_path = f"/images/{safe_name}"
    
    return {
        "success": True,
        "image_path": public_path,
        "filename": safe_name
    }