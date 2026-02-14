# reconhecedor-de-faces

Projeto pessoal para um reconhecedor de rostos modular em Python, utilizando OpenCV e face_recognition.

## Funcionalidades

1.  **Modo Treinamento**: Captura fotos da webcam e associa a nomes para criar um banco de dados de faces conhecidas.
2.  **Modo Vigilância**: Monitora a câmera em tempo real.
    *   Identifica rostos conhecidos (borda verde).
    *   Detecta intrusos (borda vermelha), emite alerta sonoro e salva a foto automaticamente na pasta `data/unknown`.

## Instalação

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/John-BrenoF/reconhecedor-de-faces.git
    cd reconhecedor-de-faces
    ```

2.  **Crie um Ambiente Virtual (Recomendado):**
    Para evitar erros de "externally-managed-environment" no Linux:
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Linux/Mac
    # ou venv\Scripts\activate no Windows
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
    *Nota: A biblioteca `face_recognition` requer `dlib`.*
    *   **Windows**: Pode ser necessário instalar o CMake e Visual Studio C++ Build Tools.
    *   **Linux (Debian/Ubuntu)**: `sudo apt-get install cmake build-essential`
    *   **Linux (Arch/Manjaro)**: `sudo pacman -S cmake base-devel`

## Uso

Execute o arquivo principal:
```bash
python main.py
