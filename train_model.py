from ultralytics import YOLO

def train_defect_detector():
    # 1. Выбираем модель. 
    # 'n' (nano) — самая быстрая, идеальна для Edge-устройств (Raspberry/Jetson)
    model = YOLO('yolov8n.pt') 

    # 2. Запускаем обучение
    results = model.train(
        data='data.yaml', # Путь к твоему конфигу
        epochs=50,                         # Для начала хватит, чтобы увидеть прогресс
        imgsz=640,                         # Стандартное разрешение для YOLO
        device='cpu',                        # '0' если есть NVIDIA (CUDA), иначе 'cpu'
        project='industrial_aoi',          # Имя проекта для логов
        name='v1_initial_test'             # Имя конкретного запуска
    )

    print("Обучение завершено. Модель сохранена в runs/detect/v1_initial_test/weights/best.pt")

if __name__ == "__main__":
    train_defect_detector()