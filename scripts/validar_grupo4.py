#!/usr/bin/env python3
"""Ejecuta y conserva una prueba local acotada del cifrado recibido del grupo 4."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shlex
import subprocess
import time
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PHRASE = 'la busqueda distribuida termina cuando aparece la frase clave'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lower', type=int, default=0)
    parser.add_argument('--upper', type=int, default=1048576)
    parser.add_argument('--processes', type=int, default=4)
    parser.add_argument('--padding', choices=['pkcs7', 'none'], default='none')
    parser.add_argument('--mode', choices=['early', 'full'], default='early')
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--warmups', type=int, default=0)
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args()
    folder = ROOT / 'fase2/grupo4'
    logs = folder / 'pruebas'
    logs.mkdir(parents=True, exist_ok=True)
    index = 1
    while (logs / f'prueba_{index:03}.json').exists():
        index += 1
    label = f'prueba_{index:03}'
    recovered = f'fase2/grupo4/pruebas/{label}_recuperado.txt'
    command = ['mpirun', '--bind-to', 'none', '-np', str(args.processes),
               './bin/bruteforce_mpi', 'search', '--cipher', 'fase2/grupo4/texto_cifrado.des',
               '--phrase', PHRASE, '--lower', str(args.lower), '--upper', str(args.upper),
               '--strategy', 'block', '--mode', args.mode, '--batch', '128',
               '--padding', args.padding, '--repeats', str(args.repeats),
               '--warmups', str(args.warmups),
               '--stats', f'fase2/grupo4/pruebas/{label}', '--out', recovered]
    record = {'inicio': datetime.now(ZoneInfo('America/Guatemala')).isoformat(),
              'plataforma': platform.platform(), 'argv': command,
              'sha256_cifrado': hashlib.sha256((folder / 'texto_cifrado.des').read_bytes()).hexdigest(),
              'sha256_ejecutable': hashlib.sha256((ROOT / 'bin/bruteforce_mpi').read_bytes()).hexdigest(),
              'caracter': 'prueba local; rango elegido para comparacion, no confirmado por emisor'}
    t0 = time.monotonic()
    try:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=args.timeout)
        record['timeout'] = False
    except subprocess.TimeoutExpired as exc:
        def decoded(value):
            return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else (value or '')
        result = subprocess.CompletedProcess(command, 124, decoded(exc.stdout), decoded(exc.stderr))
        record['timeout'] = True
    record.update(fin=datetime.now(ZoneInfo('America/Guatemala')).isoformat(),
                  duracion_externa_s=time.monotonic() - t0, codigo_salida=result.returncode)
    rows = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
    record['resultados'] = rows
    record['archivo_recuperado_generado'] = (ROOT / recovered).exists()
    if record['archivo_recuperado_generado']:
        content = (ROOT / recovered).read_bytes()
        record['recuperacion'] = {'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest(),
                                  'frase_presente': PHRASE.encode() in content}
    (logs / f'{label}.stdout.log').write_text(result.stdout, encoding='utf-8')
    (logs / f'{label}.stderr.log').write_text(result.stderr, encoding='utf-8')
    (logs / f'{label}.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    with (ROOT / 'BITACORA.md').open('a', encoding='utf-8') as journal:
        journal.write(f'\n## Nueva prueba {label}\n\nFecha local: {record["inicio"]}.\n\n')
        journal.write('```bash\n' + shlex.join(command) + '\n```\n\n')
        journal.write(f'Código de salida: {result.returncode}. Evidencia: `fase2/grupo4/pruebas/{label}.json`.\n\n')
        journal.write('Resultado observado: `' + json.dumps(rows, ensure_ascii=False) + '`.\n')
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
