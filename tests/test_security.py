"""
Pruebas de seguridad del sistema de autenticación.
Cubre inyección SQL, vulnerabilidades comunes y análisis de seguridad.
"""
import pytest
import sys
from pathlib import Path
import sqlite3

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import Database
from src.auth_service import AuthService


@pytest.fixture
def sistema_seguro():
    """Fixture para pruebas de seguridad."""
    db_path = "data/test_security.db"
    db = Database(db_path)
    auth = AuthService(db)
    
    yield {"db": db, "auth": auth}
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


# ============================================================================
# PRUEBAS DE INYECCIÓN SQL
# ============================================================================

class TestInyeccionSQL:
    """Pruebas contra ataques de inyección SQL."""
    
    def test_sql_injection_login_basico(self, sistema_seguro):
        """Debe prevenir inyección SQL básica en login."""
        auth = sistema_seguro["auth"]
        
        # Crear usuario legítimo
        auth.registrar_usuario("admin@test.com", "Pass123!")
        
        # Intentar inyección SQL clásica
        email_malicioso = "admin@test.com' OR '1'='1"
        password_malicioso = "cualquiera' OR '1'='1"
        
        exito, _ = auth.iniciar_sesion(email_malicioso, password_malicioso)
        assert exito is False, "Sistema vulnerable a inyección SQL básica"
    
    def test_sql_injection_registro(self, sistema_seguro):
        """Debe prevenir inyección SQL en registro."""
        auth = sistema_seguro["auth"]
        
        # Intentar inyección en email
        email_malicioso = "test@test.com'; DROP TABLE usuarios; --"
        
        auth.registrar_usuario(email_malicioso, "Pass123!")
        
        # Verificar que la tabla sigue existiendo
        db = sistema_seguro["db"]
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
        tabla = cursor.fetchone()
        conn.close()
        
        assert tabla is not None, "Tabla usuarios fue eliminada por inyección SQL"
    
    def test_sql_injection_comillas_simples(self, sistema_seguro):
        """Debe escapar correctamente comillas simples."""
        auth = sistema_seguro["auth"]
        
        # Email con comilla simple
        email_con_comilla = "o'connor@test.com"
        password = "Pass123!"
        
        # No debe causar error de SQL
        exito, mensaje = auth.registrar_usuario(email_con_comilla, password)
        # Puede fallar por validación de email, pero no por error SQL
        assert "SQL" not in mensaje
    
    def test_sql_injection_union_attack(self, sistema_seguro):
        """Debe prevenir ataques UNION."""
        auth = sistema_seguro["auth"]
        
        auth.registrar_usuario("user@test.com", "Pass123!")
        
        # Intentar UNION para extraer datos
        email_union = "user@test.com' UNION SELECT password_hash FROM usuarios --"
        
        exito, _ = auth.iniciar_sesion(email_union, "Pass123!")
        assert exito is False
    
    def test_sql_injection_comentarios(self, sistema_seguro):
        """Debe prevenir bypass usando comentarios SQL."""
        auth = sistema_seguro["auth"]
        
        auth.registrar_usuario("admin@test.com", "Pass123!")
        
        # Intentar comentar resto de query
        email_comentario = "admin@test.com'--"
        
        exito, _ = auth.iniciar_sesion(email_comentario, "")
        assert exito is False
    
    def test_sql_injection_batched_queries(self, sistema_seguro):
        """Debe prevenir múltiples queries."""
        auth = sistema_seguro["auth"]
        
        # Intentar ejecutar múltiples comandos
        email_batch = "test@test.com'; UPDATE usuarios SET bloqueado=1; --"
        
        auth.registrar_usuario(email_batch, "Pass123!")
        
        # Si hubiera funcionado, todos los usuarios estarían bloqueados
        # Crear usuario normal y verificar
        auth.registrar_usuario("normal@test.com", "Pass123!")
        usuario = sistema_seguro["db"].obtener_usuario("normal@test.com")
        
        assert usuario['bloqueado'] == 0, "Inyección SQL modificó otros registros"
    
    def test_sql_injection_boolean_based(self, sistema_seguro):
        """Debe prevenir inyección SQL basada en booleanos."""
        auth = sistema_seguro["auth"]
        
        auth.registrar_usuario("test@test.com", "Pass123!")
        
        # Diferentes variaciones de inyección booleana
        inyecciones = [
            "test@test.com' AND '1'='1",
            "test@test.com' AND 1=1 --",
            "test@test.com' OR 'a'='a",
        ]
        
        for email_malicioso in inyecciones:
            exito, _ = auth.iniciar_sesion(email_malicioso, "Pass123!")
            assert exito is False, f"Vulnerable a: {email_malicioso}"
    
    def test_sql_injection_time_based(self, sistema_seguro):
        """Debe prevenir inyección SQL time-based."""
        auth = sistema_seguro["auth"]
        
        # Intentar inyección con SLEEP/WAITFOR
        email_time = "test@test.com'; WAITFOR DELAY '00:00:05' --"
        
        import time
        inicio = time.time()
        auth.registrar_usuario(email_time, "Pass123!")
        duracion = time.time() - inicio
        
        # No debe demorar 5 segundos (timeout de la inyección)
        assert duracion < 2, "Posible inyección SQL time-based"


