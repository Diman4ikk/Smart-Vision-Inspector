import cv2
import requests
import time
from datetime import datetime
from camera import Camera
from vision import ObjectInspectorV8 
import numpy as np
from tracker import CentroidTracker

# Глобальные переменные для работы с мышью
polygon_points = []      
is_polygon_closed = False 
current_polygon = None   

def draw_polygon(event, x, y, flags, parameters):
    global polygon_points, is_polygon_closed, current_polygon
    
    if event == cv2.EVENT_LBUTTONDOWN:
        # Если полигон уже был закрыт, а мы кликаем снова — начинаем новый
        if is_polygon_closed:
            polygon_points = []
            is_polygon_closed = False
            current_polygon = None
        
        polygon_points.append((x, y))
        print(f"📍 Узел добавлен: ({x}, {y})")
   
    elif event == cv2.EVENT_RBUTTONDOWN:
        # Правый клик — замыкаем (нужно минимум 3 точки)
        if len(polygon_points) >= 3:
            is_polygon_closed = True
            current_polygon = np.array(polygon_points, np.int32).reshape((-1, 1, 2))
            print("✅ Полигон успешно замкнут!")
        else:
            print("⚠️ Нужно минимум 3 точки!")

def main():
    cam = Camera(source=0)
    detector = ObjectInspectorV8("yolov8s.pt")
    last_log_time = 0
    
    window_name = "Smart Inspector V8"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, draw_polygon)
    ct = CentroidTracker(max_disappeared=30)
    sent_ids = set()
    try:
        while True:
            ret, frame = cam.get_frame()
            if not ret: break

            detections = detector.detect(frame, 0.6)
            current_time = time.time()
            incident_found = False
            incident_box = None
            detected_label = ""
            detected_conf = 0
            
            # Координаты объекта для кропа (выносим выше, чтобы были доступны)
            ox, oy, ow, oh = 0, 0, 0, 0
            rects = [obj["box"] for obj in detections] # Собираем все рамки
            tracked_objects = ct.update(rects) # Обновляем трекер
            # 1. Анализ объектов
            for obj in detections:
                ox, oy, ow, oh = obj["box"]
                label = obj["class_name"]
                conf = obj["confidence"]
                color = (0, 255, 0) if label == "person" else (255, 0, 0)
                cv2.rectangle(frame, (ox, oy), (ox + ow, oy + oh), color, 2)
                cv2.putText(frame, f"{label}", (ox, oy - 10), 1, 1, color, 2)

                # Проверка полигона
                cx, cy = ox + ow // 2, oy + oh // 2
                obj_id=None
                    
                for oid , centroid in tracked_objects.items():
                    if abs(cx-centroid[0])< 5 and abs(cy-centroid[1]) <5:
                        obj_id=oid
                        break   

                cv2.putText(frame, f"ID: {obj_id} {label}", (ox, oy - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                if is_polygon_closed and current_polygon is not None:
                    # pointPolygonTest: возвращает >= 0 если внутри
                    if cv2.pointPolygonTest(current_polygon, (cx, cy), False) >= 0:
                        if label != "person" and obj_id not in sent_ids:
                            incident_found = True
                            detected_label = label
                            detected_conf = conf
                            incident_box = (ox, oy, ow, oh)
                            sent_ids.add(obj_id) # СРАЗУ помечаем как отправленный
                            print(f"🎯 Впервые вижу объект ID {obj_id} в зоне!")

            # 2. Логика отправки
            if incident_found and incident_box and (current_time - last_log_time > 3):
                ix, iy, iw, ih = incident_box
                padding = 20
                h_img, w_img, _ = frame.shape
                y1, y2 = max(0, iy-padding), min(h_img, iy+ih+padding)
                x1, x2 = max(0, ix-padding), min(w_img, ix+iw+padding)

                crop_img = frame[y1:y2, x1:x2].copy() # .copy() чтобы не портить основной кадр
                
                # Рисуем на кропе
                l_ox, l_oy = ix - x1, iy - y1
                cv2.rectangle(crop_img, (l_ox, l_oy), (l_ox + ow, l_oy + oh), (0, 0, 255), 2)
                
                _, img_encoded = cv2.imencode('.jpg', frame)
                _, crop_encoded = cv2.imencode('.jpg', crop_img)
                
                try:
                    # ВАЖНО: Добавляем кортежи с именами файлов
                    files = {
                        'file': ('full.jpg', img_encoded.tobytes(), 'image/jpeg'),
                        'crop': ('crop.jpg', crop_encoded.tobytes(), 'image/jpeg')
                    }
                    data = {
                        "object_type": detected_label, 
                        "confidence": f"{detected_conf:.2f}",
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    }
                    
                    response = requests.post("http://127.0.0.1:8000/log_incident", data=data, files=files, timeout=2)
                    
                    if response.status_code == 200:
                        last_log_time = current_time
                        print(f"🚀 Успешно отправлено: {detected_label}")
                    else:
                        print(f"⚠️ Сервер ответил кодом: {response.status_code}")
                
                except Exception as e:
                    print(f"❌ Ошибка при отправке: {e}")

            # 3. ОТРИСОВКА ИНТЕРФЕЙСА (Исправлено)
            if not is_polygon_closed:
                # Пока рисуем — показываем точки и незамкнутые линии
                for pt in polygon_points:
                    cv2.circle(frame, pt, 4, (255, 255, 255), -1)
                if len(polygon_points) > 1:
                    pts_arr = np.array(polygon_points, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(frame, [pts_arr], False, (255, 255, 255), 1)
            
            else:
                # Полигон замкнут — рисуем зону
                z_color = (0, 0, 255) if incident_found else (255, 255, 0)
                cv2.polylines(frame, [current_polygon], True, z_color, 2)
                
                # Полупрозрачная заливка
                overlay = frame.copy()
                cv2.fillPoly(overlay, [current_polygon], z_color)
                cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
                
                if incident_found and len(polygon_points) > 0:
                    cv2.putText(frame, "ALARM!", (polygon_points[0][0], polygon_points[0][1]-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)

            cv2.imshow(window_name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break
    finally:
        cam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()