from ultralytics import YOLO
import cv2

class ObjectInspectorV8:
    def __init__(self, model_name="yolov8n.pt"):
        print(f"Loading {model_name}...")
        self.model = YOLO(model_name)
        print("YOLOv8 loaded successfully!")

    def detect(self, frame, conf=0.4):
        # verbose=False убирает лишний спам в консоль
        results = self.model(frame, conf=conf, verbose=False)
        
        detections = []
        # Проходим по результатам (YOLOv8 возвращает список объектов Results)
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # Получаем координаты [x1, y1, x2, y2]
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Класс и уверенность
                cls = int(box.cls[0])
                conf_val = float(box.conf[0])
                class_name = self.model.names[cls]
                
                detections.append({
                    "box": [x1, y1, x2 - x1, y2 - y1], # Переводим в [x, y, w, h]
                    "confidence": conf_val,
                    "class_name": class_name
                })
        return detections