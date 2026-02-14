import cv2

class CameraManager:
    """Responsável apenas pela captura de vídeo e exibição de janelas."""
    
    def __init__(self, source=0):
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise Exception("Não foi possível abrir a câmera.")

    def get_frame(self):
        """Lê um frame da câmera."""
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def show_frame(self, window_name, frame):
        """Exibe o frame em uma janela."""
        cv2.imshow(window_name, frame)

    def close(self):
        """Libera recursos."""
        self.cap.release()
        cv2.destroyAllWindows()

    def wait_key(self, delay=1):
        """Wrapper para waitKey do OpenCV."""
        return cv2.waitKey(delay) & 0xFF

    def draw_box_and_text(self, frame, top, right, bottom, left, text, color=(0, 255, 0)):
        """Desenha o retângulo e o nome no frame."""
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, text, (left, bottom + 20), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)