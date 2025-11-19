"""
Pruebas unitarias para el módulo de base de datos.
Cubre operaciones CRUD, hashing, integridad y persistencia.
"""
import pytest
import sys
from pathlib import Path
import sqlite3

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import Database


@pytest.fixture
def db_test():
    """Fixture que crea una base de datos temporal para cada test."""
    db_path = "data/test_database.db"
    db = Database(db_path)
    yield db
    # Cleanup: eliminar base de datos de prueba
    Path(db_path).unlink(missing_ok=True)


# ============================================================================
# PRUEBAS DE CREACIÓN Y ESTRUCTURA
# ============================================================================

class TestEstructuraBaseDatos:
    """Pruebas de la estructura y creación de la base de datos."""
    
    def test_crear_base_datos(self, db_test):
        """Debe crear el archivo de base de datos."""
        assert Path(db_test.db_path).exists()
    
    def test_tabla_usuarios_existe(self, db_test):
        """Debe crear la tabla usuarios."""
        conn = db_test._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='usuarios'
        """)
        resultado = cursor.fetchone()
        conn.close()
        
        assert resultado is not None
        assert resultado[0] == 'usuarios'
    
    def test_tabla_recovery_tokens_existe(self, db_test):
        """Debe crear la tabla recovery_tokens."""
        conn = db_test._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='recovery_tokens'
        """)
        resultado = cursor.fetchone()
        conn.close()
        
        assert resultado is not None
        assert resultado[0] == 'recovery_tokens'
    
    def test_columnas_tabla_usuarios(self, db_test):
        """Debe tener todas las columnas necesarias en usuarios."""
        conn = db_test._get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(usuarios)")
        columnas = {row[1] for row in cursor.fetchall()}
        conn.close()
        
        columnas_requeridas = {
            'id', 'email', 'password_hash', 'fecha_creacion',
            'intentos_fallidos', 'bloqueado', 'ultimo_intento'
        }
        assert columnas_requeridas.issubset(columnas)


# ============================================================================
# PRUEBAS DE HASHING DE CONTRASEÑAS
# ============================================================================

class TestHashingPasswords:
    """Pruebas del sistema de hashing de contraseñas."""
    
    def test_hash_no_retorna_password_plana(self, db_test):
        """El hash no debe ser igual a la contraseña original."""
        password = "MiPassword123!"
        hash_resultado = db_test._hash_password(password)
        
        assert hash_resultado != password
    
    def test_hash_es_determinista(self, db_test):
        """Mismo password debe generar mismo hash."""
        password = "MiPassword123!"
        hash1 = db_test._hash_password(password)
        hash2 = db_test._hash_password(password)
        
        assert hash1 == hash2
    
    def test_hash_diferente_para_passwords_diferentes(self, db_test):
        """Passwords diferentes deben generar hashes diferentes."""
        hash1 = db_test._hash_password("Password1!")
        hash2 = db_test._hash_password("Password2!")
        
        assert hash1 != hash2
    
    def test_hash_longitud_consistente(self, db_test):
        """Todos los hashes deben tener la misma longitud (SHA-256)."""
        passwords = ["short", "medium_password", "very_long_password_here"]
        hashes = [db_test._hash_password(p) for p in passwords]
        
        # SHA-256 en hex = 64 caracteres
        assert all(len(h) == 64 for h in hashes)
    
    def test_hash_solo_caracteres_hexadecimales(self, db_test):
        """El hash debe contener solo caracteres hexadecimales."""
        hash_resultado = db_test._hash_password("Test123!")
        
        # Verificar que es hexadecimal válido
        try:
            int(hash_resultado, 16)
            es_hex = True
        except ValueError:
            es_hex = False
        
        assert es_hex is True


# ============================================================================
# PRUEBAS DE CREACIÓN DE USUARIOS (CREATE)
# ============================================================================