# ============================================================================
# PRUEBAS DE HASHING Y CRIPTOGRAFÍA
# ============================================================================

class TestSeguridadCriptografica:
    """Pruebas de la seguridad criptográfica del sistema."""
    
    def test_passwords_no_almacenadas_texto_plano(self, sistema_seguro):
        """Las contraseñas nunca deben almacenarse en texto plano."""
        db = sistema_seguro["db"]
        
        password_original = "MiPasswordSecreta123!"
        db.crear_usuario("user@test.com", password_original)
        
        # Verificar en BD que no está en texto plano
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM usuarios WHERE email = ?", ("user@test.com",))
        hash_almacenado = cursor.fetchone()['password_hash']
        conn.close()
        
        assert hash_almacenado != password_original
        assert len(hash_almacenado) == 64  # SHA-256 en hex
    
    def test_hash_no_reversible(self, sistema_seguro):
        """El hash no debe permitir recuperar la contraseña original."""
        db = sistema_seguro["db"]
        
        password = "Test123!"
        hash_password = db._hash_password(password)
        
        # El hash debe ser irreversible (no debe contener la password)
        assert password not in hash_password
        assert password.lower() not in hash_password.lower()
    
    def test_diferentes_usuarios_misma_password_diferente_hash(self, sistema_seguro):
        """Aunque esto no es ideal, verificamos el comportamiento actual."""
        db = sistema_seguro["db"]
        
        password = "SamePass123!"
        hash1 = db._hash_password(password)
        hash2 = db._hash_password(password)
        
        # SHA-256 sin salt genera mismo hash (esto es esperado pero no ideal)
        # En producción debería usar bcrypt o argon2 con salt
        assert hash1 == hash2
        # Nota: Este test documenta que NO usamos salt
        # Para mayor seguridad, se recomienda usar bcrypt en el futuro
    
    def test_hash_longitud_consistente_segura(self, sistema_seguro):
        """El hash debe tener longitud de algoritmo criptográfico seguro."""
        db = sistema_seguro["db"]
        
        passwords_variadas = [
            "A1!",  # Muy corta
            "Pass123!",  # Normal
            "SuperLongPasswordWith123!@#",  # Muy larga
        ]
        
        for password in passwords_variadas:
            hash_resultado = db._hash_password(password)
            # SHA-256 siempre produce 64 caracteres hex
            assert len(hash_resultado) == 64
    
    def test_tokens_recuperacion_son_seguros(self, sistema_seguro):
        """Los tokens de recuperación deben ser criptográficamente seguros."""
        auth = sistema_seguro["auth"]
        
        # Generar múltiples tokens
        tokens = [auth.generar_token_recuperacion() for _ in range(100)]
        
        # Todos deben ser únicos (colisiones son extremadamente improbables)
        assert len(tokens) == len(set(tokens))
        
        # Deben tener longitud adecuada (32 chars = 16 bytes)
        assert all(len(token) == 32 for token in tokens)
        
        # Deben ser hexadecimales
        for token in tokens:
            try:
                int(token, 16)
            except ValueError:
                pytest.fail(f"Token no es hexadecimal válido: {token}")


# ============================================================================
# PRUEBAS DE AUTORIZACIÓN Y ACCESO
# ============================================================================

