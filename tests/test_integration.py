"""
Pruebas de integración del sistema de autenticación.
Verifica flujos completos de usuario y la interacción entre componentes.
"""
import pytest
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import Database
from src.auth_service import AuthService


@pytest.fixture
def sistema_completo():
    """Fixture que crea un sistema completo (BD + Servicio)."""
    db_path = "data/test_integration.db"
    db = Database(db_path)
    auth_service = AuthService(db)
    
    yield {"db": db, "auth": auth_service}
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


# ============================================================================
# FLUJOS COMPLETOS DE USUARIO
# ============================================================================

class TestFlujoRegistroLogin:
    """Pruebas del flujo completo: Registro → Login."""
    
    def test_flujo_basico_registro_login(self, sistema_completo):
        """Flujo: Usuario se registra y luego inicia sesión."""
        auth = sistema_completo["auth"]
        
        email = "nuevo@test.com"
        password = "Pass123!"
        
        # 1. Registro
        exito_registro, msg_registro = auth.registrar_usuario(email, password)
        assert exito_registro is True, f"Registro falló: {msg_registro}"
        
        # 2. Login inmediato
        exito_login, msg_login = auth.iniciar_sesion(email, password)
        assert exito_login is True, f"Login falló: {msg_login}"
    
    def test_registro_login_logout_login(self, sistema_completo):
        """Flujo: Registro → Login → Logout → Login."""
        auth = sistema_completo["auth"]
        
        email = "usuario@test.com"
        password = "Pass123!"
        
        # Registro
        auth.registrar_usuario(email, password)
        
        # Primer login
        exito1, _ = auth.iniciar_sesion(email, password)
        assert exito1 is True
        
        # Segundo login (simula logout y volver a entrar)
        exito2, _ = auth.iniciar_sesion(email, password)
        assert exito2 is True
    
    def test_multiples_usuarios_independientes(self, sistema_completo):
        """Múltiples usuarios deben operar independientemente."""
        auth = sistema_completo["auth"]
        
        usuarios = [
            ("user1@test.com", "Pass123!"),
            ("user2@test.com", "Pass456!"),
            ("user3@test.com", "Pass789!")
        ]
        
        # Registrar todos
        for email, password in usuarios:
            exito, _ = auth.registrar_usuario(email, password)
            assert exito is True
        
        # Verificar que cada uno puede hacer login con su propia password
        for email, password in usuarios:
            exito, _ = auth.iniciar_sesion(email, password)
            assert exito is True
        
        # Verificar que no pueden hacer login con password de otro
        exito_cruzado, _ = auth.iniciar_sesion(usuarios[0][0], usuarios[1][1])
        assert exito_cruzado is False


