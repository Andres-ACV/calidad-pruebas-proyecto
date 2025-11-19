"""
Pruebas de rendimiento con Locust.
Simula carga, estrés y volumen para el sistema de autenticación.

Ejecutar:
    locust -f tests/performance/locustfile.py --headless -u 100 -r 10 -t 30s
    
Parámetros:
    -u: Número de usuarios concurrentes (100)
    -r: Tasa de spawn de usuarios por segundo (10)
    -t: Tiempo de ejecución (30 segundos)
"""
import sys
from pathlib import Path
from locust import User, task, between, events
import random

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import Database
from src.auth_service import AuthService


class AutenticacionUser(User):
    """
    Usuario simulado que ejecuta operaciones de autenticación.
    """
    
    # Tiempo de espera entre tareas (1-3 segundos)
    wait_time = between(1, 3)
    
    def __init__(self, *args, **kwargs):
        """Inicializa el usuario con su propia instancia de servicios."""
        super().__init__(*args, **kwargs)
        
        # Cada usuario tiene su propia conexión a la BD
        self.db = Database("data/performance_test.db")
        self.auth_service = AuthService(self.db)
        
        # Generar email único para este usuario
        self.email = f"user_{random.randint(1, 1000000)}@loadtest.com"
        self.password = "Load123!"
        self.registered = False
    
    def on_start(self):
        """Se ejecuta cuando el usuario inicia (antes de las tareas)."""
        # Registrar el usuario al inicio
        exito, _ = self.auth_service.registrar_usuario(self.email, self.password)
        if exito:
            self.registered = True
    
    @task(5)  # Peso 5: se ejecuta con más frecuencia
    def login_exitoso(self):
        """
        Tarea: Login con credenciales correctas.
        Esta es la operación más común (peso 5).
        """
        if not self.registered:
            return
        
        start_time = events.request.fire.__self__.time()
        try:
            exito, mensaje = self.auth_service.iniciar_sesion(
                self.email, 
                self.password
            )
            
            total_time = int((events.request.fire.__self__.time() - start_time) * 1000)
            
            if exito:
                events.request.fire(
                    request_type="AUTH",
                    name="login_exitoso",
                    response_time=total_time,
                    response_length=len(mensaje),
                    exception=None,
                    context={}
                )
            else:
                events.request.fire(
                    request_type="AUTH",
                    name="login_exitoso",
                    response_time=total_time,
                    response_length=0,
                    exception=Exception(mensaje),
                    context={}
                )
        except Exception as e:
            total_time = int((events.request.fire.__self__.time() - start_time) * 1000)
            events.request.fire(
                request_type="AUTH",
                name="login_exitoso",
                response_time=total_time,
                response_length=0,
                exception=e,
                context={}
            )
    
    @task(2)  # Peso 2: menos frecuente
    def login_fallido(self):
        """
        Tarea: Login con credenciales incorrectas.
        Simula errores de usuario (peso 2).
        """
        if not self.registered:
            return
        
        start_time = events.request.fire.__self__.time()
        try:
            exito, mensaje = self.auth_service.iniciar_sesion(
                self.email, 
                "PasswordIncorrecta123!"
            )
            
            total_time = int((events.request.fire.__self__.time() - start_time) * 1000)
            
            events.request.fire(
                request_type="AUTH",
                name="login_fallido",
                response_time=total_time,
                response_length=len(mensaje),
                exception=None if not exito else Exception("Debería haber fallado"),
                context={}
            )
        except Exception as e:
            total_time = int((events.request.fire.__self__.time() - start_time) * 1000)
            events.request.fire(
                request_type="AUTH",
                name="login_fallido",
                response_time=total_time,
                response_length=0,
                exception=e,
                context={}
            )
    
    @task(1)  # Peso 1: poco frecuente
    def registro_nuevo_usuario(self):
        """
        Tarea: Registro de nuevo usuario.
        Menos común que login (peso 1).
        """
        start_time = events.request.fire.__self__.time()
        try:
            # Generar email único
            nuevo_email = f"new_user_{random.randint(1, 10000000)}@loadtest.com"
            
            exito, mensaje = self.auth_service.registrar_usuario(
                nuevo_email, 
                "NewUser123!"
            )
            
            total_time = int((events.request.fire.__self__.time() - start_time) * 1000)
            
            if exito:
                events.request.fire(
                    request_type="AUTH",
                    name="registro_usuario",
                    response_time=total_time,
                    response_length=len(mensaje),
                    exception=None,
                    context={}
                )
            else:
                events.request.fire(
                    request_type="AUTH",
                    name="registro_usuario",
                    response_time=total_time,
                    response_length=0,
                    exception=Exception(mensaje),
                    context={}
                )
        except Exception as e:
            total_time = int((events.request.fire.__self__.time() - start_time) * 1000)
            events.request.fire(
                request_type="AUTH",
                name="registro_usuario",
                response_time=total_time,
                response_length=0,
                exception=e,
                context={}
            )
    
    @task(1)  # Peso 1: poco frecuente
    def validar_email(self):
        """
        Tarea: Validación de email.
        Operación ligera para medir rendimiento de validaciones (peso 1).
        """
        start_time = events.request.fire.__self__.time()
        try:
            emails_test = [
                "valido@ejemplo.com",
                "invalido",
                f"test_{random.randint(1, 1000)}@test.com"
            ]
            email = random.choice(emails_test)
            
            valido, mensaje = self.auth_service.validar_email(email)
            
            total_time = int((events.request.fire.__self__.time() - start_time) * 1000)
            
            events.request.fire(
                request_type="VALIDATION",
                name="validar_email",
                response_time=total_time,
                response_length=len(mensaje),
                exception=None,
                context={}
            )
        except Exception as e:
            total_time = int((events.request.fire.__self__.time() - start_time) * 1000)
            events.request.fire(
                request_type="VALIDATION",
                name="validar_email",
                response_time=total_time,
                response_length=0,
                exception=e,
                context={}
            )
    
    @task(1)  # Peso 1: poco frecuente
    def solicitar_recuperacion(self):
        """
        Tarea: Solicitar recuperación de contraseña.
        Operación ocasional (peso 1).
        """
        if not self.registered:
            return
        
        start_time = events.request.fire.__self__.time()
        try:
            exito, mensaje = self.auth_service.solicitar_recuperacion_password(
                self.email
            )
            
            total_time = int((events.request.fire.__self__.time() - start_time) * 1000)
            
            if exito:
                events.request.fire(
                    request_type="AUTH",
                    name="recuperacion_password",
                    response_time=total_time,
                    response_length=len(mensaje),
                    exception=None,
                    context={}
                )
            else:
                events.request.fire(
                    request_type="AUTH",
                    name="recuperacion_password",
                    response_time=total_time,
                    response_length=0,
                    exception=Exception(mensaje),
                    context={}
                )
        except Exception as e:
            total_time = int((events.request.fire.__self__.time() - start_time) * 1000)
            events.request.fire(
                request_type="AUTH",
                name="recuperacion_password",
                response_time=total_time,
                response_length=0,
                exception=e,
                context={}
            )


