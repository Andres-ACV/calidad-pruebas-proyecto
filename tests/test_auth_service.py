"""
Pruebas unitarias para el módulo de servicios de autenticación.
Cubre validaciones, lógica de negocio y casos límite.
"""
import pytest
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auth_service import AuthService
from src.database import Database


@pytest.fixture
def db_test():
    """Fixture que crea una base de datos temporal para cada test."""
    db_path = "data/test_auth_service.db"
    db = Database(db_path)
    yield db
    # Cleanup: eliminar base de datos de prueba
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def auth_service(db_test):
    """Fixture que crea un servicio de autenticación con BD de prueba."""
    return AuthService(db_test)


# ============================================================================
# PRUEBAS DE VALIDACIÓN DE EMAIL
# ============================================================================

class TestValidacionEmail:
    """Suite de pruebas para validación de emails."""
    
    def test_email_valido_basico(self, auth_service):
        """Debe aceptar un email válido básico."""
        valido, mensaje = auth_service.validar_email("usuario@ejemplo.com")
        assert valido is True
        assert "válido" in mensaje.lower()
    
    def test_email_valido_con_numeros(self, auth_service):
        """Debe aceptar emails con números."""
        valido, _ = auth_service.validar_email("usuario123@ejemplo.com")
        assert valido is True
    
    def test_email_valido_con_guiones(self, auth_service):
        """Debe aceptar emails con guiones y guiones bajos."""
        valido, _ = auth_service.validar_email("usuario-test_123@ejemplo.com")
        assert valido is True
    
    def test_email_valido_con_puntos(self, auth_service):
        """Debe aceptar emails con puntos en el nombre."""
        valido, _ = auth_service.validar_email("usuario.nombre@ejemplo.com")
        assert valido is True
    
    def test_email_valido_dominio_largo(self, auth_service):
        """Debe aceptar emails con dominios largos."""
        valido, _ = auth_service.validar_email("usuario@ejemplo.co.cr")
        assert valido is True
    
    def test_email_vacio(self, auth_service):
        """Debe rechazar email vacío."""
        valido, mensaje = auth_service.validar_email("")
        assert valido is False
        assert "vacío" in mensaje.lower()
    
    def test_email_solo_espacios(self, auth_service):
        """Debe rechazar email con solo espacios."""
        valido, mensaje = auth_service.validar_email("   ")
        assert valido is False
        assert "vacío" in mensaje.lower()
    
    def test_email_sin_arroba(self, auth_service):
        """Debe rechazar email sin @."""
        valido, mensaje = auth_service.validar_email("usuarioejemplo.com")
        assert valido is False
        assert "inválido" in mensaje.lower()
    
    def test_email_sin_dominio(self, auth_service):
        """Debe rechazar email sin dominio."""
        valido, mensaje = auth_service.validar_email("usuario@")
        assert valido is False
        assert "inválido" in mensaje.lower()
    
    def test_email_sin_nombre(self, auth_service):
        """Debe rechazar email sin nombre de usuario."""
        valido, mensaje = auth_service.validar_email("@ejemplo.com")
        assert valido is False
        assert "inválido" in mensaje.lower()
    
    def test_email_sin_extension(self, auth_service):
        """Debe rechazar email sin extensión de dominio."""
        valido, mensaje = auth_service.validar_email("usuario@ejemplo")
        assert valido is False
        assert "inválido" in mensaje.lower()
    
    def test_email_con_espacios(self, auth_service):
        """Debe rechazar email con espacios."""
        valido, mensaje = auth_service.validar_email("usuario @ejemplo.com")
        assert valido is False
        assert "inválido" in mensaje.lower()
    
    def test_email_multiple_arrobas(self, auth_service):
        """Debe rechazar email con múltiples @."""
        valido, mensaje = auth_service.validar_email("usuario@@ejemplo.com")
        assert valido is False
        assert "inválido" in mensaje.lower()
    
    def test_email_caracteres_especiales_invalidos(self, auth_service):
        """Debe rechazar email con caracteres especiales inválidos."""
        valido, mensaje = auth_service.validar_email("usuario$#@ejemplo.com")
        assert valido is False
        assert "inválido" in mensaje.lower()
    
    def test_email_none(self, auth_service):
        """Debe rechazar email None."""
        valido, mensaje = auth_service.validar_email(None)
        assert valido is False