class TestFlujoIntentosFallidos:
    """Pruebas del flujo: Intentos fallidos → Bloqueo."""
    
    def test_flujo_intentos_hasta_bloqueo(self, sistema_completo):
        """Flujo completo de 5 intentos fallidos hasta bloqueo."""
        auth = sistema_completo["auth"]
        
        email = "bloqueo@test.com"
        password_correcta = "Pass123!"
        
        # Registro
        auth.registrar_usuario(email, password_correcta)
        
        # Verificar intentos iniciales
        assert auth.obtener_intentos_restantes(email) == 5
        assert auth.usuario_esta_bloqueado(email) is False
        
        # Intento 1
        auth.iniciar_sesion(email, "Wrong1!")
        assert auth.obtener_intentos_restantes(email) == 4
        assert auth.usuario_esta_bloqueado(email) is False
        
        # Intento 2
        auth.iniciar_sesion(email, "Wrong2!")
        assert auth.obtener_intentos_restantes(email) == 3
        
        # Intento 3
        auth.iniciar_sesion(email, "Wrong3!")
        assert auth.obtener_intentos_restantes(email) == 2
        
        # Intento 4
        auth.iniciar_sesion(email, "Wrong4!")
        assert auth.obtener_intentos_restantes(email) == 1
        
        # Intento 5 (último antes de bloqueo)
        exito5, msg5 = auth.iniciar_sesion(email, "Wrong5!")
        assert exito5 is False
        assert auth.obtener_intentos_restantes(email) == 0
        assert auth.usuario_esta_bloqueado(email) is True
        
        # Intento 6 (ya bloqueado, incluso con password correcta)
        exito6, msg6 = auth.iniciar_sesion(email, password_correcta)
        assert exito6 is False
        assert "bloqueado" in msg6.lower()
    
    def test_flujo_intentos_fallidos_con_exito_intermedio(self, sistema_completo):
        """Login exitoso entre intentos fallidos resetea contador."""
        auth = sistema_completo["auth"]
        
        email = "intermedio@test.com"
        password = "Pass123!"
        
        auth.registrar_usuario(email, password)
        
        # 2 intentos fallidos
        auth.iniciar_sesion(email, "Wrong1!")
        auth.iniciar_sesion(email, "Wrong2!")
        assert auth.obtener_intentos_restantes(email) == 3
        
        # Login exitoso (resetea contador)
        auth.iniciar_sesion(email, password)
        assert auth.obtener_intentos_restantes(email) == 5
        
        # Otro intento fallido (cuenta desde 5)
        auth.iniciar_sesion(email, "Wrong3!")
        assert auth.obtener_intentos_restantes(email) == 4
    
    def test_flujo_bloqueo_no_afecta_otros_usuarios(self, sistema_completo):
        """Bloqueo de un usuario no afecta a otros."""
        auth = sistema_completo["auth"]
        
        # Dos usuarios
        email1 = "user1@test.com"
        email2 = "user2@test.com"
        password = "Pass123!"
        
        auth.registrar_usuario(email1, password)
        auth.registrar_usuario(email2, password)
        
        # Bloquear usuario 1
        for i in range(5):
            auth.iniciar_sesion(email1, f"Wrong{i}!")
        
        assert auth.usuario_esta_bloqueado(email1) is True
        
        # Usuario 2 debe seguir funcionando
        exito2, _ = auth.iniciar_sesion(email2, password)
        assert exito2 is True
        assert auth.usuario_esta_bloqueado(email2) is False


class TestFlujoRecuperacionPassword:
    """Pruebas del flujo completo de recuperación de contraseña."""
    
    def test_flujo_completo_recuperacion(self, sistema_completo):
        """Flujo: Solicitar recuperación → Cambiar password → Login."""
        auth = sistema_completo["auth"]
        
        email = "recupera@test.com"
        password_original = "Pass123!"
        password_nueva = "Nueva456!"
        
        # 1. Registro
        auth.registrar_usuario(email, password_original)
        
        # 2. Solicitar recuperación
        exito_solicitud, msg_solicitud = auth.solicitar_recuperacion_password(email)
        assert exito_solicitud is True
        assert "token" in msg_solicitud.lower()
        
        # 3. Cambiar contraseña
        exito_cambio, msg_cambio = auth.cambiar_password(email, password_nueva)
        assert exito_cambio is True
        
        # 4. Verificar que la antigua no funciona
        exito_antigua, _ = auth.iniciar_sesion(email, password_original)
        assert exito_antigua is False
        
        # 5. Verificar que la nueva funciona
        exito_nueva, _ = auth.iniciar_sesion(email, password_nueva)
        assert exito_nueva is True
    
    def test_flujo_recuperacion_desbloquea_usuario(self, sistema_completo):
        """Recuperación de password desbloquea usuario bloqueado."""
        auth = sistema_completo["auth"]
        
        email = "bloqueado@test.com"
        password_original = "Pass123!"
        password_nueva = "Nueva456!"
        
        # Registro y bloqueo
        auth.registrar_usuario(email, password_original)
        for i in range(5):
            auth.iniciar_sesion(email, f"Wrong{i}!")
        
        assert auth.usuario_esta_bloqueado(email) is True
        
        # Recuperación
        auth.solicitar_recuperacion_password(email)
        auth.cambiar_password(email, password_nueva)
        
        # Verificar desbloqueo
        assert auth.usuario_esta_bloqueado(email) is False
        assert auth.obtener_intentos_restantes(email) == 5
        
        # Verificar login
        exito, _ = auth.iniciar_sesion(email, password_nueva)
        assert exito is True
    
    def test_flujo_multiples_recuperaciones(self, sistema_completo):
        """Usuario puede recuperar password múltiples veces."""
        auth = sistema_completo["auth"]
        db = sistema_completo["db"]
        
        email = "multirec@test.com"
        auth.registrar_usuario(email, "Pass1!")
        
        # Primera recuperación
        exito1, msg1 = auth.solicitar_recuperacion_password(email)
        assert exito1 is True
        token1 = msg1.split(": ")[1] if ":" in msg1 else None
        
        # Segunda recuperación
        exito2, msg2 = auth.solicitar_recuperacion_password(email)
        assert exito2 is True
        token2 = msg2.split(": ")[1] if ":" in msg2 else None
        
        # Los tokens deben ser diferentes
        if token1 and token2:
            assert token1 != token2


