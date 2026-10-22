#!/usr/bin/env python3
"""Conserva la certificacion de recuperacion y recifrado del grupo 4."""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / 'fase2/grupo4'
trials = sorted((folder/'pruebas').glob('prueba_*.json'))
for path in reversed(trials):
    record = json.loads(path.read_text(encoding='utf-8'))
    if record.get('codigo_salida') == 0 and record.get('archivo_recuperado_generado'):
        recovered = ROOT / record['argv'][record['argv'].index('--out')+1]
        key = record['resultados'][0]['found']
        break
else:
    raise SystemExit('No hay una recuperacion MPI exitosa')
plain = recovered.read_bytes()
text = plain.decode('utf-8')
assert 'la busqueda distribuida termina cuando aparece la frase clave' in text
with tempfile.TemporaryDirectory() as td:
    encrypted = Path(td)/'control.des'
    subprocess.run([str(ROOT/'bin/bruteforce_mpi'), 'encrypt', '--text', str(recovered),
        '--key', str(key), '--padding', 'none', '--out', str(encrypted)], check=True)
    assert encrypted.read_bytes() == (folder/'texto_cifrado.des').read_bytes()
(folder/'texto_recuperado.txt').write_bytes(plain)
result = {'key_index': key, 'padding_retirado': 'none', 'bytes': len(plain),
          'palabras_separadas_por_espacios': len(text.split()),
          'sha256_plain': hashlib.sha256(plain).hexdigest(),
          'sha256_cipher': hashlib.sha256((folder/'texto_cifrado.des').read_bytes()).hexdigest(),
          'frase_exacta_presente': True, 'utf8_valido': True, 'recifrado_identico': True,
          'confirmacion_del_emisor': 'pendiente', 'origen_mpi': str(path.relative_to(ROOT))}
(folder/'validacion_recuperacion.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(result, indent=2, ensure_ascii=False))