class TestCrearUsuario:
    """Pruebas de la operación de creación de usuarios."""
    
    def test_crear_usuario_exitoso(self, db_test):
        """Debe crear un usuario correctamente."""
        exito, mensaje = db_test.crear_usuario(
            "nuevo@ejemplo.com", 
            "Password123!"
        )
        
        assert exito is True
        assert "exitosamente" in mensaje.lower()
    
    def test_crear_usuario_almacena_email(self, db_test):
        """El email debe almacenarse correctamente."""
        email = "test@ejemplo.com"
        db_test.crear_usuario(email, "Pass123!")
        
        usuario = db_test.obtener_usuario(email)
        assert usuario is not None
        assert usuario['email'] == email
    
    def test_crear_usuario_no_almacena_password_plana(self, db_test):
        """La contraseña no debe almacenarse en texto plano."""
        email = "seguro@ejemplo.com"
        password = "MiPassword123!"
        
        db_test.crear_usuario(email, password)
        
        # Verificar directamente en la BD
        conn = db_test._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash FROM usuarios WHERE email = ?", 
            (email,)
        )
        resultado = cursor.fetchone()
        conn.close()
        
        assert resultado is not None
        assert resultado['password_hash'] != password
    
    def test_crear_usuario_duplicado_falla(self, db_test):
        """No debe permitir crear usuario con email duplicado."""
        email = "duplicado@ejemplo.com"
        
        # Primera creación
        exito1, _ = db_test.crear_usuario(email, "Pass123!")
        assert exito1 is True
        
        # Segunda creación (debe fallar)
        exito2, mensaje2 = db_test.crear_usuario(email, "Pass456!")
        assert exito2 is False
        assert "registrado" in mensaje2.lower() or "email" in mensaje2.lower()
    
    def test_crear_usuario_inicializa_intentos_en_cero(self, db_test):
        """Usuario nuevo debe tener intentos_fallidos en 0."""
        email = "nuevo@ejemplo.com"
        db_test.crear_usuario(email, "Pass123!")
        
        usuario = db_test.obtener_usuario(email)
        assert usuario['intentos_fallidos'] == 0
    
    def test_crear_usuario_no_bloqueado_inicial(self, db_test):
        """Usuario nuevo no debe estar bloqueado."""
        email = "nuevo@ejemplo.com"
        db_test.crear_usuario(email, "Pass123!")
        
        usuario = db_test.obtener_usuario(email)
        assert usuario['bloqueado'] == 0
    
    def test_crear_usuario_con_fecha_creacion(self, db_test):
        """Debe almacenar fecha de creación."""
        email = "fecha@ejemplo.com"
        db_test.crear_usuario(email, "Pass123!")
        
        usuario = db_test.obtener_usuario(email)
        assert usuario['fecha_creacion'] is not None
        assert len(usuario['fecha_creacion']) > 0


# ============================================================================
# PRUEBAS DE LECTURA DE USUARIOS (READ)
# ============================================================================

class TestObtenerUsuario:
    """Pruebas de la operación de lectura de usuarios."""
    
    def test_obtener_usuario_existente(self, db_test):
        """Debe retornar datos de usuario existente."""
        email = "existe@ejemplo.com"
        db_test.crear_usuario(email, "Pass123!")
        
        usuario = db_test.obtener_usuario(email)
        
        assert usuario is not None
        assert usuario['email'] == email
    
    def test_obtener_usuario_inexistente(self, db_test):
        """Debe retornar None para usuario inexistente."""
        usuario = db_test.obtener_usuario("noexiste@ejemplo.com")
        assert usuario is None
    
    def test_obtener_usuario_retorna_diccionario(self, db_test):
        """Debe retornar un diccionario con los datos."""
        email = "dict@ejemplo.com"
        db_test.crear_usuario(email, "Pass123!")
        
        usuario = db_test.obtener_usuario(email)
        
        assert isinstance(usuario, dict)
        assert 'id' in usuario
        assert 'email' in usuario
        assert 'fecha_creacion' in usuario
    
    def test_obtener_usuario_no_incluye_password_hash(self, db_test):
        """El método obtener_usuario no debe exponer el hash."""
        email = "seguro@ejemplo.com"
        db_test.crear_usuario(email, "Pass123!")
        
        usuario = db_test.obtener_usuario(email)
        
        # No debe incluir password_hash en el resultado
        assert 'password_hash' not in usuario