# ============================================================================
# INTEGRACIÓN ENTRE COMPONENTES
# ============================================================================

class TestIntegracionBaseDatosServicio:
    """Pruebas de integración entre Database y AuthService."""
    
    def test_servicio_persiste_en_base_datos(self, sistema_completo):
        """Operaciones del servicio deben reflejarse en la BD."""
        auth = sistema_completo["auth"]
        db = sistema_completo["db"]
        
        email = "persist@test.com"
        password = "Pass123!"
        
        # Registrar mediante servicio
        auth.registrar_usuario(email, password)
        
        # Verificar en BD directamente
        usuario_bd = db.obtener_usuario(email)
        assert usuario_bd is not None
        assert usuario_bd['email'] == email
    
    def test_cambios_en_bd_visibles_en_servicio(self, sistema_completo):
        """Cambios directos en BD deben ser visibles en el servicio."""
        auth = sistema_completo["auth"]
        db = sistema_completo["db"]
        
        email = "directo@test.com"
        password = "Pass123!"
        
        # Crear usuario directamente en BD
        db.crear_usuario(email, password)
        
        # Verificar que el servicio puede usarlo
        exito, _ = auth.iniciar_sesion(email, password)
        assert exito is True
    
    def test_intentos_fallidos_sincronizados(self, sistema_completo):
        """Intentos fallidos en servicio deben actualizarse en BD."""
        auth = sistema_completo["auth"]
        db = sistema_completo["db"]
        
        email = "sync@test.com"
        auth.registrar_usuario(email, "Pass123!")
        
        # Intento fallido mediante servicio
        auth.iniciar_sesion(email, "Wrong!")
        
        # Verificar en BD
        usuario_bd = db.obtener_usuario(email)
        assert usuario_bd['intentos_fallidos'] == 1
    
    def test_bloqueo_sincronizado(self, sistema_completo):
        """Estado de bloqueo debe estar sincronizado."""
        auth = sistema_completo["auth"]
        db = sistema_completo["db"]
        
        email = "bloqueo_sync@test.com"
        auth.registrar_usuario(email, "Pass123!")
        
        # Bloquear mediante intentos fallidos
        for i in range(5):
            auth.iniciar_sesion(email, f"Wrong{i}!")
        
        # Verificar en BD
        usuario_bd = db.obtener_usuario(email)
        assert usuario_bd['bloqueado'] == 1
        
        # Verificar en servicio
        assert auth.usuario_esta_bloqueado(email) is True


# ============================================================================
# PRUEBAS DE CONSISTENCIA Y ESTADO
# ============================================================================

class TestConsistenciaEstado:
    """Pruebas de consistencia del estado del sistema."""
    
    def test_estado_consistente_despues_operaciones_mixtas(self, sistema_completo):
        """Estado debe ser consistente tras operaciones variadas."""
        auth = sistema_completo["auth"]
        
        email = "mixto@test.com"
        auth.registrar_usuario(email, "Pass1!")
        
        # Mezcla de operaciones
        auth.iniciar_sesion(email, "Pass1!")  # Exitoso
        auth.iniciar_sesion(email, "Wrong!")  # Fallido
        auth.cambiar_password(email, "Pass2!")  # Cambio
        auth.iniciar_sesion(email, "Pass2!")  # Exitoso con nueva
        
        # Verificar estado final
        assert auth.usuario_esta_bloqueado(email) is False
        assert auth.obtener_intentos_restantes(email) == 5
    
    def test_transacciones_atomicas(self, sistema_completo):
        """Operaciones deben ser atómicas (todo o nada)."""
        auth = sistema_completo["auth"]
        
        # Intentar registrar con datos inválidos no debe crear usuario parcial
        exito, _ = auth.registrar_usuario("invalido", "Pass123!")
        assert exito is False
        
        # Verificar que no se creó nada
        usuario = auth.db.obtener_usuario("invalido")
        assert usuario is None
    
    def test_concurrencia_basica(self, sistema_completo):
        """Sistema debe manejar operaciones secuenciales correctamente."""
        auth = sistema_completo["auth"]
        
        # Simular múltiples usuarios operando
        for i in range(10):
            email = f"concurrent{i}@test.com"
            password = f"Pass{i}!"
            
            auth.registrar_usuario(email, password)
            exito, _ = auth.iniciar_sesion(email, password)
            assert exito is True