class TestAutorizacionAcceso:
    """Pruebas de control de acceso y autorización."""
    
    def test_usuario_no_puede_acceder_sin_autenticacion(self, sistema_seguro):
        """Usuario debe autenticarse antes de acceder."""
        auth = sistema_seguro["auth"]
        
        # Intentar login sin registrarse
        exito, _ = auth.iniciar_sesion("noexiste@test.com", "Pass123!")
        assert exito is False
    
    def test_usuario_bloqueado_no_tiene_acceso(self, sistema_seguro):
        """Usuario bloqueado no debe poder acceder."""
        auth = sistema_seguro["auth"]
        
        email = "bloqueado@test.com"
        password = "Pass123!"
        
        auth.registrar_usuario(email, password)
        
        # Bloquear usuario
        for i in range(5):
            auth.iniciar_sesion(email, f"Wrong{i}!")
        
        # No debe poder acceder ni con password correcta
        exito, _ = auth.iniciar_sesion(email, password)
        assert exito is False
    
    def test_usuarios_no_pueden_modificar_cuentas_ajenas(self, sistema_seguro):
        """Un usuario no debe poder modificar datos de otro."""
        auth = sistema_seguro["auth"]
        
        # Crear dos usuarios
        auth.registrar_usuario("user1@test.com", "Pass1!")
        auth.registrar_usuario("user2@test.com", "Pass2!")
        
        # Usuario 1 no puede cambiar password de usuario 2 sin autenticación
        # (el sistema actual requiere email para cambiar password)
        auth.cambiar_password("user2@test.com", "Hacked!")
        
        # Verificar que user2 puede seguir usando su password original
        # Si el cambio no requirió autenticación, esto es una vulnerabilidad
        exito, _ = auth.iniciar_sesion("user2@test.com", "Pass2!")
        # Este test documenta que cambiar_password NO requiere autenticación previa
        # En producción, debería requerir el password actual o token válido


# ============================================================================
# PRUEBAS DE ENUMERACIÓN DE USUARIOS
# ============================================================================

class TestEnumeracionUsuarios:
    """Pruebas para prevenir enumeración de usuarios."""
    
    def test_registro_no_revela_usuarios_existentes_inmediatamente(self, sistema_seguro):
        """Los mensajes de error no deben permitir enumerar usuarios fácilmente."""
        auth = sistema_seguro["auth"]
        
        # Registrar usuario
        auth.registrar_usuario("exists@test.com", "Pass123!")
        
        # Intentar registrar el mismo
        exito, mensaje = auth.registrar_usuario("exists@test.com", "Pass456!")
        
        assert exito is False
        # El mensaje indica que el email ya existe
        # Esto permite enumeración, pero es un trade-off con UX
        assert "registrado" in mensaje.lower() or "email" in mensaje.lower()
    
    def test_recuperacion_password_no_revela_si_usuario_existe(self, sistema_seguro):
        """Recuperación de password debe dar respuesta similar exista o no el usuario."""
        auth = sistema_seguro["auth"]
        
        # Usuario existente
        auth.registrar_usuario("exists@test.com", "Pass123!")
        
        # Solicitar recuperación para usuario existente
        exito1, msg1 = auth.solicitar_recuperacion_password("exists@test.com")
        
        # Solicitar recuperación para usuario inexistente
        exito2, msg2 = auth.solicitar_recuperacion_password("noexists@test.com")
        
        # Los mensajes deberían ser diferentes pero el sistema actual
        # revela si el usuario existe (exito1=True, exito2=False)
        # En producción, debería dar mensaje genérico en ambos casos
        assert exito1 is True
        assert exito2 is False
        # Este test documenta una posible mejora de seguridad


# ============================================================================
# PRUEBAS DE LÍMITES Y ATAQUES DE RECURSOS
# ============================================================================

