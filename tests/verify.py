#!/usr/bin/env python3
"""Pruebas de cifrado completo, limites MPI y terminacion sin coincidencia."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
BIN = str(ROOT / 'bin/bruteforce_mpi')
PHRASE = 'ciencia con paciencia'

def run(args, code=0):
    p = subprocess.run(args, text=True, capture_output=True, timeout=45)
    assert p.returncode == code, (args, p.returncode, p.stdout, p.stderr)
    return p.stdout

checks = 0
run([BIN, 'selftest']); checks += 1
with tempfile.TemporaryDirectory() as td:
    temp = Path(td)
    cipher = temp / 'cipher.des'
    recovered = temp / 'recovered.txt'
    # Rango no divisible entre 3; incluye 0 y el ultimo candidato.
    for key in [0, 3, 4, 7, 9, 10]:
        run([BIN, 'encrypt', '--text', 'data/texto.txt', '--key', str(key), '--out', str(cipher)])
        for strategy in ['block', 'cyclic']:
            args = ['mpirun', '--bind-to', 'none', '-np', '3', BIN, 'search', '--cipher', str(cipher),
                    '--phrase', PHRASE, '--upper', '11', '--strategy', strategy,
                    '--batch', '2', '--out', str(recovered)]
            row = json.loads(run(args))
            assert row['found'] == key, row
            assert recovered.read_bytes() == Path('data/texto.txt').read_bytes()
            checks += 1
    # Mas procesos que candidatos, y llave 56-bit grande dentro de una ventana.
    for lower, upper, key in [(0, 2, 1), ((1 << 54) - 5, (1 << 54) + 6, 1 << 54),
                              ((1 << 56) - 4, 1 << 56, (1 << 56) - 1)]:
        run([BIN, 'encrypt', '--text', 'data/texto.txt', '--key', str(key), '--out', str(cipher)])
        for strategy in ['block', 'cyclic']:
            row = json.loads(run(['mpirun', '--bind-to', 'none', '-np', '4', BIN, 'search',
                '--cipher', str(cipher), '--phrase', PHRASE, '--lower', str(lower),
                '--upper', str(upper), '--strategy', strategy, '--batch', '2', '--mode', 'full']))
            assert row['found'] == key and row['attempts'] == upper - lower, row
            checks += 1
    # Sin coincidencia termina de forma colectiva, devolviendo codigo 2.
    row = json.loads(run(['mpirun', '--bind-to', 'none', '-np', '3', BIN, 'search',
        '--cipher', str(cipher), '--phrase', PHRASE, '--upper', '11', '--batch', '2'], code=2))
    assert row['found'] is None and row['attempts'] == 11
    checks += 1
    # Longitud mal formada debe rechazarse antes de DES.
    cipher.write_bytes(b'invalid')
    run([BIN, 'search', '--cipher', str(cipher), '--phrase', PHRASE, '--upper', '11'], code=1)
    checks += 1
assert len(Path('data/texto.txt').read_text().split()) == 350
checks += 1
print(f'PASS: {checks} comprobaciones; vector conocido, texto completo, limites, llaves grandes y sin coincidencia.')