# ============================================================================
# ESCENARIOS DE USO REAL
# ============================================================================

class TestEscenariosReales:
    """Pruebas basadas en escenarios de uso real."""
    
    def test_escenario_usuario_olvida_password(self, sistema_completo):
        """Escenario: Usuario olvida su contraseña."""
        auth = sistema_completo["auth"]
        
        email = "olvidadizo@test.com"
        password_original = "Pass123!"
        
        # Usuario se registra
        auth.registrar_usuario(email, password_original)
        auth.iniciar_sesion(email, password_original)
        
        # Usuario olvida password e intenta varias veces
        auth.iniciar_sesion(email, "Intento1!")
        auth.iniciar_sesion(email, "Intento2!")
        auth.iniciar_sesion(email, "Intento3!")
        
        # Usuario solicita recuperación
        exito_rec, _ = auth.solicitar_recuperacion_password(email)
        assert exito_rec is True
        
        # Usuario cambia password
        password_nueva = "Nueva456!"
        auth.cambiar_password(email, password_nueva)
        
        # Usuario puede hacer login con la nueva
        exito_final, _ = auth.iniciar_sesion(email, password_nueva)
        assert exito_final is True
    
    def test_escenario_ataque_fuerza_bruta(self, sistema_completo):
        """Escenario: Intento de ataque por fuerza bruta."""
        auth = sistema_completo["auth"]
        
        email = "victima@test.com"
        password_real = "Pass123!"
        
        # Usuario legítimo se registra
        auth.registrar_usuario(email, password_real)
        
        # Atacante intenta múltiples passwords
        passwords_atacante = [
            "123456", "password", "12345678", "qwerty", "abc123"
        ]
        
        for pwd in passwords_atacante:
            exito, _ = auth.iniciar_sesion(email, pwd)
            assert exito is False
        
        # Usuario debe estar bloqueado
        assert auth.usuario_esta_bloqueado(email) is True
        
        # Incluso el usuario real no puede entrar
        exito_real, msg = auth.iniciar_sesion(email, password_real)
        assert exito_real is False
        assert "bloqueado" in msg.lower()
    
    def test_escenario_usuario_cambia_password_periodicamente(self, sistema_completo):
        """Escenario: Usuario cambia password por seguridad."""
        auth = sistema_completo["auth"]
        
        email = "seguro@test.com"
        passwords = ["Pass1!", "Pass2!", "Pass3!"]
        
        # Registro inicial
        auth.registrar_usuario(email, passwords[0])
        
        # Cambios periódicos de password
        for i in range(len(passwords) - 1):
            # Login con password actual
            exito, _ = auth.iniciar_sesion(email, passwords[i])
            assert exito is True
            
            # Cambiar a siguiente
            auth.cambiar_password(email, passwords[i + 1])
            
            # Verificar que la anterior no funciona
            exito_antigua, _ = auth.iniciar_sesion(email, passwords[i])
            assert exito_antigua is False
        
        # Login final con última password
        exito_final, _ = auth.iniciar_sesion(email, passwords[-1])
        assert exito_final is True
    
    def test_escenario_cuenta_compartida_detectada(self, sistema_completo):
        """Escenario: Múltiples intentos desde diferentes lugares."""
        auth = sistema_completo["auth"]
        
        email = "compartida@test.com"
        password = "Pass123!"
        
        auth.registrar_usuario(email, password)
        
        # Varios logins exitosos consecutivos (uso normal)
        for _ in range(5):
            exito, _ = auth.iniciar_sesion(email, password)
            assert exito is True
        
        # Intentos fallidos intercalados (actividad sospechosa)
        auth.iniciar_sesion(email, "Wrong1!")
        auth.iniciar_sesion(email, password)  # Resetea intentos
        auth.iniciar_sesion(email, "Wrong2!")
        
        # La cuenta sigue funcionando pero se registran intentos
        intentos = auth.obtener_intentos_restantes(email)
        assert intentos == 4  # Se redujo por el último intento fallido


