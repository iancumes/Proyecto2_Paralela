#!/usr/bin/env python3
"""Experimento real, secuencial entre configuraciones, sin mediciones simultaneas."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess
import json
import random
import hashlib
import platform
import time
import os

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
BIN = str(ROOT / 'bin/bruteforce_mpi')
KEYS = [8192, 135168, 249856]
UPPER = 262144
PHRASE = 'ciencia con paciencia'

def command(args):
    return subprocess.run(args, text=True, capture_output=True, check=True, timeout=180)

metadata = {
    'started_local': datetime.now(ZoneInfo('America/Guatemala')).isoformat(),
    'platform': platform.platform(), 'cpu': command(['sysctl', '-n', 'machdep.cpu.brand_string']).stdout.strip(),
    'logical_cpus': os.cpu_count(), 'memory_bytes': int(command(['sysctl','-n','hw.memsize']).stdout),
    'mpi': command(['mpirun', '--version']).stdout.strip(),
    'openssl': command(['openssl', 'version']).stdout.strip(),
    'compiler': command(['clang', '--version']).stdout.splitlines()[0],
    'text_words': len(Path('data/texto.txt').read_text().split()),
    'text_bytes': len(Path('data/texto.txt').read_bytes()),
    'text_sha256': hashlib.sha256(Path('data/texto.txt').read_bytes()).hexdigest(),
    'space': [0, UPPER], 'keys': KEYS, 'processes': [1,2,4,8],
    'repeats': 5, 'warmups_per_case': 1, 'batch': 128, 'seed': 20261015,
    'binding': 'none', 'hosts': 1, 'phrase': PHRASE,
    'timed': 'MPI_MAX de duraciones locales, despues de MPI_Barrier; incluye calculo y Allreduce; excluye E/S, cifrado, arranque y Gather de estadisticas',
}
Path('results/metadata.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
for key in KEYS:
    p = command([BIN, 'encrypt', '--text', 'data/texto.txt', '--key', str(key), '--out', f'data/key_{key}.des'])
    Path(f'results/encrypt_{key}.log').write_text(p.stdout)
cases = [(key, p, strategy, 'early') for key in KEYS for p in [1,2,4,8] for strategy in ['block','cyclic']]
cases += [(key, p, 'block', 'full') for key in KEYS for p in [1,2,4,8]]
random.Random(metadata['seed']).shuffle(cases)
all_rows = []
start = time.monotonic()
with open('results/commands.jsonl', 'w') as commands, open('results/raw.jsonl', 'w') as raw:
    for i, (key, p, strategy, mode) in enumerate(cases, 1):
        label = f'k{key}_p{p}_{strategy}_{mode}'
        args = ['mpirun', '--bind-to', 'none', '-np', str(p), BIN, 'search',
            '--cipher', f'data/key_{key}.des', '--phrase', PHRASE, '--upper', str(UPPER),
            '--strategy', strategy, '--mode', mode, '--batch', '128', '--repeats', '5',
            '--warmups', '1', '--stats', f'results/{label}', '--out', f'data/recovered_{key}.txt']
        commands.write(json.dumps({'case':label,'argv':args}) + '\n'); commands.flush()
        result = command(args)
        Path(f'results/{label}.log').write_text(result.stdout + result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
        assert len(rows) == 5 and all(row['found'] == key for row in rows)
        assert Path(f'data/recovered_{key}.txt').read_bytes() == Path('data/texto.txt').read_bytes()
        for row in rows:
            row.update(key=key, case=label)
            raw.write(json.dumps(row) + '\n')
            all_rows.append(row)
        raw.flush()
        print(f'{i:02}/{len(cases)} {label}: mean={sum(r["seconds"] for r in rows)/5:.4f}s elapsed={time.monotonic()-start:.1f}s', flush=True)
metadata['finished_local'] = datetime.now(ZoneInfo('America/Guatemala')).isoformat()
metadata['wall_seconds'] = time.monotonic() - start
metadata['measured_runs'] = len(all_rows)
Path('results/metadata.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
print(f'COMPLETE: {len(all_rows)} mediciones reales.', flush=True)
