"""
Interfaz gráfica de autenticación usando tkinter.
Pantalla moderna con colores y validaciones visuales.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from src.database import Database
from src.auth_service import AuthService


class LoginUI:
    """Interfaz gráfica para el sistema de autenticación."""
    
    def __init__(self):
        """Inicializa la ventana principal y los componentes."""
        self.ventana = tk.Tk()
        self.ventana.title("Sistema de Autenticación")
        self.ventana.geometry("450x600")
        self.ventana.resizable(False, False)
        
        # Colores modernos
        self.color_fondo = "#1e1e2e"
        self.color_primario = "#89b4fa"
        self.color_secundario = "#cba6f7"
        self.color_texto = "#cdd6f4"
        self.color_error = "#f38ba8"
        self.color_exito = "#a6e3a1"
        self.color_campo = "#313244"
        
        self.ventana.configure(bg=self.color_fondo)
        
        # Inicializar servicios
        self.db = Database()
        self.auth_service = AuthService(self.db)
        
        # Variables
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.modo_registro = False
        
        # Construir interfaz
        self._crear_interfaz()
    
    def _crear_interfaz(self):
        """Crea todos los elementos de la interfaz."""
        # Frame principal
        frame_principal = tk.Frame(self.ventana, bg=self.color_fondo)
        frame_principal.pack(expand=True, fill='both', padx=30, pady=30)
        
        # Título
        self.label_titulo = tk.Label(
            frame_principal,
            text="🔐 INICIAR SESIÓN",
            font=("Segoe UI", 24, "bold"),
            bg=self.color_fondo,
            fg=self.color_primario
        )
        self.label_titulo.pack(pady=(0, 30))
        
        # Subtítulo informativo
        self.label_info = tk.Label(
            frame_principal,
            text="Ingresa tus credenciales",
            font=("Segoe UI", 10),
            bg=self.color_fondo,
            fg=self.color_texto
        )
        self.label_info.pack(pady=(0, 20))
        
        # Campo Email
        label_email = tk.Label(
            frame_principal,
            text="📧 Email",
            font=("Segoe UI", 11, "bold"),
            bg=self.color_fondo,
            fg=self.color_texto,
            anchor='w'
        )
        label_email.pack(fill='x', pady=(10, 5))
        
        self.entry_email = tk.Entry(
            frame_principal,
            textvariable=self.email_var,
            font=("Segoe UI", 12),
            bg=self.color_campo,
            fg=self.color_texto,
            insertbackground=self.color_texto,
            relief='flat',
            bd=5
        )
        self.entry_email.pack(fill='x', ipady=8)
        
        # Mensaje de validación email
        self.label_email_error = tk.Label(
            frame_principal,
            text="",
            font=("Segoe UI", 9),
            bg=self.color_fondo,
            fg=self.color_error,
            anchor='w'
        )
        self.label_email_error.pack(fill='x')
        
        # Campo Contraseña
        label_password = tk.Label(
            frame_principal,
            text="🔑 Contraseña",
            font=("Segoe UI", 11, "bold"),
            bg=self.color_fondo,
            fg=self.color_texto,
            anchor='w'
        )
        label_password.pack(fill='x', pady=(15, 5))
        
        self.entry_password = tk.Entry(
            frame_principal,
            textvariable=self.password_var,
            font=("Segoe UI", 12),
            bg=self.color_campo,
            fg=self.color_texto,
            insertbackground=self.color_texto,
            show="●",
            relief='flat',
            bd=5
        )
        self.entry_password.pack(fill='x', ipady=8)
        
        # Mensaje de validación password
        self.label_password_error = tk.Label(
            frame_principal,
            text="",
            font=("Segoe UI", 9),
            bg=self.color_fondo,
            fg=self.color_error,
            anchor='w'
        )
        self.label_password_error.pack(fill='x')
        
        # Requisitos de contraseña (solo visible en modo registro)
        self.label_requisitos = tk.Label(
            frame_principal,
            text="Requisitos: 5-10 caracteres, 1 mayúscula, 1 carácter especial",
            font=("Segoe UI", 8),
            bg=self.color_fondo,
            fg=self.color_secundario,
            anchor='w'
        )
        
        # Botón principal (Login/Registro)
        self.btn_principal = tk.Button(
            frame_principal,
            text="INICIAR SESIÓN",
            font=("Segoe UI", 12, "bold"),
            bg=self.color_primario,
            fg=self.color_fondo,
            activebackground=self.color_secundario,
            activeforeground=self.color_fondo,
            relief='flat',
            cursor='hand2',
            command=self._accion_principal
        )
        self.btn_principal.pack(fill='x', pady=(25, 10), ipady=10)
        
        # Línea separadora
        tk.Frame(frame_principal, height=1, bg=self.color_campo).pack(fill='x', pady=15)
        
        # Botón recuperar contraseña
        btn_recuperar = tk.Button(
            frame_principal,
            text="¿Olvidaste tu contraseña?",
            font=("Segoe UI", 9),
            bg=self.color_fondo,
            fg=self.color_secundario,
            activebackground=self.color_fondo,
            activeforeground=self.color_primario,
            relief='flat',
            cursor='hand2',
            bd=0,
            command=self._recuperar_password
        )
        btn_recuperar.pack(pady=5)
        
        # Botón cambiar modo
        self.btn_cambiar_modo = tk.Button(
            frame_principal,
            text="¿No tienes cuenta? Regístrate",
            font=("Segoe UI", 9, "bold"),
            bg=self.color_fondo,
            fg=self.color_primario,
            activebackground=self.color_fondo,
            activeforeground=self.color_secundario,
            relief='flat',
            cursor='hand2',
            bd=0,
            command=self._cambiar_modo
        )
        self.btn_cambiar_modo.pack(pady=5)
        
        # Label de estado (intentos restantes, etc.)
        self.label_estado = tk.Label(
            frame_principal,
            text="",
            font=("Segoe UI", 9),
            bg=self.color_fondo,
            fg=self.color_texto
        )
        self.label_estado.pack(pady=(15, 0))
        
        # Bind Enter key
        self.ventana.bind('<Return>', lambda e: self._accion_principal())
    
    def _validar_email_tiempo_real(self, event=None):
        """Valida el email mientras el usuario escribe."""
        email = self.email_var.get()
        if len(email) == 0:
            self.label_email_error.config(text="")
            return
        
        valido, mensaje = self.auth_service.validar_email(email)
        if not valido:
            self.label_email_error.config(text=f"❌ {mensaje}")
        else:
            self.label_email_error.config(text="✓ Email válido", fg=self.color_exito)
    
    def _validar_password_tiempo_real(self, event=None):
        """Valida la contraseña mientras el usuario escribe."""
        password = self.password_var.get()
        if len(password) == 0 or not self.modo_registro:
            self.label_password_error.config(text="")
            return
        
        valido, mensaje = self.auth_service.validar_password(password)
        if not valido:
            self.label_password_error.config(text=f"❌ {mensaje}")
        else:
            self.label_password_error.config(text="✓ Contraseña válida", fg=self.color_exito)
    
    def _accion_principal(self):
        """Ejecuta login o registro según el modo actual."""
        if self.modo_registro:
            self._registrar()
        else:
            self._login()
    
    def _login(self):
        """Intenta iniciar sesión."""
        email = self.email_var.get().strip()
        password = self.password_var.get()
        
        # Limpiar mensajes
        self.label_email_error.config(text="")
        self.label_password_error.config(text="")
        
        # Validar campos vacíos
        if not email:
            self.label_email_error.config(text="❌ El email es requerido")
            return
        
        if not password:
            self.label_password_error.config(text="❌ La contraseña es requerida")
            return
        
        # Intentar login
        exito, mensaje = self.auth_service.iniciar_sesion(email, password)
        
        if exito:
            messagebox.showinfo(
                "✓ Login Exitoso",
                f"¡Bienvenido!\n\nHas iniciado sesión correctamente como:\n{email}"
            )
            self._limpiar_campos()
        else:
            messagebox.showerror("✗ Error de Autenticación", mensaje)
            
            # Mostrar intentos restantes si el usuario existe
            if not self.auth_service.usuario_esta_bloqueado(email):
                intentos = self.auth_service.obtener_intentos_restantes(email)
                if intentos > 0:
                    self.label_estado.config(
                        text=f"⚠ Intentos restantes: {intentos}",
                        fg=self.color_error
                    )
            else:
                self.label_estado.config(
                    text="🔒 Usuario bloqueado",
                    fg=self.color_error
                )
    
    def _registrar(self):
        """Registra un nuevo usuario."""
        email = self.email_var.get().strip()
        password = self.password_var.get()
        
        # Limpiar mensajes
        self.label_email_error.config(text="")
        self.label_password_error.config(text="")
        
        # Intentar registro
        exito, mensaje = self.auth_service.registrar_usuario(email, password)
        
        if exito:
            messagebox.showinfo(
                "✓ Registro Exitoso",
                f"Usuario creado correctamente.\n\nYa puedes iniciar sesión con:\n{email}"
            )
            self._limpiar_campos()
            self._cambiar_modo()  # Volver a modo login
        else:
            if "email" in mensaje.lower():
                self.label_email_error.config(text=f"❌ {mensaje}")
            else:
                self.label_password_error.config(text=f"❌ {mensaje}")
    
    def _recuperar_password(self):
        """Muestra diálogo para recuperar contraseña."""
        email = self.email_var.get().strip()
        
        if not email:
            messagebox.showwarning(
                "Email Requerido",
                "Por favor ingresa tu email primero."
            )
            return
        
        # Validar que el usuario existe
        usuario = self.db.obtener_usuario(email)
        if not usuario:
            messagebox.showerror(
                "Error",
                "El email no está registrado en el sistema."
            )
            return
        
        # Solicitar recuperación (sin credenciales SMTP se obtiene el token)
        exito, mensaje = self.auth_service.solicitar_recuperacion_password(email)
        
        if exito:
            # Extraer token del mensaje
            if "Token de recuperación generado:" in mensaje:
                token = mensaje.split(": ")[1]
                
                # Pedir nueva contraseña
                ventana_recovery = tk.Toplevel(self.ventana)
                ventana_recovery.title("Recuperar Contraseña")
                ventana_recovery.geometry("400x250")
                ventana_recovery.configure(bg=self.color_fondo)
                ventana_recovery.resizable(False, False)
                
                tk.Label(
                    ventana_recovery,
                    text=f"Tu token: {token}",
                    font=("Segoe UI", 10, "bold"),
                    bg=self.color_fondo,
                    fg=self.color_exito
                ).pack(pady=15)
                
                tk.Label(
                    ventana_recovery,
                    text="Nueva Contraseña:",
                    font=("Segoe UI", 10),
                    bg=self.color_fondo,
                    fg=self.color_texto
                ).pack(pady=5)
                
                nueva_pass_var = tk.StringVar()
                entry_nueva = tk.Entry(
                    ventana_recovery,
                    textvariable=nueva_pass_var,
                    font=("Segoe UI", 11),
                    bg=self.color_campo,
                    fg=self.color_texto,
                    show="●",
                    relief='flat'
                )
                entry_nueva.pack(pady=5, padx=20, fill='x', ipady=5)
                
                tk.Label(
                    ventana_recovery,
                    text="Requisitos: 5-10 caracteres, 1 mayúscula, 1 especial",
                    font=("Segoe UI", 8),
                    bg=self.color_fondo,
                    fg=self.color_secundario
                ).pack(pady=5)
                
                def cambiar():
                    nueva_pass = nueva_pass_var.get()
                    exito_cambio, msg_cambio = self.auth_service.cambiar_password(email, nueva_pass)
                    
                    if exito_cambio:
                        messagebox.showinfo("✓ Éxito", "Contraseña actualizada correctamente")
                        ventana_recovery.destroy()
                    else:
                        messagebox.showerror("✗ Error", msg_cambio)
                
                tk.Button(
                    ventana_recovery,
                    text="CAMBIAR CONTRASEÑA",
                    font=("Segoe UI", 10, "bold"),
                    bg=self.color_primario,
                    fg=self.color_fondo,
                    relief='flat',
                    cursor='hand2',
                    command=cambiar
                ).pack(pady=15, padx=20, fill='x', ipady=8)
    
    def _cambiar_modo(self):
        """Alterna entre modo login y registro."""
        self.modo_registro = not self.modo_registro
        
        # Limpiar campos y mensajes
        self._limpiar_campos()
        
        if self.modo_registro:
            self.label_titulo.config(text="📝 REGISTRO")
            self.label_info.config(text="Crea tu cuenta")
            self.btn_principal.config(text="REGISTRARSE")
            self.btn_cambiar_modo.config(text="¿Ya tienes cuenta? Inicia sesión")
            self.label_requisitos.pack(fill='x', pady=(5, 0))
            
            # Activar validación en tiempo real
            self.email_var.trace_add('write', lambda *args: self._validar_email_tiempo_real())
            self.password_var.trace_add('write', lambda *args: self._validar_password_tiempo_real())
        else:
            self.label_titulo.config(text="🔐 INICIAR SESIÓN")
            self.label_info.config(text="Ingresa tus credenciales")
            self.btn_principal.config(text="INICIAR SESIÓN")
            self.btn_cambiar_modo.config(text="¿No tienes cuenta? Regístrate")
            self.label_requisitos.pack_forget()
            
            # Desactivar validación en tiempo real (opcional en login)
            self.label_email_error.config(text="")
            self.label_password_error.config(text="", fg=self.color_error)
    
    def _limpiar_campos(self):
        """Limpia todos los campos y mensajes de error."""
        self.email_var.set("")
        self.password_var.set("")
        self.label_email_error.config(text="")
        self.label_password_error.config(text="", fg=self.color_error)
        self.label_estado.config(text="")
    
    def ejecutar(self):
        """Inicia el loop principal de la interfaz."""
        self.ventana.mainloop()


# Función helper para ejecutar la aplicación
def iniciar_aplicacion():
    """Inicia la aplicación de autenticación."""
    app = LoginUI()
    app.ejecutar()


if __name__ == "__main__":
    iniciar_aplicacion()
