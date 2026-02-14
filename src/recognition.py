import face_recognition
import cv2
import numpy as np

class FaceRecognizer:
    """Responsável pela lógica de detecção e comparação de faces."""

    def __init__(self):
        pass

    def process_frame(self, frame, known_encodings, known_names):
        """
        Processa o frame para encontrar faces e identificar nomes.
        Retorna uma lista de tuplas (top, right, bottom, left, name).
        """
        # Redimensiona para 1/4 do tamanho para processamento mais rápido
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        results = []
        for face_encoding, location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            name = "Desconhecido"

            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_names[best_match_index]
            
            # Escala as coordenadas de volta para o tamanho original (x4)
            top, right, bottom, left = location
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            
            results.append((top, right, bottom, left, name))
        
        return results