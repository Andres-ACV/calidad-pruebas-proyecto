"""
Punto de entrada principal de la aplicación.
Inicializa la base de datos y lanza la interfaz gráfica.
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent))

from src.ui_login import iniciar_aplicacion


def main():
    """
    Función principal que inicia la aplicación.
    """
    print("=" * 50)
    print("Sistema de Autenticación - v1.0.0")
    print("=" * 50)
    print("Iniciando aplicación...")
    print("Base de datos: data/auth_system.db")
    print("-" * 50)
    
    try:
        iniciar_aplicacion()
    except KeyboardInterrupt:
        print("\n\nAplicación cerrada por el usuario.")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
