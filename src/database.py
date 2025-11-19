"""
Módulo de gestión de base de datos SQLite.
Maneja la conexión, creación de tablas y operaciones CRUD para usuarios.
"""
import sqlite3
import hashlib
import os
from datetime import datetime
from typing import Optional, Tuple


class Database:
    """Clase para manejar todas las operaciones de base de datos."""
    
    def __init__(self, db_path: str = "data/auth_system.db"):
        """
        Inicializa la conexión a la base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Crea y retorna una conexión a la base de datos."""
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
        return conn
    
    def _create_tables(self):
        """Crea las tablas necesarias si no existen."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                fecha_creacion TEXT NOT NULL,
                intentos_fallidos INTEGER DEFAULT 0,
                bloqueado INTEGER DEFAULT 0,
                ultimo_intento TEXT
            )
        """)
        
        # Tabla para tokens de recuperación
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recovery_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                token TEXT NOT NULL,
                fecha_creacion TEXT NOT NULL,
                usado INTEGER DEFAULT 0,
                FOREIGN KEY (email) REFERENCES usuarios(email)
            )
        """)
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Genera un hash SHA-256 de la contraseña.
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash hexadecimal de la contraseña
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def crear_usuario(self, email: str, password: str) -> Tuple[bool, str]:
        """
        Crea un nuevo usuario en la base de datos.
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
            
        Returns:
            Tupla (éxito: bool, mensaje: str)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            password_hash = self._hash_password(password)
            fecha_actual = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO usuarios (email, password_hash, fecha_creacion)
                VALUES (?, ?, ?)
            """, (email, password_hash, fecha_actual))
            
            conn.commit()
            conn.close()
            return True, "Usuario creado exitosamente"
            
        except sqlite3.IntegrityError:
            return False, "El email ya está registrado"
        except Exception as e:
            return False, f"Error al crear usuario: {str(e)}"
    
    def verificar_credenciales(self, email: str, password: str) -> Tuple[bool, str]:
        """
        Verifica si las credenciales son correctas.
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
            
        Returns:
            Tupla (éxito: bool, mensaje: str)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT password_hash, intentos_fallidos, bloqueado
                FROM usuarios
                WHERE email = ?
            """, (email,))
            
            resultado = cursor.fetchone()
            
            if not resultado:
                conn.close()
                return False, "Usuario no encontrado"
            
            if resultado['bloqueado'] == 1:
                conn.close()
                return False, "Usuario bloqueado por múltiples intentos fallidos"
            
            password_hash = self._hash_password(password)
            
            if password_hash == resultado['password_hash']:
                # Login exitoso - resetear intentos fallidos
                cursor.execute("""
                    UPDATE usuarios
                    SET intentos_fallidos = 0, ultimo_intento = ?
                    WHERE email = ?
                """, (datetime.now().isoformat(), email))
                conn.commit()
                conn.close()
                return True, "Login exitoso"
            else:
                # Incrementar intentos fallidos
                nuevos_intentos = resultado['intentos_fallidos'] + 1
                bloqueado = 1 if nuevos_intentos >= 5 else 0
                
                cursor.execute("""
                    UPDATE usuarios
                    SET intentos_fallidos = ?, bloqueado = ?, ultimo_intento = ?
                    WHERE email = ?
                """, (nuevos_intentos, bloqueado, datetime.now().isoformat(), email))
                
                conn.commit()
                conn.close()
                
                intentos_restantes = 5 - nuevos_intentos
                if bloqueado:
                    return False, "Usuario bloqueado por múltiples intentos fallidos"
                else:
                    return False, f"Contraseña incorrecta. Intentos restantes: {intentos_restantes}"
                    
        except Exception as e:
            return False, f"Error al verificar credenciales: {str(e)}"
    
    def obtener_usuario(self, email: str) -> Optional[dict]:
        """
        Obtiene la información de un usuario.
        
        Args:
            email: Email del usuario
            
        Returns:
            Diccionario con datos del usuario o None si no existe
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, email, fecha_creacion, intentos_fallidos, bloqueado
                FROM usuarios
                WHERE email = ?
            """, (email,))
            
            resultado = cursor.fetchone()
            conn.close()
            
            if resultado:
                return dict(resultado)
            return None
            
        except Exception as e:
            print(f"Error al obtener usuario: {e}")
            return None
    
    def crear_token_recuperacion(self, email: str, token: str) -> Tuple[bool, str]:
        """
        Crea un token de recuperación de contraseña.
        
        Args:
            email: Email del usuario
            token: Token generado
            
        Returns:
            Tupla (éxito: bool, mensaje: str)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO recovery_tokens (email, token, fecha_creacion)
                VALUES (?, ?, ?)
            """, (email, token, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True, "Token creado exitosamente"
            
        except Exception as e:
            return False, f"Error al crear token: {str(e)}"
    
    def cambiar_password(self, email: str, nueva_password: str) -> Tuple[bool, str]:
        """
        Cambia la contraseña de un usuario.
        
        Args:
            email: Email del usuario
            nueva_password: Nueva contraseña en texto plano
            
        Returns:
            Tupla (éxito: bool, mensaje: str)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            password_hash = self._hash_password(nueva_password)
            
            cursor.execute("""
                UPDATE usuarios
                SET password_hash = ?, intentos_fallidos = 0, bloqueado = 0
                WHERE email = ?
            """, (password_hash, email))
            
            if cursor.rowcount == 0:
                conn.close()
                return False, "Usuario no encontrado"
            
            conn.commit()
            conn.close()
            return True, "Contraseña actualizada exitosamente"
            
        except Exception as e:
            return False, f"Error al cambiar contraseña: {str(e)}"
    
    def desbloquear_usuario(self, email: str) -> Tuple[bool, str]:
        """
        Desbloquea un usuario y resetea sus intentos fallidos.
        
        Args:
            email: Email del usuario
            
        Returns:
            Tupla (éxito: bool, mensaje: str)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE usuarios
                SET intentos_fallidos = 0, bloqueado = 0
                WHERE email = ?
            """, (email,))
            
            if cursor.rowcount == 0:
                conn.close()
                return False, "Usuario no encontrado"
            
            conn.commit()
            conn.close()
            return True, "Usuario desbloqueado exitosamente"
            
        except Exception as e:
            return False, f"Error al desbloquear usuario: {str(e)}"
