import sys

# Verificação de dependência crítica antes de carregar o restante
try:
    import face_recognition_models
except ImportError as e:
    print(f"\n[ERRO CRÍTICO] Falha ao importar 'face_recognition_models': {e}")
    print("Isso geralmente ocorre por incompatibilidade com versões novas do Python.")
    print("Tente executar no terminal:\n")
    print("    pip install \"setuptools<70\"")
    print("    pip install --force-reinstall face-recognition-models")
    sys.exit(1)

from src.camera import CameraManager
from src.storage import StorageManager
from src.recognition import FaceRecognizer
from src.alert import AlertSystem

def run_training_mode():
    print("--- MODO TREINAMENTO ---")
    print("Pressione 'c' para capturar a foto e cadastrar um nome.")
    print("Pressione 'q' para sair.")
    
    camera = CameraManager()
    storage = StorageManager()

    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                break

            camera.show_frame("Treinamento - Pressione 'c'", frame)
            key = camera.wait_key()

            if key == ord('q'):
                break
            elif key == ord('c'):
                # Pausa visualmente ou fecha momentaneamente para input
                name = input("Digite o nome do indivíduo: ").strip()
                if name:
                    storage.save_known_face(frame, name)
                else:
                    print("Nome inválido, foto descartada.")
    finally:
        camera.close()

def run_surveillance_mode():
    print("--- MODO VIGILÂNCIA ---")
    print("Monitorando... Pressione 'q' para encerrar.")
    
    storage = StorageManager()
    # Carrega dados antes de iniciar a câmera
    known_encodings, known_names = storage.load_known_faces()
    
    if not known_encodings:
        print("AVISO: Nenhum rosto conhecido encontrado em 'data/known'. O modo vigilância considerará todos como desconhecidos.")

    camera = CameraManager()
    recognizer = FaceRecognizer()
    alert = AlertSystem()

    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                break

            # Processamento de reconhecimento
            detections = recognizer.process_frame(frame, known_encodings, known_names)

            for (top, right, bottom, left, name) in detections:
                color = (0, 255, 0) # Verde para conhecidos
                
                if name == "Desconhecido":
                    color = (0, 0, 255) # Vermelho para desconhecidos
                    alert.trigger_alert()
                    saved_path = storage.save_unknown_event(frame)
                    # Opcional: Evitar spam de logs/salvamento (logica simples aqui)
                    # alert.log_intrusion(saved_path) 
                
                camera.draw_box_and_text(frame, top, right, bottom, left, name, color)

            camera.show_frame("Vigilancia", frame)

            if camera.wait_key() == ord('q'):
                break
    finally:
        camera.close()

def main():
    print("Bem-vindo ao Reconhecedor de Faces")
    print("1 - Modo Treinamento (Cadastrar rostos)")
    print("2 - Modo Vigilância (Monitorar)")
    
    choice = input("Escolha uma opção: ")

    if choice == '1':
        run_training_mode()
    elif choice == '2':
        run_surveillance_mode()
    else:
        print("Opção inválida.")

if __name__ == "__main__":
    main()