#!/usr/bin/env python3
"""Regresion de interoperabilidad del grupo 4 y soporte sin relleno."""
from pathlib import Path
import subprocess
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
BIN = str(ROOT / 'bin/bruteforce_mpi')
PHRASE = 'la busqueda distribuida termina cuando aparece la frase clave'
CIPHER = ROOT / 'fase2/grupo4/texto_cifrado.des'


def run(args, code=0):
    p = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=45)
    assert p.returncode == code, (args, p.returncode, p.stdout, p.stderr)
    return p.stdout


with tempfile.TemporaryDirectory() as td:
    temp = Path(td)
    for strategy in ['block', 'cyclic']:
        out = temp / f'{strategy}.txt'
        result = json.loads(run(['mpirun', '--bind-to', 'none', '-np', '3', BIN, 'search',
            '--cipher', str(CIPHER), '--phrase', PHRASE, '--lower', '899997', '--upper', '900003',
            '--strategy', strategy, '--padding', 'none', '--out', str(out)]))
        plain = out.read_bytes()
        assert result['found'] == 900000 and result['padding'] == 'none'
        assert PHRASE in plain.decode('utf-8') and len(plain) == 2192
        encrypted = temp / f'{strategy}.des'
        run([BIN, 'encrypt', '--text', str(out), '--key', '900000', '--padding', 'none', '--out', str(encrypted)])
        assert encrypted.read_bytes() == CIPHER.read_bytes()
    # El valor predeterminado sigue rechazando un final sin PKCS#7.
    result = json.loads(run([BIN, 'search', '--cipher', str(CIPHER), '--phrase', PHRASE,
        '--lower', '900000', '--upper', '900001'], code=2))
    assert result['found'] is None and result['padding'] == 'pkcs7'
    bad = temp / 'no_multiple.txt'
    bad.write_bytes(b'12345')
    run([BIN, 'encrypt', '--text', str(bad), '--key', '1', '--padding', 'none', '--out', str(temp/'bad.des')], code=1)
print('PASS fase 2: block, cyclic, frase UTF-8, recifrado exacto, PKCS#7 predeterminado y rechazo de longitud invalida.')
