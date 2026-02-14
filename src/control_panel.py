import json
import os

class ControlPanel:
    """Gerencia a janela de configurações usando GTK 3."""

    def __init__(self, shared_settings, window_name="Painel de Controle"):
        self.settings = shared_settings
        self.load_config()
        self.known_dir = "data/known"
        
        self.window = Gtk.Window(title=window_name)
        self.window.set_border_width(10)
        self.window.set_default_size(300, 600)
        
        # Tenta definir o ícone da janela (coloque um arquivo icon.png na pasta do projeto)
        if os.path.exists("icon.png"):
            self.window.set_icon_from_file("icon.png")
            
        # Fecha o processo GTK quando a janela for fechada
        self.window.connect("destroy", self.on_close)

        # Layout principal
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.window.add(vbox)

        # --- Widgets ---
        
        # Modo de Operação
        vbox.pack_start(Gtk.Label(label="Modo de Operação"), False, False, 0)
        self.combo_mode = Gtk.ComboBoxText()
        self.combo_mode.append("vigilancia", "Vigilância")
        self.combo_mode.append("treinamento", "Treinamento")
        self.combo_mode.set_active_id(self.settings.get("mode", "vigilancia"))
        self.combo_mode.connect("changed", self.on_mode_change)
        vbox.pack_start(self.combo_mode, False, False, 0)
        
        # Intervalo
        vbox.pack_start(Gtk.Label(label="Tempo Reconhecimento (s)"), False, False, 0)
        self.scale_rec = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.5, 10.0, 0.1)
        self.scale_rec.set_value(self.settings.get("rec_interval", 4.3))
        self.scale_rec.connect("value-changed", self.on_rec_change)
        vbox.pack_start(self.scale_rec, False, False, 0)

        # Tolerância
        vbox.pack_start(Gtk.Label(label="Tolerância (%)"), False, False, 0)
        self.scale_tol = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 10, 100, 1)
        self.scale_tol.set_value(self.settings.get("tolerance", 0.6) * 100)
        self.scale_tol.connect("value-changed", self.on_tol_change)
        vbox.pack_start(self.scale_tol, False, False, 0)

        # Brilho
        vbox.pack_start(Gtk.Label(label="Brilho"), False, False, 0)
        self.scale_bri = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 255, 1)
        self.scale_bri.set_value(self.settings.get("brightness", 150))
        self.scale_bri.connect("value-changed", self.on_bri_change)
        vbox.pack_start(self.scale_bri, False, False, 0)

        # Filtro
        vbox.pack_start(Gtk.Label(label="Filtro (0=Normal, 1=Cinza, 2=Borda, 3=Inv)"), False, False, 0)
        self.scale_fil = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 3, 1)
        self.scale_fil.set_digits(0)
        self.scale_fil.set_value(self.settings.get("filter_id", 0))
        self.scale_fil.connect("value-changed", self.on_fil_change)
        vbox.pack_start(self.scale_fil, False, False, 0)

        # Separador
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5)

        # Botões
        self.btn_photo = Gtk.Button(label="📸 Tirar Foto")
        self.btn_photo.connect("clicked", self.on_photo_click)
        vbox.pack_start(self.btn_photo, False, False, 0)

        self.btn_record = Gtk.Button(label="🎥 Gravar 10s")
        self.btn_record.connect("clicked", self.on_record_click)
        vbox.pack_start(self.btn_record, False, False, 0)

        self.btn_reset = Gtk.Button(label="🔄 Restaurar Padrões")
        self.btn_reset.connect("clicked", self.on_reset_click)
        vbox.pack_start(self.btn_reset, False, False, 0)

        # --- Gerenciamento de Dados ---
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 10)
        vbox.pack_start(Gtk.Label(label="Gerenciar Rostos Conhecidos"), False, False, 0)

        # Lista de Arquivos (TreeView)
        self.face_store = Gtk.ListStore(str)
        self.populate_faces()

        self.tree_faces = Gtk.TreeView(model=self.face_store)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Arquivo", renderer, text=0)
        self.tree_faces.append_column(column)

        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(150)
        scroll.add(self.tree_faces)
        vbox.pack_start(scroll, True, True, 0)

        # Conecta o evento de seleção para mostrar a miniatura
        selection = self.tree_faces.get_selection()
        selection.connect("changed", self.on_face_selected)

        hbox_data = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        vbox.pack_start(hbox_data, False, False, 0)

        self.btn_refresh = Gtk.Button(label="🔄 Atualizar")
        self.btn_refresh.connect("clicked", self.on_refresh_list)
        hbox_data.pack_start(self.btn_refresh, True, True, 0)

        self.btn_delete = Gtk.Button(label="🗑️ Excluir")
        self.btn_delete.connect("clicked", self.on_delete_face)
        hbox_data.pack_start(self.btn_delete, True, True, 0)

        # Área de Preview da Imagem
        vbox.pack_start(Gtk.Label(label="Preview:"), False, False, 5)
        self.image_preview = Gtk.Image()
        vbox.pack_start(self.image_preview, False, False, 0)

        self.window.show_all()

    def on_mode_change(self, widget):
        self.settings["mode"] = widget.get_active_id()

    def on_rec_change(self, widget):
        self.settings["rec_interval"] = widget.get_value()

    def on_tol_change(self, widget):
        self.settings["tolerance"] = widget.get_value() / 100.0

    def on_bri_change(self, widget):
        self.settings["brightness"] = int(widget.get_value())

    def on_fil_change(self, widget):
        self.settings["filter_id"] = int(widget.get_value())

    def on_photo_click(self, widget):
        self.settings["take_photo"] = 1

    def on_record_click(self, widget):
        self.settings["record_video"] = 1

    def load_config(self):
        """Carrega configurações do arquivo JSON."""
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        if k in self.settings:
                            self.settings[k] = v
                print("Configurações carregadas.")
            except Exception as e:
                print(f"Erro ao carregar config: {e}")

    def save_config(self):
        """Salva configurações no arquivo JSON."""
        try:
            data = dict(self.settings)
            # Reseta gatilhos para não iniciar tirando foto na próxima vez
            data["take_photo"] = 0
            data["record_video"] = 0
            with open("config.json", "w") as f:
                json.dump(data, f, indent=4)
            print("Configurações salvas.")
        except Exception as e:
            print(f"Erro ao salvar config: {e}")

    def on_close(self, widget):
        self.save_config()
        Gtk.main_quit()

    def on_reset_click(self, widget):
        self.combo_mode.set_active_id("vigilancia")
        self.scale_rec.set_value(4.3)
        self.scale_tol.set_value(60)
        self.scale_bri.set_value(150)
        self.scale_fil.set_value(0)
        print("Configurações restauradas.")

    def populate_faces(self):
        """Lê a pasta data/known e preenche a lista."""
        self.face_store.clear()
        if os.path.exists(self.known_dir):
            for f in os.listdir(self.known_dir):
                if f.endswith(('.jpg', '.jpeg', '.png')):
                    self.face_store.append([f])

    def on_refresh_list(self, widget):
        self.populate_faces()

    def on_face_selected(self, selection):
        """Carrega a miniatura da imagem selecionada."""
        model, treeiter = selection.get_selected()
        if treeiter:
            filename = model[treeiter][0]
            filepath = os.path.join(self.known_dir, filename)
            try:
                # Carrega a imagem redimensionada para 150px de largura (preservando proporção)
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(filepath, 150, 150, True)
                self.image_preview.set_from_pixbuf(pixbuf)
            except Exception as e:
                print(f"Erro ao carregar preview: {e}")
                self.image_preview.clear()

    def on_delete_face(self, widget):
        selection = self.tree_faces.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            filename = model[treeiter][0]
            filepath = os.path.join(self.known_dir, filename)
            try:
                os.remove(filepath)
                model.remove(treeiter)
                self.image_preview.clear() # Limpa o preview
                print(f"Arquivo removido: {filepath}")
                self.settings["reload_faces"] = True # Avisa o main.py para recarregar
            except Exception as e:
                print(f"Erro ao excluir: {e}")

    def run(self):
        """Inicia o loop principal do GTK."""
        # Gtk estará disponível no escopo global injetado por launch_panel
        Gtk.main()

def launch_panel(shared_settings):
    """Função auxiliar para iniciar o processo."""
    # Importação movida para cá para evitar conflito (SegFault) com OpenCV no processo pai
    global Gtk, GdkPixbuf
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GdkPixbuf

    app = ControlPanel(shared_settings)
    app.run()