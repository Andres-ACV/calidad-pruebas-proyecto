# Sistema de Autenticación - Proyecto de Calidad y Pruebas

## 📋 Descripción

Sistema de autenticación con interfaz gráfica desarrollado en Python usando Tkinter y SQLite. El proyecto incluye un completo sistema de pruebas automatizadas que cubre todos los aspectos del ciclo de vida del software.

## ✨ Características

### Funcionalidades Principales
- ✅ **Autenticación de usuarios** con email y contraseña
- ✅ **Registro de nuevos usuarios** con validaciones robustas
- ✅ **Recuperación de contraseña** vía email (token)
- ✅ **Sistema de intentos limitados** (5 intentos antes de bloqueo)
- ✅ **Base de datos SQLite** persistente
- ✅ **Interfaz gráfica moderna** con colores y validaciones en tiempo real

### Validaciones de Contraseña
- Longitud: 5-10 caracteres
- Al menos una letra mayúscula
- Al menos un carácter especial (!@#$%^&*...)
- Validación en tiempo real durante el registro

### Validaciones de Email
- Formato estándar de email (RFC 5322)
- Validación en tiempo real

## 🏗️ Arquitectura del Proyecto

```
calidad-pruebas-proyecto/
│
├── src/                          # Código fuente
│   ├── __init__.py
│   ├── database.py              # Gestión de BD SQLite
│   ├── auth_service.py          # Lógica de autenticación
│   └── ui_login.py              # Interfaz gráfica (Tkinter)
│
├── tests/                        # Pruebas automatizadas
│   ├── __init__.py
│   ├── test_database.py         # Pruebas unitarias de BD
│   ├── test_auth_service.py     # Pruebas unitarias de servicio
│   ├── test_integration.py      # Pruebas de integración
│   ├── test_security.py         # Pruebas de seguridad
│   └── performance/             # Pruebas de rendimiento
│       └── locustfile.py
│
├── data/                         # Base de datos (generada al ejecutar)
│   └── auth_system.db
│
├── main.py                       # Punto de entrada
├── requirements.txt              # Dependencias
└── README.md                     # Este archivo
```

## 🚀 Instalación y Uso

### Prerrequisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- tkinter (interfaz gráfica)

### Instalación

1. **Clonar el repositorio**
```bash
git clone <url-del-repositorio>
cd calidad-pruebas-proyecto
```

2. **Crear entorno virtual (recomendado)**
```bash
python3 -m venv .venv
source .venv/bin/activate  # En Linux/Mac
# .venv\Scripts\activate   # En Windows
```

3. **Instalar tkinter (solo en Linux/WSL)**
```bash
# Ubuntu/Debian/WSL
sudo apt-get update
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

**Nota**: En Windows y macOS, tkinter viene incluido con Python.

4. **Instalar dependencias de Python**
```bash
pip install -r requirements.txt
```

3. **(Opcional) Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus credenciales SMTP si deseas enviar emails reales
```

### Ejecutar la Aplicación

```bash
python main.py
```

La aplicación abrirá una ventana gráfica donde podrás:
1. **Registrar** un nuevo usuario
2. **Iniciar sesión** con credenciales existentes
3. **Recuperar contraseña** si la olvidaste

## 🧪 Pruebas

El proyecto incluye un completo sistema de pruebas automatizadas:

### Pruebas Unitarias

Probar módulos individuales:
```bash
# Todas las pruebas unitarias
pytest tests/test_*.py -v

# Solo base de datos
pytest tests/test_database.py -v

# Solo servicio de autenticación
pytest tests/test_auth_service.py -v
```

### Pruebas de Integración

```bash
pytest tests/test_integration.py -v
```

### Pruebas de Seguridad

```bash
# Análisis estático con Bandit
bandit -r src/ -f txt -o docs/reporte_seguridad.txt

# Pruebas de inyección SQL y otras
pytest tests/test_security.py -v
```

### Pruebas de Rendimiento

```bash
cd tests/performance
locust -f locustfile.py --headless -u 100 -r 10 -t 30s
```

### Cobertura de Código

```bash
pytest --cov=src --cov-report=html --cov-report=term
```

El reporte HTML se generará en `htmlcov/index.html`

## 📊 Plan de Pruebas

El proyecto incluye los siguientes tipos de pruebas:

### Caja Negra
- Validación de entradas
- Casos límite (boundary testing)
- Flujos de usuario completos

### Pruebas Unitarias
- Validación de email
- Validación de contraseña
- Hash de contraseñas
- CRUD de base de datos

### Pruebas de Integración
- Flujo completo de registro + login
- Sistema de intentos fallidos
- Recuperación de contraseña

### Pruebas de Sistema y UAT
- Escenarios de usuario final
- Validaciones de interfaz
- Mensajes de error apropiados

### Pruebas de Rendimiento
- **Carga**: 100 usuarios concurrentes
- **Estrés**: Incremento gradual hasta fallo
- **Volumen**: Miles de registros en BD

### Pruebas de Seguridad
- Inyección SQL
- Hash seguro de contraseñas (SHA-256)
- Bloqueo por intentos fallidos
- Análisis de vulnerabilidades (Bandit)

### Pruebas de Usabilidad
- Validaciones en tiempo real
- Mensajes claros de error
- Interfaz intuitiva
- Accesibilidad (colores, tamaños)

### Pruebas de Compatibilidad
- Python 3.8, 3.9, 3.10, 3.11, 3.12
- Windows, Linux, macOS
- Tkinter estándar (sin dependencias externas)

### Pruebas de Recuperación
- Manejo de errores de BD
- Manejo de archivos corruptos
- Recuperación de conexión

## 🔒 Seguridad

El sistema implementa las siguientes medidas de seguridad:

1. **Hashing de Contraseñas**: SHA-256 (no se almacenan en texto plano)
2. **Límite de Intentos**: 5 intentos fallidos antes de bloqueo
3. **Validaciones Robustas**: Email y contraseña validados
4. **Protección SQL Injection**: Uso de parámetros en queries
5. **Tokens Seguros**: Generación criptográfica para recuperación

## 🛠️ Tecnologías Utilizadas

- **Python 3.8+**: Lenguaje principal
- **Tkinter**: Interfaz gráfica
- **SQLite3**: Base de datos
- **pytest**: Framework de pruebas
- **Bandit**: Análisis de seguridad
- **Locust**: Pruebas de carga
- **hashlib**: Hashing de contraseñas