# ============================================================================
# PRUEBAS DE VALIDACIÓN DE CONTRASEÑA
# ============================================================================

class TestValidacionPassword:
    """Suite de pruebas para validación de contraseñas."""
    
    def test_password_valida_minima(self, auth_service):
        """Debe aceptar contraseña válida de longitud mínima (5 chars)."""
        valido, mensaje = auth_service.validar_password("Ab1@x")
        assert valido is True
        assert "válida" in mensaje.lower()
    
    def test_password_valida_maxima(self, auth_service):
        """Debe aceptar contraseña válida de longitud máxima (10 chars)."""
        valido, mensaje = auth_service.validar_password("Abcd123!@#")
        assert valido is True
        assert "válida" in mensaje.lower()
    
    def test_password_valida_media(self, auth_service):
        """Debe aceptar contraseña válida de longitud media."""
        valido, mensaje = auth_service.validar_password("Pass123!")
        assert valido is True
    
    def test_password_todos_especiales_validos(self, auth_service):
        """Debe aceptar diferentes caracteres especiales."""
        especiales = "!@#$%^&*()_+-=[]{}|;:',.<>?/\\`~"
        for char in especiales[:5]:  # Probar algunos
            valido, _ = auth_service.validar_password(f"Pass1{char}")
            assert valido is True, f"Falló con carácter especial: {char}"
    
    def test_password_vacia(self, auth_service):
        """Debe rechazar contraseña vacía."""
        valido, mensaje = auth_service.validar_password("")
        assert valido is False
        assert "vacía" in mensaje.lower()
    
    def test_password_none(self, auth_service):
        """Debe rechazar contraseña None."""
        valido, mensaje = auth_service.validar_password(None)
        assert valido is False
        assert "vacía" in mensaje.lower()
    
    def test_password_muy_corta(self, auth_service):
        """Debe rechazar contraseña menor a 5 caracteres."""
        valido, mensaje = auth_service.validar_password("Ab1!")
        assert valido is False
        assert "5 caracteres" in mensaje.lower()
    
    def test_password_muy_corta_4_chars(self, auth_service):
        """Debe rechazar contraseña de 4 caracteres."""
        valido, mensaje = auth_service.validar_password("Ax1!")
        assert valido is False
        assert "5" in mensaje
    
    def test_password_muy_larga(self, auth_service):
        """Debe rechazar contraseña mayor a 10 caracteres."""
        valido, mensaje = auth_service.validar_password("Password123!")
        assert valido is False
        assert "10 caracteres" in mensaje.lower()
    
    def test_password_muy_larga_11_chars(self, auth_service):
        """Debe rechazar contraseña de 11 caracteres."""
        valido, mensaje = auth_service.validar_password("Password12!")
        assert valido is False
        assert "10" in mensaje
    
    def test_password_sin_mayuscula(self, auth_service):
        """Debe rechazar contraseña sin mayúsculas."""
        valido, mensaje = auth_service.validar_password("pass123!")
        assert valido is False
        assert "mayúscula" in mensaje.lower()
    
    def test_password_sin_especial(self, auth_service):
        """Debe rechazar contraseña sin carácter especial."""
        valido, mensaje = auth_service.validar_password("Pass1234")
        assert valido is False
        assert "especial" in mensaje.lower()
    
    def test_password_solo_letras_mayusculas(self, auth_service):
        """Debe rechazar contraseña solo con letras mayúsculas."""
        valido, mensaje = auth_service.validar_password("PASSWORD")
        assert valido is False
        # Falla por falta de especial (o longitud)
    
    def test_password_solo_numeros(self, auth_service):
        """Debe rechazar contraseña solo con números."""
        valido, mensaje = auth_service.validar_password("12345678")
        assert valido is False
    
    def test_password_espacios(self, auth_service):
        """Debe aceptar contraseñas con espacios si cumplen requisitos."""
        valido, _ = auth_service.validar_password("Pass 1!")
        # Los espacios son válidos en contraseñas
        assert valido is True
    
    def test_password_unicode(self, auth_service):
        """Debe manejar caracteres unicode en contraseñas."""
        valido, _ = auth_service.validar_password("Páss1!")
        # La validación actual acepta unicode
        assert valido is True


# ============================================================================
# PRUEBAS DE REGISTRO DE USUARIOS
# ============================================================================

