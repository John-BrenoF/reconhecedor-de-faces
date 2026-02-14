import sys
import cv2  # Necessário para eventos de mouse
import time

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

# Estado global da aplicação para controle via mouse
app_state = {
    "mode": "vigilancia",  # 'vigilancia' ou 'treinamento'
    "button_rect": (20, 20, 260, 40),  # x, y, w, h do botão
    "reload_faces": False,  # Flag para recarregar rostos após cadastro
    "is_typing": False,     # Se está digitando um nome
    "input_text": "",       # Texto sendo digitado
    "captured_frame": None  # Frame congelado para salvar
}

def mouse_handler(event, x, y, flags, param):
    """Callback para cliques do mouse."""
    if event == cv2.EVENT_LBUTTONDOWN:
        bx, by, bw, bh = app_state["button_rect"]
        # Verifica se clicou dentro da área do botão
        if bx <= x <= bx + bw and by <= y <= by + bh:
            # Alterna o modo
            if app_state["mode"] == "vigilancia":
                app_state["mode"] = "treinamento"
            else:
                app_state["mode"] = "vigilancia"
            app_state["is_typing"] = False # Reseta digitação ao trocar de modo
            print(f"--- Modo alterado para: {app_state['mode'].upper()} ---")

def main():
    print("Iniciando sistema...")
    
    # Inicialização dos módulos
    storage = StorageManager()
    camera = CameraManager()
    camera.set_brightness(150)
    recognizer = FaceRecognizer()
    alert = AlertSystem()

    # Configuração da Janela e Mouse
    WINDOW_NAME = "Reconhecedor Facial"
    camera.setup_window(WINDOW_NAME)
    camera.set_mouse_callback(WINDOW_NAME, mouse_handler)

    # Carrega faces conhecidas
    known_encodings, known_names = storage.load_known_faces()
    
    detections = []
    prev_frame_time = 0
    last_rec_time = 0

    try:
        while True:
            frame = camera.get_frame()
            if frame is None: break

            # Cálculo de FPS
            curr_time = time.time()
            fps = 1 / (curr_time - prev_frame_time) if prev_frame_time > 0 else 0
            prev_frame_time = curr_time
            cv2.putText(frame, f"FPS: {int(fps)}", (frame.shape[1] - 120, 30), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 255), 1)

            # Desenha o botão de troca de modo
            bx, by, bw, bh = app_state["button_rect"]
            if app_state["mode"] == "vigilancia":
                btn_text = "MODO: VIGILANCIA (Clique)"
                btn_color = (0, 255, 0) # Verde
            else:
                btn_text = "MODO: TREINO (Clique)"
                btn_color = (0, 255, 255) # Amarelo
            
            camera.draw_button(frame, btn_text, bx, by, bw, bh, btn_color)

            # Lógica do Modo VIGILÂNCIA
            if app_state["mode"] == "vigilancia":
                # Se houve cadastro recente, recarrega o banco
                if app_state["reload_faces"]:
                    known_encodings, known_names = storage.load_known_faces()
                    app_state["reload_faces"] = False

                # OTIMIZAÇÃO: Processa reconhecimento a cada 6.3 segundos
                if curr_time - last_rec_time > 6.3:
                    detections = recognizer.process_frame(frame, known_encodings, known_names)
                    last_rec_time = curr_time

                for (top, right, bottom, left, name) in detections:
                    color = (0, 255, 0) if name != "Desconhecido" else (0, 0, 255)
                    if name == "Desconhecido":
                        alert.trigger_alert()
                        storage.save_unknown_event(frame)
                    
                    camera.draw_box_and_text(frame, top, right, bottom, left, name, color)

            # Lógica do Modo TREINAMENTO
            elif app_state["mode"] == "treinamento":
                if app_state["is_typing"]:
                    # Mostra o frame que foi capturado (congelado) ao fundo
                    if app_state["captured_frame"] is not None:
                        frame = app_state["captured_frame"].copy()
                    
                    # Desenha a caixa de texto
                    camera.draw_text_input(frame, f"Nome: {app_state['input_text']}", 20, 100, 400, 50)
                    cv2.putText(frame, "Enter: Salvar | Esc: Cancelar", (20, 170), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 255, 255), 1)
                else:
                    cv2.putText(frame, "Pressione 'c' para capturar", (20, 80), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)

            camera.show_frame(WINDOW_NAME, frame)
            key = camera.wait_key()

            # Se pressionar 'q' e NÃO estiver digitando, sai do programa
            if not app_state["is_typing"] and key == ord('q'):
                break
            
            # Lógica de teclas para o modo TREINAMENTO
            if app_state["mode"] == "treinamento":
                if app_state["is_typing"]:
                    if key == 13: # Enter
                        name = app_state["input_text"].strip()
                        if name:
                            storage.save_known_face(app_state["captured_frame"], name)
                            app_state["reload_faces"] = True
                            print(f"Rosto de '{name}' cadastrado com sucesso!")
                        app_state["is_typing"] = False
                        app_state["captured_frame"] = None
                    elif key == 27: # Esc
                        app_state["is_typing"] = False
                        app_state["captured_frame"] = None
                    elif key == 8 or key == 127: # Backspace
                        app_state["input_text"] = app_state["input_text"][:-1]
                    elif 32 <= key <= 126: # Caracteres imprimíveis
                        app_state["input_text"] += chr(key)
                
                elif key == ord('c'):
                    app_state["is_typing"] = True
                    app_state["input_text"] = ""
                    app_state["captured_frame"] = frame.copy() # Congela o frame atual

    finally:
        camera.close()

if __name__ == "__main__":
    main()