# ============================================================================
# PRUEBAS DE VERIFICACIÓN DE CREDENCIALES
# ============================================================================

class TestVerificarCredenciales:
    """Pruebas de la verificación de credenciales de login."""
    
    @pytest.fixture(autouse=True)
    def setup_usuario(self, db_test):
        """Crea un usuario de prueba antes de cada test."""
        self.email = "login@ejemplo.com"
        self.password = "Password123!"
        db_test.crear_usuario(self.email, self.password)
    
    def test_verificar_credenciales_correctas(self, db_test):
        """Debe aceptar credenciales correctas."""
        exito, mensaje = db_test.verificar_credenciales(
            self.email, 
            self.password
        )
        
        assert exito is True
        assert "exitoso" in mensaje.lower()
    
    def test_verificar_credenciales_password_incorrecta(self, db_test):
        """Debe rechazar password incorrecta."""
        exito, mensaje = db_test.verificar_credenciales(
            self.email, 
            "PasswordIncorrecta!"
        )
        
        assert exito is False
        assert "incorrecta" in mensaje.lower()
    
    def test_verificar_credenciales_usuario_inexistente(self, db_test):
        """Debe rechazar usuario inexistente."""
        exito, mensaje = db_test.verificar_credenciales(
            "noexiste@ejemplo.com", 
            "Pass123!"
        )
        
        assert exito is False
        assert "no encontrado" in mensaje.lower()
    
    def test_verificar_incrementa_intentos_fallidos(self, db_test):
        """Credenciales incorrectas deben incrementar intentos."""
        # Intento fallido
        db_test.verificar_credenciales(self.email, "Incorrecta!")
        
        usuario = db_test.obtener_usuario(self.email)
        assert usuario['intentos_fallidos'] == 1
    
    def test_verificar_resetea_intentos_en_exito(self, db_test):
        """Login exitoso debe resetear intentos fallidos."""
        # Varios intentos fallidos
        for _ in range(3):
            db_test.verificar_credenciales(self.email, "Incorrecta!")
        
        # Login exitoso
        db_test.verificar_credenciales(self.email, self.password)
        
        usuario = db_test.obtener_usuario(self.email)
        assert usuario['intentos_fallidos'] == 0
    
    def test_verificar_bloquea_despues_5_intentos(self, db_test):
        """Debe bloquear usuario después de 5 intentos fallidos."""
        # 5 intentos fallidos
        for i in range(5):
            db_test.verificar_credenciales(self.email, f"Incorrecta{i}!")
        
        usuario = db_test.obtener_usuario(self.email)
        assert usuario['bloqueado'] == 1
    
    def test_verificar_rechaza_usuario_bloqueado(self, db_test):
        """Usuario bloqueado no puede hacer login."""
        # Bloquear usuario
        for i in range(5):
            db_test.verificar_credenciales(self.email, f"Incorrecta{i}!")
        
        # Intentar con password correcta
        exito, mensaje = db_test.verificar_credenciales(
            self.email, 
            self.password
        )
        
        assert exito is False
        assert "bloqueado" in mensaje.lower()
    
    def test_verificar_actualiza_ultimo_intento(self, db_test):
        """Debe actualizar la fecha de último intento."""
        db_test.verificar_credenciales(self.email, "Incorrecta!")
        
        usuario = db_test.obtener_usuario(self.email)
        # Verificar en la BD directamente
        conn = db_test._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ultimo_intento FROM usuarios WHERE email = ?",
            (self.email,)
        )
        resultado = cursor.fetchone()
        conn.close()
        
        assert resultado['ultimo_intento'] is not None


# ============================================================================
# PRUEBAS DE ACTUALIZACIÓN (UPDATE)
# ============================================================================