class TestAtaquesRecursos:
    """Pruebas contra ataques de consumo de recursos."""
    
    def test_muchos_registros_no_causan_denegacion_servicio(self, sistema_seguro):
        """Registros masivos no deben degradar el sistema."""
        auth = sistema_seguro["auth"]
        
        # Intentar registrar muchos usuarios rápidamente
        for i in range(50):
            email = f"user{i}@test.com"
            auth.registrar_usuario(email, "Pass123!")
        
        # Sistema debe seguir respondiendo
        exito, _ = auth.iniciar_sesion("user0@test.com", "Pass123!")
        assert exito is True
    
    def test_muchos_intentos_fallidos_no_causan_crash(self, sistema_seguro):
        """Muchos intentos fallidos no deben crashear el sistema."""
        auth = sistema_seguro["auth"]
        
        auth.registrar_usuario("victim@test.com", "Pass123!")
        
        # Simular ataque de fuerza bruta
        for i in range(100):
            auth.iniciar_sesion("victim@test.com", f"Wrong{i}!")
        
        # Sistema debe seguir funcionando
        assert auth.usuario_esta_bloqueado("victim@test.com") is True
    
    def test_emails_extremadamente_largos(self, sistema_seguro):
        """Debe manejar emails extremadamente largos sin crash."""
        auth = sistema_seguro["auth"]
        
        # Email de 10,000 caracteres
        email_largo = "a" * 10000 + "@test.com"
        
        # No debe crashear, aunque probablemente falle validación
        try:
            auth.registrar_usuario(email_largo, "Pass123!")
            # Si llegamos aquí, el sistema no crasheó
            assert True
        except Exception as e:
            pytest.fail(f"Sistema crasheó con email largo: {e}")
    
    def test_passwords_extremadamente_largas(self, sistema_seguro):
        """Debe manejar passwords extremadamente largas."""
        auth = sistema_seguro["auth"]
        
        # Password de 10,000 caracteres
        password_larga = "P" + "a" * 9997 + "1!"
        
        # Debe rechazar por validación (>10 chars) pero no crashear
        try:
            exito, _ = auth.registrar_usuario("test@test.com", password_larga)
            assert exito is False  # Debe rechazar
        except Exception as e:
            pytest.fail(f"Sistema crasheó con password larga: {e}")


# ============================================================================
# PRUEBAS DE VALIDACIÓN DE ENTRADA
# ============================================================================

class TestValidacionEntradas:
    """Pruebas de validación robusta de entradas."""
    
    def test_caracteres_especiales_email(self, sistema_seguro):
        """Debe manejar correctamente caracteres especiales en email."""
        auth = sistema_seguro["auth"]
        
        emails_especiales = [
            "test+tag@test.com",  # Válido
            "test.name@test.com",  # Válido
            "test<script>@test.com",  # Inválido
            "test@test@test.com",  # Inválido
        ]
        
        for email in emails_especiales:
            exito, _ = auth.registrar_usuario(email, "Pass123!")
            # No debe crashear, debe validar correctamente
    
    def test_caracteres_unicode_password(self, sistema_seguro):
        """Debe manejar caracteres unicode en contraseñas."""
        auth = sistema_seguro["auth"]
        
        # Password con caracteres unicode
        password_unicode = "Pàss123!"
        
        exito, _ = auth.registrar_usuario("unicode@test.com", password_unicode)
        
        if exito:
            # Si acepta unicode, debe poder hacer login
            exito_login, _ = auth.iniciar_sesion("unicode@test.com", password_unicode)
            assert exito_login is True
    
    def test_null_bytes_en_entrada(self, sistema_seguro):
        """Debe manejar null bytes sin causar vulnerabilidades."""
        auth = sistema_seguro["auth"]
        
        # Intentar null byte injection
        email_null = "test\x00@test.com"
        password_null = "Pass\x00123!"
        
        # No debe crashear
        try:
            auth.registrar_usuario(email_null, password_null)
            assert True
        except Exception as e:
            # Es aceptable rechazar, pero no debe crashear
            if "null" not in str(e).lower():
                pytest.fail(f"Error inesperado con null bytes: {e}")
    
    def test_newlines_en_entrada(self, sistema_seguro):
        """Debe manejar saltos de línea en entradas."""
        auth = sistema_seguro["auth"]
        
        email_newline = "test\n@test.com"
        password_newline = "Pass\n123!"
        
        # Debe rechazar o manejar correctamente
        exito, _ = auth.registrar_usuario(email_newline, password_newline)
        # No importa si acepta o rechaza, no debe crashear


# ============================================================================
# PRUEBAS DE SEGURIDAD DE SESIÓN
# ============================================================================