class TestRegistroUsuario:
    """Suite de pruebas para el registro de usuarios."""
    
    def test_registro_exitoso(self, auth_service):
        """Debe registrar un usuario válido exitosamente."""
        exito, mensaje = auth_service.registrar_usuario(
            "nuevo@ejemplo.com", 
            "Pass123!"
        )
        assert exito is True
        assert "exitosamente" in mensaje.lower()
    
    def test_registro_email_invalido(self, auth_service):
        """Debe fallar registro con email inválido."""
        exito, mensaje = auth_service.registrar_usuario(
            "email-invalido", 
            "Pass123!"
        )
        assert exito is False
        assert "email" in mensaje.lower()
    
    def test_registro_password_invalida(self, auth_service):
        """Debe fallar registro con contraseña inválida."""
        exito, mensaje = auth_service.registrar_usuario(
            "test@ejemplo.com", 
            "corta"
        )
        assert exito is False
        assert "contraseña" in mensaje.lower() or "caracteres" in mensaje.lower()
    
    def test_registro_duplicado(self, auth_service):
        """Debe fallar registro con email duplicado."""
        email = "duplicado@ejemplo.com"
        password = "Pass123!"
        
        # Primer registro
        exito1, _ = auth_service.registrar_usuario(email, password)
        assert exito1 is True
        
        # Segundo registro con mismo email
        exito2, mensaje2 = auth_service.registrar_usuario(email, password)
        assert exito2 is False
        assert "registrado" in mensaje2.lower() or "email" in mensaje2.lower()
    
    def test_registro_multiples_usuarios(self, auth_service):
        """Debe permitir registrar múltiples usuarios diferentes."""
        usuarios = [
            ("user1@test.com", "Pass123!"),
            ("user2@test.com", "Pass456!"),
            ("user3@test.com", "Pass789!")
        ]
        
        for email, password in usuarios:
            exito, _ = auth_service.registrar_usuario(email, password)
            assert exito is True


# ============================================================================
# PRUEBAS DE INICIO DE SESIÓN
# ============================================================================

class TestInicioSesion:
    """Suite de pruebas para el inicio de sesión."""
    
    @pytest.fixture(autouse=True)
    def setup_usuario(self, auth_service):
        """Crea un usuario de prueba antes de cada test."""
        self.email_test = "login@ejemplo.com"
        self.password_test = "Pass123!"
        auth_service.registrar_usuario(self.email_test, self.password_test)
    
    def test_login_exitoso(self, auth_service):
        """Debe permitir login con credenciales correctas."""
        exito, mensaje = auth_service.iniciar_sesion(
            self.email_test, 
            self.password_test
        )
        assert exito is True
        assert "exitoso" in mensaje.lower()
    
    def test_login_password_incorrecta(self, auth_service):
        """Debe fallar login con contraseña incorrecta."""
        exito, mensaje = auth_service.iniciar_sesion(
            self.email_test, 
            "Incorrecta1!"
        )
        assert exito is False
        assert "incorrecta" in mensaje.lower()
    
    def test_login_usuario_inexistente(self, auth_service):
        """Debe fallar login con usuario inexistente."""
        exito, mensaje = auth_service.iniciar_sesion(
            "noexiste@ejemplo.com", 
            "Pass123!"
        )
        assert exito is False
        assert "no encontrado" in mensaje.lower() or "no existe" in mensaje.lower()
    
    def test_login_email_vacio(self, auth_service):
        """Debe fallar login con email vacío."""
        exito, mensaje = auth_service.iniciar_sesion("", "Pass123!")
        assert exito is False
        assert "vacío" in mensaje.lower()
    
    def test_login_password_vacia(self, auth_service):
        """Debe fallar login con contraseña vacía."""
        exito, mensaje = auth_service.iniciar_sesion(self.email_test, "")
        assert exito is False
        assert "vacía" in mensaje.lower()
    
    def test_login_ambos_vacios(self, auth_service):
        """Debe fallar login con ambos campos vacíos."""
        exito, mensaje = auth_service.iniciar_sesion("", "")
        assert exito is False


# ============================================================================
# PRUEBAS DE SISTEMA DE INTENTOS
# ============================================================================

