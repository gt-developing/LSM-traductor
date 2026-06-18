"""Interfaz grafica del traductor LSM."""

# =========================================================
# APP PRINCIPAL
# =========================================================

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import os
import random
from glob import glob

if __package__ in (None, ""):
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from traductor_lsm.interfaz_utilidades import (
        obtener_datos_tecnicos,
        tokenizar_glosa_para_animacion,
    )
    from traductor_lsm.traductor import (
        traducir_a_glosa_lsm_natural,
        traducir_a_glosa_lsm_tecnica,
    )
else:
    from .interfaz_utilidades import (
        obtener_datos_tecnicos,
        tokenizar_glosa_para_animacion,
    )
    from .traductor import (
        traducir_a_glosa_lsm_natural,
        traducir_a_glosa_lsm_tecnica,
    )


class TraductorLSMApp:
    """Interfaz grafica del traductor LSM.

    Administra la entrada del usuario, la salida en glosa visible, el panel
    tecnico y la lista de tokens que simula la secuencia de animacion.
    """

    def __init__(self, root):
        """Inicializa estado de la ventana y construye la interfaz."""

        self.root = root
        self.root.title("Traductor Español → Glosa LSM")
        self.root.geometry("1100x650")
        self.root.minsize(900, 550)
        self.root.configure(fg_color="white")

        self.tecnico_visible = False
        self.avatar_frames = self.cargar_frames_avatar()
        self.ultimo_avatar = None
        self.crear_interfaz()

    def cargar_frames_avatar(self):
        """Carga imagenes PNG del avatar desde la carpeta ``similar``."""

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        patron = os.path.join(base_dir, "similar", "simibailando (*.png")
        rutas = sorted(glob(patron))

        frames = []
        for ruta in rutas:
            try:
                frames.append(tk.PhotoImage(file=ruta))
            except tk.TclError:
                continue

        return frames

    def actualizar_frame_avatar(self):
        """Muestra un frame aleatorio del avatar evitando repetir el anterior."""

        if not self.avatar_frames or not hasattr(self, "avatar_frame_label"):
            return

        if len(self.avatar_frames) == 1:
            indice = 0
        else:
            opciones = list(range(len(self.avatar_frames)))
            if self.ultimo_avatar in opciones:
                opciones.remove(self.ultimo_avatar)
            indice = random.choice(opciones)

        self.ultimo_avatar = indice
        imagen = self.avatar_frames[indice]
        self.avatar_frame_label.configure(image=imagen, text="")
        self.avatar_frame_label.image = imagen

    def crear_interfaz(self):
        """Crea la estructura general de la ventana."""

        # Contenedor general (Main grid)
        # Usamos un CTkFrame transparente para que actúe como el 'main' original
        main = ctk.CTkFrame(self.root, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=34, pady=34)

        # --- HEADER (Título y Subtítulo) ---
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))

        titulo = ctk.CTkLabel(
            header, 
            text="Traductor Español → LSM", 
            font=("Segoe UI", 24, "bold")
        )
        titulo.pack(anchor="w")

        subtitulo = ctk.CTkLabel(
            header, 
            text="Prototipo de texto a glosa LSM con vista previa de animación palabra por palabra.", 
            font=("Segoe UI", 13),
            text_color="#5E5E5E"
        )
        subtitulo.pack(anchor="w")

        # --- DIVISIÓN IZQUIERDA / DERECHA ---
        # Nota: CustomTkinter maneja mejor la distribución con frames normales/grids que con PanedWindow
        cuerpo = ctk.CTkFrame(main, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True)
        
        # Panel izquierdo ocupará el 65% del ancho, el derecho el 35%
        self.panel_izquierdo = ctk.CTkFrame(cuerpo, fg_color="white")
        self.panel_izquierdo.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.panel_derecho = ctk.CTkFrame(cuerpo, fg_color="transparent")
        self.panel_derecho.configure(width=320)
        self.panel_derecho.pack(side="right", fill="both", expand=False, padx=(10, 0))

        self.crear_panel_izquierdo()
        self.crear_panel_derecho()

    def crear_panel_con_sombra(self, parent, corner_radius=12, fg_color="#FFFFFF"):
        """Crea un contenedor reutilizable con borde y radio de esquina."""

        contenedor = ctk.CTkFrame(parent, fg_color="transparent")

        panel = ctk.CTkFrame(
            contenedor,
            fg_color=fg_color,
            corner_radius=corner_radius,
            border_width=1,
            border_color="#D0D0D0"
        )
        panel.pack(fill="both", expand=True)

        return contenedor, panel

    def crear_panel_izquierdo(self):
        """Construye los controles de entrada, botones, glosa y detalles."""

        # --- ENTRADA (Panel con sombra y bordes redondeados automática) ---
        # 'corner_radius' se encarga de redondearlo y darle un aspecto moderno
        entrada_container, entrada_frame = self.crear_panel_con_sombra(self.panel_izquierdo)
        entrada_container.pack(fill="both", expand=True, pady=(0, 10))

        titulo_panel_entrada = ctk.CTkLabel(
            entrada_frame, 
            text="Texto en español", 
            font=("Segoe UI", 14, "bold")
        )
        titulo_panel_entrada.pack(anchor="w", padx=15, pady=(12, 4))

        # Cuadro de texto nativo de CustomTkinter
        self.texto_entrada = ctk.CTkTextbox(
            entrada_frame, 
            font=("Segoe UI", 13),
            activate_scrollbars=True,
            border_color="#53BAFF", border_width=1
        )
        self.texto_entrada.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.texto_entrada.insert("1.0", "El gato negro duerme en la cama.")

        # --- BOTONES ---
        botones_frame = ctk.CTkFrame(self.panel_izquierdo, fg_color="transparent")
        botones_frame.pack(fill="x", pady=10)

        # Botón Traducir (Estilo principal, color llamativo opcional)
        self.btn_traducir = ctk.CTkButton(
            botones_frame, 
            text="Traducir a LSM", 
            font=("Segoe UI", 12, "bold"),
            height=40,
            command=self.traducir
        )
        self.btn_traducir.pack(side="left", padx=(0, 8))

        # Botón Mostrar Técnico
        self.btn_ojo = ctk.CTkButton(
            botones_frame, 
            text="👁 Mostrar técnico", 
            fg_color="#FFFFFF", hover_color="#CECECE",
            text_color="#000000",
            border_color="#D0D0D0",
            border_width=1,
            height=40, 
            command=self.toggle_tecnico
        )
        self.btn_ojo.pack(side="left", padx=(0, 8))

        # Botón Limpiar
        self.btn_limpiar = ctk.CTkButton(
            botones_frame, 
            text="Limpiar",
            height=40,
            text_color="#000000",
            border_color="#D0D0D0",
            border_width=1, 
            fg_color="#FFFFFF", hover_color="#CACACA", # Tonos rojos
            command=self.limpiar
        )
        self.btn_limpiar.pack(side="left")

        # --- SALIDA GLOSA (Panel con sombra automático) ---
        glosa_container, glosa_frame = self.crear_panel_con_sombra(self.panel_izquierdo)
        glosa_container.pack(fill="both", expand=True, pady=10)

        titulo_glosa = ctk.CTkLabel(
            glosa_frame, 
            text="Glosa LSM", 
            font=("Segoe UI", 14, "bold")
        )
        titulo_glosa.pack(anchor="w", padx=15, pady=(12, 4))

        self.texto_glosa = ctk.CTkTextbox(
            glosa_frame, 
            font=("Consolas", 15, "bold"),
            activate_scrollbars=True
        )
        self.texto_glosa.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # --- TÉCNICO OCULTO ---
        self.tecnico_frame, tecnico_frame = self.crear_panel_con_sombra(self.panel_izquierdo)
        # No hace pack al inicio porque está oculto

        titulo_tecnico = ctk.CTkLabel(
            tecnico_frame, 
            text="Detalles técnicos", 
            font=("Segoe UI", 14, "bold")
        )
        titulo_tecnico.pack(anchor="w", padx=15, pady=(12, 4))

        self.texto_tecnico = ctk.CTkTextbox(
            tecnico_frame, 
            font=("Consolas", 12),
            activate_scrollbars=True
        )
        self.texto_tecnico.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def crear_panel_derecho(self):
        """Construye la vista de avatar, lista de tokens y controles."""

        # --- PANEL DE ANIMACIÓN ---
        anim_container, anim_frame = self.crear_panel_con_sombra(self.panel_derecho)
        anim_container.pack(fill="both", expand=True)

        titulo_anim = ctk.CTkLabel(
            anim_frame, 
            text="Vista de animación", 
            font=("Segoe UI", 14, "bold")
        )
        titulo_anim.pack(anchor="w", padx=15, pady=(12, 4))

        descripcion = ctk.CTkLabel(
            anim_frame, 
            text="Secuencia que ejecutaría el avatar :b", 
            font=("Segoe UI", 12),
            wraplength=260
        )
        descripcion.pack(anchor="w", padx=15, pady=(0, 10))

        avatar_container = ctk.CTkFrame(anim_frame, fg_color="#F7F7F7", border_width=1, border_color="#D3D3D3")
        avatar_container.pack(fill="x", padx=15, pady=(0, 10))

        avatar_titulo = ctk.CTkLabel(
            avatar_container,
            text="Avatar",
            font=("Segoe UI", 12, "bold"),
            text_color="#4B4B4B"
        )
        avatar_titulo.pack(anchor="w", padx=10, pady=(8, 4))

        self.avatar_frame_label = ctk.CTkLabel(avatar_container, text="")
        self.avatar_frame_label.pack(padx=10, pady=(0, 10))

        # Contenedor de la lista (un sutil borde alrededor)
        rectangulo = ctk.CTkFrame(anim_frame, fg_color="transparent", border_width=2, border_color="#D3D3D3")
        rectangulo.pack(fill="both", expand=True, padx=15, pady=10)

        # Mantenemos el tk.Listbox clásico porque CustomTkinter no tiene Listbox nativo,
        # pero lo estilizamos para que encaje perfectamente.
        self.animacion_lista = tk.Listbox(
            rectangulo,
            font=("Segoe UI", 16, "bold"),
            justify="center",
            activestyle="none",
            bd=0,
            highlightthickness=0,
            bg="#f9f9f9" if ctk.get_appearance_mode() == "Light" else "#2b2b2b",
            fg="black" if ctk.get_appearance_mode() == "Light" else "white"
        )
        self.animacion_lista.pack(fill="both", expand=True, padx=5, pady=5)

        # Controles de reproducción
        controles = ctk.CTkFrame(anim_frame, fg_color="transparent")
        controles.pack(fill="x", padx=15, pady=(0, 15))

        self.btn_anterior = ctk.CTkButton(controles, text="◀", width=40, command=self.animacion_anterior)
        self.btn_anterior.pack(side="left", padx=(0, 6))

        self.btn_reproducir = ctk.CTkButton(controles, text="Reproducir demo", command=self.reproducir_demo)
        self.btn_reproducir.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.btn_siguiente = ctk.CTkButton(controles, text="▶", width=40, command=self.animacion_siguiente)
        self.btn_siguiente.pack(side="left")

        self.indice_animacion = 0
        self.actualizar_frame_avatar()

    # =====================================================
    # LÓGICA Y ACCIONES (Se mantienen igual de eficientes)
    # =====================================================

    def traducir(self):
        """Traduce el texto escrito y actualiza glosa, detalles y animacion."""

        texto = self.texto_entrada.get("1.0", "end").strip()

        if not texto:
            messagebox.showwarning("Texto vacío", "Escribe una oración para traducir.")
            return

        try:
            glosa_tecnica = traducir_a_glosa_lsm_tecnica(texto)
            glosa_visible = traducir_a_glosa_lsm_natural(texto)
        except NameError:
            messagebox.showerror(
                "Error",
                "No encontré las funciones de traducción.\nAsegúrate de que estén declaradas arriba en el script."
            )
            return
        except Exception as e:
            messagebox.showerror("Error al traducir", str(e))
            return

        self.texto_glosa.delete("1.0", "end")
        self.texto_glosa.insert("1.0", glosa_visible)

        self.actualizar_animacion(glosa_visible)

        tecnico = obtener_datos_tecnicos(texto, glosa_tecnica)
        self.texto_tecnico.delete("1.0", "end")
        self.texto_tecnico.insert("1.0", tecnico)

    def actualizar_animacion(self, glosa):
        """Refresca la lista visual con los tokens de la glosa visible."""

        self.animacion_lista.delete(0, "end")
        tokens = tokenizar_glosa_para_animacion(glosa)

        for token in tokens:
            self.animacion_lista.insert("end", token)

        self.indice_animacion = 0
        if tokens:
            self.animacion_lista.selection_set(0)
            self.animacion_lista.activate(0)
            self.animacion_lista.see(0)
            self.actualizar_frame_avatar()

    def toggle_tecnico(self):
        """Muestra u oculta el panel con datos tecnicos."""

        if self.tecnico_visible:
            self.tecnico_frame.pack_forget()
            self.btn_ojo.configure(text="Mostrar técnico")
            self.tecnico_visible = False
        else:
            self.tecnico_frame.pack(fill="both", expand=True, pady=(10, 0))
            self.btn_ojo.configure(text="Ocultar técnico")
            self.tecnico_visible = True

    def limpiar(self):
        """Limpia entrada, salidas y estado de animacion."""

        self.texto_entrada.delete("1.0", "end")
        self.texto_glosa.delete("1.0", "end")
        self.texto_tecnico.delete("1.0", "end")
        self.animacion_lista.delete(0, "end")
        self.indice_animacion = 0

    def animacion_anterior(self):
        """Selecciona el token anterior en la secuencia de animacion."""

        total = self.animacion_lista.size()
        if total == 0: return
        self.indice_animacion = max(0, self.indice_animacion - 1)
        self.seleccionar_animacion_actual()

    def animacion_siguiente(self):
        """Selecciona el siguiente token en la secuencia de animacion."""

        total = self.animacion_lista.size()
        if total == 0: return
        self.indice_animacion = min(total - 1, self.indice_animacion + 1)
        self.seleccionar_animacion_actual()

    def seleccionar_animacion_actual(self):
        """Sincroniza la seleccion visual con ``indice_animacion``."""

        self.animacion_lista.selection_clear(0, "end")
        self.animacion_lista.selection_set(self.indice_animacion)
        self.animacion_lista.activate(self.indice_animacion)
        self.animacion_lista.see(self.indice_animacion)
        self.actualizar_frame_avatar()

    def reproducir_demo(self):
        """Inicia la reproduccion automatica de la secuencia actual."""

        total = self.animacion_lista.size()
        if total == 0: return
        self.indice_animacion = 0
        self.reproducir_paso()

    def reproducir_paso(self):
        """Avanza un paso de la reproduccion automatica."""

        total = self.animacion_lista.size()
        if self.indice_animacion >= total: return

        self.seleccionar_animacion_actual()
        self.indice_animacion += 1
        self.root.after(700, self.reproducir_paso)




def ejecutar_app():
    """Inicia la aplicacion de escritorio."""

    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    TraductorLSMApp(root)
    root.mainloop()


if __name__ == "__main__":
    ejecutar_app()
