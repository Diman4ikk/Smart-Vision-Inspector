from fastapi import FastAPI, UploadFile, File, Form
import os
import shutil
from datetime import datetime

app = FastAPI()

# Создаем папку для фото, если нет
os.makedirs("incidents_media", exist_ok=True)

@app.post("/log_incident")
async def log_incident(
    object_type: str = Form(...),
    confidence: str = Form(...),
    timestamp: str = Form(...),
    file: UploadFile = File(...),
    crop: UploadFile = File(...)
):
    # 1. Генерируем уникальное время для имен файлов
    t = datetime.now().strftime('%H%M%S')
    
    # 2. Формируем пути
    full_name = f"full_{t}_{object_type}.jpg"
    crop_name = f"crop_{t}_{object_type}.jpg"
    full_path = os.path.join("incidents_media", full_name)
    crop_path = os.path.join("incidents_media", crop_name)

    # 3. Сохраняем общий кадр
    with open(full_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 4. Сохраняем вырезанный объект (crop)
    with open(crop_path, "wb") as buffer:
        shutil.copyfileobj(crop.file, buffer)

    # 5. Записываем в лог ОДНУ строку со всеми данными
    log_entry = f"{timestamp} | {object_type} | {confidence} | {full_name} | {crop_name}\n"
    with open("incidents_log.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)
        
    print(f"📸 Сохранены кадры для: {object_type}")
    return {"status": "saved", "full": full_name, "crop": crop_name}

if __name__ == "__main__":
    import uvicorn
    # Запускаем сервер на порту 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)