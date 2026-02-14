import sys
import cv2  # Necessário para eventos de mouse
import time
import dlib
from datetime import datetime
from multiprocessing import Process, Manager

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
from src.control_panel import launch_panel

# Estado global da aplicação para controle via mouse
app_state = {
    "reload_faces": False,  # Flag para recarregar rostos após cadastro
    "is_typing": False,     # Se está digitando um nome
    "input_text": "",       # Texto sendo digitado
    "captured_frame": None  # Frame congelado para salvar
}

def main():
    print("Iniciando sistema...")
    
    # Inicialização dos módulos
    storage = StorageManager()
    camera = CameraManager()
    camera.set_brightness(150)
    recognizer = FaceRecognizer()
    alert = AlertSystem()
    
    # Configuração do Multiprocessamento para o Painel
    manager = Manager()
    settings = manager.dict({
        "mode": "vigilancia",
        "rec_interval": 4.3,
        "tolerance": 0.6,
        "brightness": 150,
        "filter_id": 0,
        "take_photo": 0,
        "record_video": 0,
        "reload_faces": False
    })
    
    panel_process = Process(target=launch_panel, args=(settings,))
    panel_process.start()

    # Configuração da Janela e Mouse
    WINDOW_NAME = "Reconhecedor Facial"
    camera.setup_window(WINDOW_NAME)

    # Carrega faces conhecidas
    known_encodings, known_names = storage.load_known_faces()
    
    active_trackers = [] # Lista de dicionários: {'tracker': obj, 'name': str}
    prev_frame_time = 0
    last_rec_time = 0
    last_mode = settings["mode"]
    
    # Variáveis de gravação de vídeo
    video_writer = None
    recording_start_time = 0
    is_recording = False

    try:
        while True:
            # Verifica mudança de modo via Painel
            current_mode = settings["mode"]
            if current_mode != last_mode:
                app_state["is_typing"] = False
                print(f"--- Modo alterado para: {current_mode.upper()} ---")
                last_mode = current_mode

            # Aplica brilho (apenas se mudou significativamente para não spammar comando)
            camera.set_brightness(settings["brightness"])

            # 2. Captura Frame
            frame = camera.get_frame()
            if frame is None: break

            # 3. Aplica Filtros (Visual apenas)
            # Nota: O reconhecimento facial idealmente roda na imagem original, 
            # mas para filtros simples como P&B ou Invertido, podemos passar o frame filtrado
            # ou manter uma cópia 'clean_frame' para o reconhecimento se o filtro for muito destrutivo.
            frame = camera.apply_filter(frame, settings["filter_id"])

            # Cálculo de FPS
            curr_time = time.time()
            fps = 1 / (curr_time - prev_frame_time) if prev_frame_time > 0 else 0
            prev_frame_time = curr_time
            cv2.putText(frame, f"FPS: {int(fps)}", (frame.shape[1] - 120, 30), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 255), 1)

            # Exibe o modo atual na tela (apenas texto)
            cv2.putText(frame, f"MODO: {current_mode.upper()}", (20, 40), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0) if current_mode == "vigilancia" else (0, 255, 255), 2)

            # Lógica do Modo VIGILÂNCIA
            if current_mode == "vigilancia":
                # Se houve cadastro recente, recarrega o banco
                if app_state["reload_faces"] or settings.get("reload_faces", False):
                    known_encodings, known_names = storage.load_known_faces()
                    app_state["reload_faces"] = False
                    settings["reload_faces"] = False

                # 1. FASE DE DETECÇÃO (Tempo configurável pelo painel)
                if curr_time - last_rec_time > settings["rec_interval"]:
                    detections = recognizer.process_frame(frame, known_encodings, known_names, tolerance=settings["tolerance"])
                    
                    # Reinicia os rastreadores com as novas posições detectadas
                    active_trackers = []
                    for (top, right, bottom, left, name) in detections:
                        # Usando dlib para tracking (mais robusto que opencv-python puro)
                        tracker = dlib.correlation_tracker()
                        rect = dlib.rectangle(left, top, right, bottom)
                        tracker.start_track(frame, rect)
                        
                        active_trackers.append({"tracker": tracker, "name": name})
                        
                        # Salva no Log CSV
                        storage.log_access(name)

                    last_rec_time = curr_time
                
                # 2. FASE DE RASTREAMENTO (TRACKING) - Nos intervalos
                else:
                    # Atualiza a posição de cada caixa baseada no movimento do vídeo
                    for item in active_trackers:
                        item["tracker"].update(frame)
                        pos = item["tracker"].get_position()
                        
                        left = int(pos.left())
                        top = int(pos.top())
                        right = int(pos.right())
                        bottom = int(pos.bottom())
                        
                        item["box"] = (top, right, bottom, left)

                # Desenha os rastreadores ativos
                for item in active_trackers:
                    if "box" not in item: continue # Se o tracker falhou, pula
                    
                    top, right, bottom, left = item["box"]
                    name = item["name"]
                    color = (0, 255, 0) if name != "Desconhecido" else (0, 0, 255)
                    
                    if name == "Desconhecido":
                        # Alerta apenas se estivermos no ciclo de detecção (para não spammar)
                        if curr_time - last_rec_time < 0.5:
                            alert.trigger_alert()
                            storage.save_unknown_event(frame)
                    
                    camera.draw_box_and_text(frame, top, right, bottom, left, name, color)

            # Lógica do Modo TREINAMENTO
            elif current_mode == "treinamento":
                if app_state["is_typing"]:
                    # Mostra o frame que foi capturado (congelado) ao fundo
                    if app_state["captured_frame"] is not None:
                        frame = app_state["captured_frame"].copy()
                    
                    # Desenha a caixa de texto
                    camera.draw_text_input(frame, f"Nome: {app_state['input_text']}", 20, 100, 400, 50)
                    cv2.putText(frame, "Enter: Salvar | Esc: Cancelar", (20, 170), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 255, 255), 1)
                else:
                    cv2.putText(frame, "Pressione 'c' para capturar", (20, 80), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)

            # --- Lógica do Painel de Controle (Ações) ---
            
            # Tirar Foto
            if settings["take_photo"] == 1:
                filename = f"FOTO_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Foto salva: {filename}")
                settings["take_photo"] = 0

            # Gravar Vídeo (10 segundos)
            if settings["record_video"] == 1 and not is_recording:
                is_recording = True
                recording_start_time = time.time()
                w, h = camera.get_resolution()
                vid_filename = f"VIDEO_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
                video_writer = camera.create_video_writer(vid_filename, 20.0, w, h)
                print(f"Iniciando gravação: {vid_filename}")
                settings["record_video"] = 0

            if is_recording:
                video_writer.write(frame)
                cv2.circle(frame, (frame.shape[1]-30, 30), 10, (0, 0, 255), -1) # Indicador REC
                
                if time.time() - recording_start_time > 10:
                    is_recording = False
                    video_writer.release()
                    print("Gravação finalizada.")

            camera.show_frame(WINDOW_NAME, frame)
            key = camera.wait_key()

            # Se pressionar 'q' e NÃO estiver digitando, sai do programa
            if not app_state["is_typing"] and key == ord('q'):
                break
            
            # Lógica de teclas para o modo TREINAMENTO
            if current_mode == "treinamento":
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
        if panel_process.is_alive():
            panel_process.terminate()
        if video_writer is not None:
            video_writer.release()

if __name__ == "__main__":
    main()