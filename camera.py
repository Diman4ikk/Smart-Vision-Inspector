import cv2

class Camera:
    def __init__(self, source=0):
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise ValueError(f"Не удалось открыть источник видео: {source}")

    def get_frame(self):
        ret,frame=self.cap.read()

        if not ret or frame is None:
            return False,None
    
        return True,frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
        