class TestSistemaIntentos:
    """Suite de pruebas para el sistema de intentos fallidos."""
    
    @pytest.fixture(autouse=True)
    def setup_usuario(self, auth_service):
        """Crea un usuario de prueba."""
        self.email_test = "intentos@ejemplo.com"
        self.password_test = "Pass123!"
        auth_service.registrar_usuario(self.email_test, self.password_test)
    
    def test_intentos_restantes_inicial(self, auth_service):
        """Usuario nuevo debe tener 5 intentos disponibles."""
        intentos = auth_service.obtener_intentos_restantes(self.email_test)
        assert intentos == 5
    
    def test_intento_fallido_reduce_contador(self, auth_service):
        """Intento fallido debe reducir contador."""
        # Primer intento fallido
        auth_service.iniciar_sesion(self.email_test, "Incorrecta1!")
        intentos = auth_service.obtener_intentos_restantes(self.email_test)
        assert intentos == 4
    
    def test_intento_exitoso_resetea_contador(self, auth_service):
        """Intento exitoso debe resetear el contador."""
        # Varios intentos fallidos
        for _ in range(3):
            auth_service.iniciar_sesion(self.email_test, "Incorrecta1!")
        
        # Intento exitoso
        auth_service.iniciar_sesion(self.email_test, self.password_test)
        
        # Verificar que se reseteó
        intentos = auth_service.obtener_intentos_restantes(self.email_test)
        assert intentos == 5
    
    def test_bloqueo_despues_5_intentos(self, auth_service):
        """Usuario debe bloquearse después de 5 intentos fallidos."""
        # 5 intentos fallidos
        for i in range(5):
            exito, _ = auth_service.iniciar_sesion(
                self.email_test, 
                f"Incorrecta{i}!"
            )
            assert exito is False
        
        # Verificar bloqueo
        assert auth_service.usuario_esta_bloqueado(self.email_test) is True
    
    def test_login_bloqueado_rechaza_password_correcta(self, auth_service):
        """Usuario bloqueado no puede hacer login ni con password correcta."""
        # Bloquear usuario
        for i in range(5):
            auth_service.iniciar_sesion(self.email_test, f"Incorrecta{i}!")
        
        # Intentar con password correcta
        exito, mensaje = auth_service.iniciar_sesion(
            self.email_test, 
            self.password_test
        )
        assert exito is False
        assert "bloqueado" in mensaje.lower()
    
    def test_intentos_restantes_cero_cuando_bloqueado(self, auth_service):
        """Intentos restantes debe ser 0 cuando está bloqueado."""
        # Bloquear
        for i in range(5):
            auth_service.iniciar_sesion(self.email_test, f"Incorrecta{i}!")
        
        intentos = auth_service.obtener_intentos_restantes(self.email_test)
        assert intentos == 0


# ============================================================================
# PRUEBAS DE RECUPERACIÓN DE CONTRASEÑA
# ============================================================================