class TestCambiarPassword:
    """Pruebas de cambio de contraseña."""
    
    @pytest.fixture(autouse=True)
    def setup_usuario(self, db_test):
        """Crea un usuario de prueba."""
        self.email = "cambio@ejemplo.com"
        self.password_original = "Original123!"
        db_test.crear_usuario(self.email, self.password_original)
    
    def test_cambiar_password_exitoso(self, db_test):
        """Debe cambiar la contraseña correctamente."""
        nueva_password = "Nueva456!"
        exito, mensaje = db_test.cambiar_password(self.email, nueva_password)
        
        assert exito is True
        assert "actualizada" in mensaje.lower()
    
    def test_cambiar_password_permite_login_con_nueva(self, db_test):
        """Después del cambio, debe permitir login con nueva password."""
        nueva_password = "Nueva456!"
        db_test.cambiar_password(self.email, nueva_password)
        
        # Intentar login con nueva
        exito, _ = db_test.verificar_credenciales(self.email, nueva_password)
        assert exito is True
    
    def test_cambiar_password_rechaza_antigua(self, db_test):
        """Después del cambio, debe rechazar la antigua password."""
        nueva_password = "Nueva456!"
        db_test.cambiar_password(self.email, nueva_password)
        
        # Intentar login con antigua
        exito, _ = db_test.verificar_credenciales(
            self.email, 
            self.password_original
        )
        assert exito is False
    
    def test_cambiar_password_resetea_intentos(self, db_test):
        """Cambiar password debe resetear intentos fallidos."""
        # Generar intentos fallidos
        for i in range(3):
            db_test.verificar_credenciales(self.email, f"Incorrecta{i}!")
        
        # Cambiar password
        db_test.cambiar_password(self.email, "Nueva456!")
        
        usuario = db_test.obtener_usuario(self.email)
        assert usuario['intentos_fallidos'] == 0
    
    def test_cambiar_password_desbloquea_usuario(self, db_test):
        """Cambiar password debe desbloquear usuario bloqueado."""
        # Bloquear usuario
        for i in range(5):
            db_test.verificar_credenciales(self.email, f"Incorrecta{i}!")
        
        # Cambiar password
        db_test.cambiar_password(self.email, "Nueva456!")
        
        usuario = db_test.obtener_usuario(self.email)
        assert usuario['bloqueado'] == 0
    
    def test_cambiar_password_usuario_inexistente(self, db_test):
        """Debe fallar al cambiar password de usuario inexistente."""
        exito, mensaje = db_test.cambiar_password(
            "noexiste@ejemplo.com", 
            "Nueva456!"
        )
        
        assert exito is False
        assert "no encontrado" in mensaje.lower()


class TestDesbloquearUsuario:
    """Pruebas de desbloqueo de usuarios."""
    
    @pytest.fixture(autouse=True)
    def setup_usuario_bloqueado(self, db_test):
        """Crea y bloquea un usuario de prueba."""
        self.email = "bloqueado@ejemplo.com"
        db_test.crear_usuario(self.email, "Pass123!")
        
        # Bloquear usuario
        for i in range(5):
            db_test.verificar_credenciales(self.email, f"Incorrecta{i}!")
    
    def test_desbloquear_usuario_exitoso(self, db_test):
        """Debe desbloquear usuario correctamente."""
        exito, mensaje = db_test.desbloquear_usuario(self.email)
        
        assert exito is True
        assert "desbloqueado" in mensaje.lower()
    
    def test_desbloquear_resetea_flag_bloqueado(self, db_test):
        """Debe poner bloqueado en 0."""
        db_test.desbloquear_usuario(self.email)
        
        usuario = db_test.obtener_usuario(self.email)
        assert usuario['bloqueado'] == 0
    
    def test_desbloquear_resetea_intentos(self, db_test):
        """Debe resetear intentos fallidos."""
        db_test.desbloquear_usuario(self.email)
        
        usuario = db_test.obtener_usuario(self.email)
        assert usuario['intentos_fallidos'] == 0
    
    def test_desbloquear_permite_login(self, db_test):
        """Usuario desbloqueado debe poder hacer login."""
        db_test.desbloquear_usuario(self.email)
        
        # Intentar login (con password correcta)
        exito, _ = db_test.verificar_credenciales(self.email, "Pass123!")
        assert exito is True
    
    def test_desbloquear_usuario_inexistente(self, db_test):
        """Debe fallar al desbloquear usuario inexistente."""
        exito, mensaje = db_test.desbloquear_usuario("noexiste@ejemplo.com")
        
        assert exito is False
        assert "no encontrado" in mensaje.lower()


