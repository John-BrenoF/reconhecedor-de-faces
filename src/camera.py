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

    def set_brightness(self, value):
        """Define o brilho da câmera (geralmente entre 0 e 255, ou 0.0 e 1.0 dependendo da câmera)."""
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)

    def setup_window(self, window_name):
        """Cria a janela explicitamente para permitir configurações de callback."""
        cv2.namedWindow(window_name)

    def set_mouse_callback(self, window_name, callback):
        """Define a função que será chamada quando houver cliques do mouse."""
        cv2.setMouseCallback(window_name, callback)

    def draw_button(self, frame, text, x, y, w, h, color):
        """Desenha um botão interativo na tela."""
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, -1)
        cv2.putText(frame, text, (x + 10, y + 25), cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 0), 1)

    def draw_text_input(self, frame, text, x, y, w, h):
        """Desenha uma caixa de texto para entrada de dados."""
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), -1)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 0), 2)
        cv2.putText(frame, text, (x + 10, y + 35), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 0), 1)

    def apply_filter(self, frame, filter_id):
        """Aplica filtros visuais no frame."""
        if filter_id == 1: # Escala de Cinza (mantendo 3 canais para compatibilidade)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        elif filter_id == 2: # Bordas (Canny)
            edges = cv2.Canny(frame, 100, 200)
            return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        elif filter_id == 3: # Invertido (Negativo)
            return cv2.bitwise_not(frame)
        return frame # 0 = Normal

    def create_video_writer(self, filepath, fps, width, height):
        """Cria um objeto para salvar vídeo."""
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        return cv2.VideoWriter(filepath, fourcc, fps, (width, height))

    def get_resolution(self):
        """Retorna largura e altura da câmera."""
        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return w, h