class TestRecuperacionPassword:
    """Suite de pruebas para recuperación de contraseña."""
    
    @pytest.fixture(autouse=True)
    def setup_usuario(self, auth_service):
        """Crea un usuario de prueba."""
        self.email_test = "recuperacion@ejemplo.com"
        self.password_test = "Pass123!"
        auth_service.registrar_usuario(self.email_test, self.password_test)
    
    def test_generar_token_recuperacion(self, auth_service):
        """Debe generar un token de recuperación."""
        token = auth_service.generar_token_recuperacion()
        assert token is not None
        assert len(token) == 32  # 16 bytes en hex = 32 caracteres
        assert isinstance(token, str)
    
    def test_tokens_son_unicos(self, auth_service):
        """Cada token generado debe ser único."""
        tokens = [auth_service.generar_token_recuperacion() for _ in range(10)]
        assert len(tokens) == len(set(tokens))  # Todos únicos
    
    def test_solicitar_recuperacion_usuario_existente(self, auth_service):
        """Debe permitir solicitar recuperación para usuario existente."""
        exito, mensaje = auth_service.solicitar_recuperacion_password(
            self.email_test
        )
        assert exito is True
        assert "token" in mensaje.lower() or "generado" in mensaje.lower()
    
    def test_solicitar_recuperacion_usuario_inexistente(self, auth_service):
        """Debe fallar recuperación para usuario inexistente."""
        exito, mensaje = auth_service.solicitar_recuperacion_password(
            "noexiste@ejemplo.com"
        )
        assert exito is False
        assert "no" in mensaje.lower() and "registrado" in mensaje.lower()
    
    def test_cambiar_password_exitoso(self, auth_service):
        """Debe permitir cambiar contraseña con validaciones."""
        nueva_password = "Nueva123!"
        exito, mensaje = auth_service.cambiar_password(
            self.email_test, 
            nueva_password
        )
        assert exito is True
        assert "actualizada" in mensaje.lower() or "exitosamente" in mensaje.lower()
        
        # Verificar que puede hacer login con la nueva
        exito_login, _ = auth_service.iniciar_sesion(
            self.email_test, 
            nueva_password
        )
        assert exito_login is True
    
    def test_cambiar_password_invalida(self, auth_service):
        """Debe rechazar cambio a contraseña inválida."""
        exito, mensaje = auth_service.cambiar_password(
            self.email_test, 
            "corta"
        )
        assert exito is False
        assert "contraseña" in mensaje.lower()
    
    def test_cambiar_password_desbloquea_usuario(self, auth_service):
        """Cambiar contraseña debe desbloquear usuario bloqueado."""
        # Bloquear usuario
        for i in range(5):
            auth_service.iniciar_sesion(self.email_test, f"Incorrecta{i}!")
        
        assert auth_service.usuario_esta_bloqueado(self.email_test) is True
        
        # Cambiar contraseña
        auth_service.cambiar_password(self.email_test, "Nueva123!")
        
        # Verificar que se desbloqueó
        assert auth_service.usuario_esta_bloqueado(self.email_test) is False


# ============================================================================
# PRUEBAS DE CASOS LÍMITE (EDGE CASES)
# ============================================================================

class TestCasosLimite:
    """Pruebas de casos límite y situaciones especiales."""
    
    def test_email_muy_largo(self, auth_service):
        """Debe manejar emails extremadamente largos."""
        email_largo = "a" * 100 + "@ejemplo.com"
        valido, _ = auth_service.validar_email(email_largo)
        # Debe validar el formato (incluso si es largo)
        assert valido is True
    
    def test_password_con_caracteres_raros(self, auth_service):
        """Debe manejar contraseñas con emojis y unicode."""
        # Con emoji (si tiene 5-10 chars, mayúscula y especial)
        valido, _ = auth_service.validar_password("Pás1!")
        assert valido is True  # ñ/á son válidos
    
    def test_multiples_usuarios_mismo_password(self, auth_service):
        """Múltiples usuarios pueden tener la misma contraseña."""
        password = "Pass123!"
        exito1, _ = auth_service.registrar_usuario("user1@test.com", password)
        exito2, _ = auth_service.registrar_usuario("user2@test.com", password)
        
        assert exito1 is True
        assert exito2 is True
    
    def test_usuario_inexistente_intentos_restantes(self, auth_service):
        """Intentos restantes para usuario inexistente debe ser 0."""
        intentos = auth_service.obtener_intentos_restantes("noexiste@test.com")
        assert intentos == 0
    
    def test_usuario_inexistente_no_esta_bloqueado(self, auth_service):
        """Usuario inexistente no debe reportarse como bloqueado."""
        bloqueado = auth_service.usuario_esta_bloqueado("noexiste@test.com")
        assert bloqueado is False


# ============================================================================
# PRUEBAS DE INTEGRACIÓN ENTRE MÉTODOS
# ============================================================================

class TestIntegracionMetodos:
    """Pruebas que verifican la interacción entre múltiples métodos."""
    
    def test_flujo_completo_usuario(self, auth_service):
        """Flujo completo: registro → login → recuperación → cambio."""
        email = "flujo@test.com"
        
        # 1. Registro
        exito, _ = auth_service.registrar_usuario(email, "Pass123!")
        assert exito is True
        
        # 2. Login exitoso
        exito, _ = auth_service.iniciar_sesion(email, "Pass123!")
        assert exito is True
        
        # 3. Solicitar recuperación
        exito, _ = auth_service.solicitar_recuperacion_password(email)
        assert exito is True
        
        # 4. Cambiar contraseña
        exito, _ = auth_service.cambiar_password(email, "Nueva456!")
        assert exito is True
        
        # 5. Login con nueva contraseña
        exito, _ = auth_service.iniciar_sesion(email, "Nueva456!")
        assert exito is True