# ============================================================================
# ESCENARIOS DE PRUEBA
# ============================================================================

class PruebasCarga(AutenticacionUser):
    """
    Escenario 1: Pruebas de Carga
    Simula 100 usuarios concurrentes durante 30 segundos.
    
    Ejecutar:
        locust -f locustfile.py --headless -u 100 -r 10 -t 30s --tags carga
    """
    pass


class PruebasEstres(AutenticacionUser):
    """
    Escenario 2: Pruebas de Estrés
    Incrementa usuarios hasta sobrecargar el sistema.
    
    Ejecutar:
        locust -f locustfile.py --headless -u 500 -r 50 -t 60s --tags estres
    """
    # Menos tiempo de espera = más presión
    wait_time = between(0.1, 0.5)


class PruebasVolumen(AutenticacionUser):
    """
    Escenario 3: Pruebas de Volumen
    Crea gran cantidad de usuarios en la base de datos.
    
    Ejecutar:
        locust -f locustfile.py --headless -u 50 -r 5 -t 120s --tags volumen
    """
    
    @task(10)  # Mayoría de tareas son registros
    def registro_masivo(self):
        """Registra usuarios masivamente para llenar la BD."""
        self.registro_nuevo_usuario()


# ============================================================================
# EVENTOS Y REPORTES
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Se ejecuta al iniciar las pruebas."""
    print("=" * 60)
    print("INICIANDO PRUEBAS DE RENDIMIENTO")
    print("=" * 60)
    print(f"Base de datos: data/performance_test.db")
    print(f"Usuarios concurrentes: {environment.parsed_options.num_users if hasattr(environment, 'parsed_options') else 'N/A'}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Se ejecuta al finalizar las pruebas."""
    print("\n" + "=" * 60)
    print("PRUEBAS DE RENDIMIENTO FINALIZADAS")
    print("=" * 60)
    
    # Limpiar base de datos de prueba
    db_path = Path("data/performance_test.db")
    if db_path.exists():
        try:
            db_path.unlink()
            print("✓ Base de datos de prueba eliminada")
        except:
            print("⚠ No se pudo eliminar la base de datos de prueba")
    
    print("=" * 60)


# ============================================================================
# INSTRUCCIONES DE USO
# ============================================================================

"""
COMANDOS ÚTILES:

1. Pruebas de Carga (100 usuarios, 30 segundos):
   locust -f tests/performance/locustfile.py --headless -u 100 -r 10 -t 30s

2. Pruebas de Estrés (500 usuarios, 60 segundos):
   locust -f tests/performance/locustfile.py --headless -u 500 -r 50 -t 60s

3. Pruebas de Volumen (50 usuarios, 2 minutos):
   locust -f tests/performance/locustfile.py --headless -u 50 -r 5 -t 120s

4. Modo Interactivo (con interfaz web en http://localhost:8089):
   locust -f tests/performance/locustfile.py

5. Ver estadísticas en CSV:
   locust -f tests/performance/locustfile.py --headless -u 100 -r 10 -t 30s --csv=results

MÉTRICAS IMPORTANTES:
- Response Time (ms): Tiempo de respuesta promedio
- RPS (Requests per Second): Solicitudes por segundo
- Failure Rate (%): Porcentaje de fallos
- 95th Percentile: 95% de solicitudes más rápidas que este valor
"""
