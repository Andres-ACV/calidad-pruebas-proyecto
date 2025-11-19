"""
Módulo de servicios de autenticación.
Contiene toda la lógica de negocio para autenticación y validaciones.
NO depende de la interfaz gráfica - diseñado para ser testeable.
"""
import re
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple, Optional
from src.database import Database


class AuthService:
    """Servicio de autenticación con validaciones y lógica de negocio."""
    
    def __init__(self, db: Database):
        """
        Inicializa el servicio de autenticación.
        
        Args:
            db: Instancia de la clase Database
        """
        self.db = db
        self.max_intentos = 5
    
    @staticmethod
    def validar_email(email: str) -> Tuple[bool, str]:
        """
        Valida el formato de un email.
        
        Args:
            email: String con el email a validar
            
        Returns:
            Tupla (es_válido: bool, mensaje: str)
        """
        if not email or len(email.strip()) == 0:
            return False, "El email no puede estar vacío"
        
        # Patrón regex para validar email
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(patron, email):
            return False, "Formato de email inválido"
        
        return True, "Email válido"
    
    @staticmethod
    def validar_password(password: str) -> Tuple[bool, str]:
        """
        Valida que la contraseña cumpla con los requisitos:
        - Mínimo 5 caracteres
        - Máximo 10 caracteres
        - Al menos una mayúscula
        - Al menos un carácter especial
        
        Args:
            password: String con la contraseña a validar
            
        Returns:
            Tupla (es_válida: bool, mensaje: str)
        """
        if not password:
            return False, "La contraseña no puede estar vacía"
        
        if len(password) < 5:
            return False, "La contraseña debe tener al menos 5 caracteres"
        
        if len(password) > 10:
            return False, "La contraseña no puede tener más de 10 caracteres"
        
        if not any(c.isupper() for c in password):
            return False, "La contraseña debe contener al menos una mayúscula"
        
        # Caracteres especiales comunes
        caracteres_especiales = r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]'
        if not re.search(caracteres_especiales, password):
            return False, "La contraseña debe contener al menos un carácter especial"
        
        return True, "Contraseña válida"
    
    def registrar_usuario(self, email: str, password: str) -> Tuple[bool, str]:
        """
        Registra un nuevo usuario después de validar los datos.
        
        Args:
            email: Email del usuario
            password: Contraseña del usuario
            
        Returns:
            Tupla (éxito: bool, mensaje: str)
        """
        # Validar email
        email_valido, mensaje_email = self.validar_email(email)
        if not email_valido:
            return False, mensaje_email
        
        # Validar password
        password_valida, mensaje_password = self.validar_password(password)
        if not password_valida:
            return False, mensaje_password
        
        # Crear usuario en la base de datos
        return self.db.crear_usuario(email, password)
    
    def iniciar_sesion(self, email: str, password: str) -> Tuple[bool, str]:
        """
        Intenta iniciar sesión con las credenciales proporcionadas.
        
        Args:
            email: Email del usuario
            password: Contraseña del usuario
            
        Returns:
            Tupla (éxito: bool, mensaje: str)
        """
        # Validar que los campos no estén vacíos
        if not email or len(email.strip()) == 0:
            return False, "El email no puede estar vacío"
        
        if not password or len(password.strip()) == 0:
            return False, "La contraseña no puede estar vacía"
        
        # Verificar credenciales en la base de datos
        return self.db.verificar_credenciales(email, password)
    
    def generar_token_recuperacion(self) -> str:
        """
        Genera un token seguro para recuperación de contraseña.
        
        Returns:
            Token de 32 caracteres hexadecimales
        """
        return secrets.token_hex(16)
    
    def solicitar_recuperacion_password(self, email: str, 
                                       smtp_server: str = None,
                                       smtp_port: int = 587,
                                       smtp_user: str = None,
                                       smtp_password: str = None) -> Tuple[bool, str]:
        """
        Solicita la recuperación de contraseña enviando un token por email.
        
        Args:
            email: Email del usuario
            smtp_server: Servidor SMTP (ej: smtp.gmail.com)
            smtp_port: Puerto SMTP
            smtp_user: Usuario SMTP
            smtp_password: Contraseña SMTP
            
        Returns:
            Tupla (éxito: bool, mensaje: str)
        """
        # Validar que el usuario existe
        usuario = self.db.obtener_usuario(email)
        if not usuario:
            return False, "El email no está registrado"
        
        # Generar token
        token = self.generar_token_recuperacion()
        
        # Guardar token en la base de datos
        exito, mensaje = self.db.crear_token_recuperacion(email, token)
        if not exito:
            return False, mensaje
        
        # Enviar email (solo si se proporcionan credenciales SMTP)
        if smtp_server and smtp_user and smtp_password:
            try:
                exito_email = self._enviar_email_recuperacion(
                    email, token, smtp_server, smtp_port, smtp_user, smtp_password
                )
                if exito_email:
                    return True, f"Email de recuperación enviado a {email}"
                else:
                    return True, f"Token generado (email no enviado): {token}"
            except Exception as e:
                # Aunque el email falle, el token se guardó
                return True, f"Token generado pero email falló: {token}"
        else:
            # Modo de desarrollo - retornar el token directamente
            return True, f"Token de recuperación generado: {token}"
    
    def _enviar_email_recuperacion(self, destinatario: str, token: str,
                                   smtp_server: str, smtp_port: int,
                                   smtp_user: str, smtp_password: str) -> bool:
        """
        Envía un email con el token de recuperación.
        
        Args:
            destinatario: Email del usuario
            token: Token de recuperación
            smtp_server: Servidor SMTP
            smtp_port: Puerto SMTP
            smtp_user: Usuario SMTP
            smtp_password: Contraseña SMTP
            
        Returns:
            True si el email se envió correctamente
        """
        try:
            mensaje = MIMEMultipart()
            mensaje['From'] = smtp_user
            mensaje['To'] = destinatario
            mensaje['Subject'] = 'Recuperación de Contraseña'
            
            cuerpo = f"""
            Hola,
            
            Has solicitado recuperar tu contraseña.
            
            Tu token de recuperación es: {token}
            
            Usa este token para restablecer tu contraseña.
            
            Si no solicitaste esto, ignora este mensaje.
            
            Saludos,
            Sistema de Autenticación
            """
            
            mensaje.attach(MIMEText(cuerpo, 'plain'))
            
            # Conectar y enviar
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(mensaje)
            
            return True
            
        except Exception as e:
            print(f"Error al enviar email: {e}")
            return False
    
    def cambiar_password(self, email: str, nueva_password: str) -> Tuple[bool, str]:
        """
        Cambia la contraseña de un usuario.
        
        Args:
            email: Email del usuario
            nueva_password: Nueva contraseña
            
        Returns:
            Tupla (éxito: bool, mensaje: str)
        """
        # Validar la nueva contraseña
        password_valida, mensaje = self.validar_password(nueva_password)
        if not password_valida:
            return False, mensaje
        
        # Cambiar en la base de datos
        return self.db.cambiar_password(email, nueva_password)
    
    def obtener_intentos_restantes(self, email: str) -> int:
        """
        Obtiene el número de intentos restantes para un usuario.
        
        Args:
            email: Email del usuario
            
        Returns:
            Número de intentos restantes (0 si está bloqueado o no existe)
        """
        usuario = self.db.obtener_usuario(email)
        if not usuario:
            return 0
        
        if usuario['bloqueado'] == 1:
            return 0
        
        intentos_usados = usuario['intentos_fallidos']
        return max(0, self.max_intentos - intentos_usados)
    
    def usuario_esta_bloqueado(self, email: str) -> bool:
        """
        Verifica si un usuario está bloqueado.
        
        Args:
            email: Email del usuario
            
        Returns:
            True si el usuario está bloqueado
        """
        usuario = self.db.obtener_usuario(email)
        if not usuario:
            return False
        
        return usuario['bloqueado'] == 1