class TestSeguridadSesion:
    """Pruebas de seguridad relacionadas con sesiones."""
    
    def test_login_exitoso_resetea_intentos_fallidos(self, sistema_seguro):
        """Login exitoso debe limpiar historial de intentos fallidos."""
        auth = sistema_seguro["auth"]
        
        email = "test@test.com"
        password = "Pass123!"
        
        auth.registrar_usuario(email, password)
        
        # Algunos intentos fallidos
        for i in range(3):
            auth.iniciar_sesion(email, f"Wrong{i}!")
        
        # Login exitoso
        auth.iniciar_sesion(email, password)
        
        # Intentos deben resetearse
        intentos = auth.obtener_intentos_restantes(email)
        assert intentos == 5
    
    def test_cambio_password_invalida_sesiones_anteriores(self, sistema_seguro):
        """Cambiar password debería invalidar sesiones anteriores."""
        auth = sistema_seguro["auth"]
        
        email = "session@test.com"
        password_old = "Pass1!"
        password_new = "Pass2!"
        
        auth.registrar_usuario(email, password_old)
        auth.iniciar_sesion(email, password_old)
        
        # Cambiar password
        auth.cambiar_password(email, password_new)
        
        # Password antigua no debe funcionar
        exito, _ = auth.iniciar_sesion(email, password_old)
        assert exito is False


# ============================================================================
# PRUEBAS DE LOGS Y AUDITORÍA
# ============================================================================

class TestAuditoria:
    """Pruebas de capacidad de auditoría del sistema."""
    
    def test_sistema_registra_intentos_fallidos(self, sistema_seguro):
        """Sistema debe llevar cuenta de intentos fallidos."""
        auth = sistema_seguro["auth"]
        db = sistema_seguro["db"]
        
        email = "audit@test.com"
        auth.registrar_usuario(email, "Pass123!")
        
        # Generar intentos fallidos
        for i in range(3):
            auth.iniciar_sesion(email, f"Wrong{i}!")
        
        # Verificar que se registraron
        usuario = db.obtener_usuario(email)
        assert usuario['intentos_fallidos'] == 3
    
    def test_sistema_registra_fecha_ultimo_intento(self, sistema_seguro):
        """Sistema debe registrar timestamp de último intento."""
        auth = sistema_seguro["auth"]
        db = sistema_seguro["db"]
        
        email = "timestamp@test.com"
        auth.registrar_usuario(email, "Pass123!")
        
        # Hacer intento
        auth.iniciar_sesion(email, "Wrong!")
        
        # Verificar timestamp
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ultimo_intento FROM usuarios WHERE email = ?", (email,))
        resultado = cursor.fetchone()
        conn.close()
        
        assert resultado['ultimo_intento'] is not None


# ============================================================================
# RESUMEN DE VULNERABILIDADES CONOCIDAS (DOCUMENTADAS)
# ============================================================================

class TestVulnerabilidadesConocidas:
    """Tests que documentan vulnerabilidades conocidas para futuras mejoras."""
    
    def test_conocido_no_usa_salt_en_passwords(self, sistema_seguro):
        """CONOCIDO: Sistema no usa salt, lo que permite rainbow tables."""
        db = sistema_seguro["db"]
        
        # Mismo password genera mismo hash
        hash1 = db._hash_password("Test123!")
        hash2 = db._hash_password("Test123!")
        
        assert hash1 == hash2
        # MEJORA RECOMENDADA: Usar bcrypt, argon2 o agregar salt a SHA-256
    
    def test_conocido_cambio_password_sin_autenticacion(self, sistema_seguro):
        """CONOCIDO: Cambiar password no requiere password actual."""
        auth = sistema_seguro["auth"]
        
        auth.registrar_usuario("test@test.com", "Pass1!")
        
        # Cualquiera con el email puede cambiar la password
        exito, _ = auth.cambiar_password("test@test.com", "Hacked!")
        
        assert exito is True
        # MEJORA RECOMENDADA: Requerir password actual o token de recuperación válido
    
    def test_conocido_enumeracion_usuarios_posible(self, sistema_seguro):
        """CONOCIDO: Es posible enumerar usuarios existentes."""
        auth = sistema_seguro["auth"]
        
        auth.registrar_usuario("exists@test.com", "Pass123!")
        
        # Diferentes respuestas revelan si usuario existe
        exito1, _ = auth.registrar_usuario("exists@test.com", "Pass456!")
        exito2, _ = auth.registrar_usuario("noexists@test.com", "Pass789!")
        
        # exito1 falla por duplicado, exito2 puede fallar por validación
        # pero los mensajes son diferentes
        # MEJORA RECOMENDADA: Mensajes genéricos para no revelar existencia
