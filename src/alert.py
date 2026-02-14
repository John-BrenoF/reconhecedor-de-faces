import sys
import time

class AlertSystem:
    """Responsável por emitir alertas sonoros e logs."""

    def trigger_alert(self):
        """Emite um som de alerta (bip)."""
        # '\a' é o caractere ASCII Bell, funciona na maioria dos terminais
        print('\a', end='', flush=True)
        
        # Se estiver no Windows, pode-se usar winsound (opcional)
        try:
            import winsound
            winsound.Beep(1000, 200) # Frequencia 1000Hz, 200ms
        except ImportError:
            pass

    def log_intrusion(self, path):
        print(f"[ALERTA] Rosto desconhecido detectado! Imagem salva em: {path}")