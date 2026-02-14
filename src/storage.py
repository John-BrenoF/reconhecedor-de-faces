import os
import cv2
import face_recognition
from datetime import datetime

class StorageManager:
    """Responsável pela persistência de dados (salvar/carregar imagens)."""

    def __init__(self, base_dir="data"):
        self.base_dir = base_dir
        self.known_dir = os.path.join(base_dir, "known")
        self.unknown_dir = os.path.join(base_dir, "unknown")
        
        os.makedirs(self.known_dir, exist_ok=True)
        os.makedirs(self.unknown_dir, exist_ok=True)

    def save_known_face(self, frame, name):
        """Salva a foto de uma pessoa conhecida."""
        # Cria uma pasta para a pessoa se não existir, ou salva direto com o nome
        filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        path = os.path.join(self.known_dir, filename)
        cv2.imwrite(path, frame)
        print(f"Dados de '{name}' salvos em {path}")

    def save_unknown_event(self, frame):
        """Salva a foto de um desconhecido (vigilância)."""
        filename = f"INTRUSO_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        path = os.path.join(self.unknown_dir, filename)
        cv2.imwrite(path, frame)
        return path

    def load_known_faces(self):
        """Carrega todas as faces conhecidas da pasta data/known."""
        known_encodings = []
        known_names = []

        print("Carregando banco de dados de faces...")
        for filename in os.listdir(self.known_dir):
            if filename.endswith((".jpg", ".png", ".jpeg")):
                filepath = os.path.join(self.known_dir, filename)
                image = face_recognition.load_image_file(filepath)
                encodings = face_recognition.face_encodings(image)
                
                if encodings:
                    known_encodings.append(encodings[0])
                    # Assume que o nome do arquivo é o nome da pessoa (ex: joao_123.jpg -> joao)
                    name = filename.split('_')[0]
                    known_names.append(name)
        
        return known_encodings, known_names