# ============================================================================
# PRUEBAS DE TOKENS DE RECUPERACIÓN
# ============================================================================

class TestRecoveryTokens:
    """Pruebas de la gestión de tokens de recuperación."""
    
    @pytest.fixture(autouse=True)
    def setup_usuario(self, db_test):
        """Crea un usuario de prueba."""
        self.email = "recovery@ejemplo.com"
        db_test.crear_usuario(self.email, "Pass123!")
    
    def test_crear_token_recuperacion(self, db_test):
        """Debe crear un token de recuperación."""
        token = "abc123def456"
        exito, mensaje = db_test.crear_token_recuperacion(self.email, token)
        
        assert exito is True
        assert "exitosamente" in mensaje.lower()
    
    def test_token_se_almacena_en_bd(self, db_test):
        """El token debe almacenarse en la base de datos."""
        token = "abc123def456"
        db_test.crear_token_recuperacion(self.email, token)
        
        # Verificar en BD
        conn = db_test._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT token FROM recovery_tokens 
            WHERE email = ? AND token = ?
        """, (self.email, token))
        resultado = cursor.fetchone()
        conn.close()
        
        assert resultado is not None
        assert resultado['token'] == token
    
    def test_multiples_tokens_mismo_usuario(self, db_test):
        """Debe permitir múltiples tokens para mismo usuario."""
        token1 = "token1"
        token2 = "token2"
        
        exito1, _ = db_test.crear_token_recuperacion(self.email, token1)
        exito2, _ = db_test.crear_token_recuperacion(self.email, token2)
        
        assert exito1 is True
        assert exito2 is True


# ============================================================================
# PRUEBAS DE PERSISTENCIA Y CONCURRENCIA
# ============================================================================

class TestPersistencia:
    """Pruebas de persistencia de datos."""
    
    def test_datos_persisten_entre_conexiones(self):
        """Datos deben persistir al cerrar y reabrir conexión."""
        db_path = "data/test_persistencia.db"
        
        # Primera conexión: crear usuario
        db1 = Database(db_path)
        db1.crear_usuario("persist@ejemplo.com", "Pass123!")
        del db1  # Cerrar conexión
        
        # Segunda conexión: verificar que existe
        db2 = Database(db_path)
        usuario = db2.obtener_usuario("persist@ejemplo.com")
        
        assert usuario is not None
        assert usuario['email'] == "persist@ejemplo.com"
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    def test_multiples_operaciones_consecutivas(self, db_test):
        """Debe manejar múltiples operaciones seguidas."""
        emails = [f"user{i}@test.com" for i in range(10)]
        
        # Crear 10 usuarios
        for email in emails:
            exito, _ = db_test.crear_usuario(email, "Pass123!")
            assert exito is True
        
        # Verificar que todos existen
        for email in emails:
            usuario = db_test.obtener_usuario(email)
            assert usuario is not None


# ============================================================================
# PRUEBAS DE MANEJO DE ERRORES
# ============================================================================

class TestManejoErrores:
    """Pruebas de manejo de errores y casos excepcionales."""
    
    def test_crear_usuario_sin_crash_en_error(self, db_test):
        """Errores de BD no deben causar crash."""
        # Email duplicado debe retornar False, no lanzar excepción
        email = "error@test.com"
        db_test.crear_usuario(email, "Pass123!")
        
        exito, mensaje = db_test.crear_usuario(email, "Pass123!")
        assert exito is False
        assert isinstance(mensaje, str)
    
    def test_obtener_usuario_sin_crash_en_error(self, db_test):
        """Errores al obtener usuario no deben causar crash."""
        # Usuario inexistente debe retornar None, no lanzar excepción
        usuario = db_test.obtener_usuario("noexiste@test.com")
        assert usuario is None
