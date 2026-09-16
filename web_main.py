"""
Ponto de Entrada do Dashboard Web Flask.
HAOC VoIP Monitor Enterprise.
"""
import os
import sys

# Adicionar raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from haoc_voip.core.database import db
from haoc_voip.core.monitor import monitor_engine
from haoc_voip.web.app import create_app

def main():
    # Inicializar banco de dados SQLite
    db.init_db()

    app = create_app()

    port = int(os.environ.get("FLASK_PORT", 5050))
    host = os.environ.get("FLASK_HOST", "0.0.0.0")

    print(f"[*] Iniciando HAOC VoIP Monitor Web Dashboard em http://{host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)

if __name__ == "__main__":
    main()
