#!/usr/bin/env python3
import sys
import os
import random
from pathlib import Path

if sys.version_info < (3, 11):
    print("Erro: Python 3.11+ é necessário.")
    sys.exit(1)

port = 9020
os.environ['OBSERVADOR_PORT'] = str(port)
print(f"OBSERVADOR iniciando na porta {port}")

base_path = Path(__file__).parent
sys.path.insert(0, str(base_path))

storage_path = base_path / "storage"
storage_path.mkdir(exist_ok=True)

readings_file = storage_path / "readings.jsonl"
if not readings_file.exists():
    readings_file.touch()

errors_file = storage_path / "errors.log"
if not errors_file.exists():
    errors_file.touch()

try:
    from web.app import create_app
    
    app = create_app()
    app.run(host='0.0.0.0', port=port, debug=False)
except KeyboardInterrupt:
    sys.exit(0)
except Exception as e:
    error_msg = f"Interferência detectada. O Véu se fecha momentaneamente."
    print(error_msg)
    
    import traceback
    with open(errors_file, 'a', encoding='utf-8') as f:
        from datetime import datetime
        f.write(f"\n[{datetime.now()}] {traceback.format_exc()}\n")
    
    sys.exit(1)