# ============================================================================
# PRUEBAS DE REGRESIÓN
# ============================================================================

class TestRegresion:
    """Pruebas para prevenir regresiones de bugs conocidos."""
    
    def test_bug_login_case_sensitive_email(self, sistema_completo):
        """Bug: Email debe ser case-sensitive."""
        auth = sistema_completo["auth"]
        
        email_original = "User@Test.com"
        password = "Pass123!"
        
        auth.registrar_usuario(email_original, password)
        
        # Login con mismo case debe funcionar
        exito_mismo, _ = auth.iniciar_sesion(email_original, password)
        assert exito_mismo is True
        
        # Login con diferente case no debe funcionar (emails son case-sensitive)
        exito_diferente, _ = auth.iniciar_sesion("user@test.com", password)
        # Esto debería fallar porque no existe ese email exacto
        assert exito_diferente is False
    
    def test_bug_intentos_no_se_acumulan_entre_usuarios(self, sistema_completo):
        """Bug: Intentos fallidos no deben afectar otros usuarios."""
        auth = sistema_completo["auth"]
        
        usuarios = [
            ("user1@test.com", "Pass1!"),
            ("user2@test.com", "Pass2!")
        ]
        
        for email, password in usuarios:
            auth.registrar_usuario(email, password)
        
        # Agotar intentos del usuario 1
        for i in range(5):
            auth.iniciar_sesion(usuarios[0][0], f"Wrong{i}!")
        
        # Usuario 2 debe tener intentos completos
        intentos_u2 = auth.obtener_intentos_restantes(usuarios[1][0])
        assert intentos_u2 == 5
    
    def test_bug_password_vacia_no_permitida(self, sistema_completo):
        """Bug: No debe permitir passwords vacías."""
        auth = sistema_completo["auth"]
        
        exito, _ = auth.registrar_usuario("test@test.com", "")
        assert exito is False
        
        exito2, _ = auth.registrar_usuario("test2@test.com", "   ")
        # Espacios no cumplen requisitos de longitud/caracteres
        assert exito2 is False


# ============================================================================
# PRUEBAS DE LIMITES DEL SISTEMA
# ============================================================================

class TestLimitesSistema:
    """Pruebas de los límites y capacidad del sistema."""
    
    def test_sistema_maneja_muchos_usuarios(self, sistema_completo):
        """Sistema debe manejar gran cantidad de usuarios."""
        auth = sistema_completo["auth"]
        
        cantidad_usuarios = 100
        
        # Crear muchos usuarios
        for i in range(cantidad_usuarios):
            email = f"user{i}@test.com"
            password = f"Pass{i}!"
            exito, _ = auth.registrar_usuario(email, password)
            assert exito is True
        
        # Verificar que todos pueden hacer login
        for i in range(0, cantidad_usuarios, 10):  # Probar algunos
            email = f"user{i}@test.com"
            password = f"Pass{i}!"
            exito, _ = auth.iniciar_sesion(email, password)
            assert exito is True
    
    def test_sistema_maneja_muchos_intentos_fallidos(self, sistema_completo):
        """Sistema debe manejar muchos intentos sin degradación."""
        auth = sistema_completo["auth"]
        
        email = "test@test.com"
        auth.registrar_usuario(email, "Pass123!")
        
        # Muchos intentos fallidos (más allá del bloqueo)
        for i in range(20):
            auth.iniciar_sesion(email, f"Wrong{i}!")
        
        # Sistema debe seguir funcionando
        assert auth.usuario_esta_bloqueado(email) is True
        assert auth.obtener_intentos_restantes(email) == 0
