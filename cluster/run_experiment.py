#!/usr/bin/env python3
"""Registra una busqueda local, un ensayo virtual o una ejecucion fisica.

Ejecutar dentro del contenedor maestro en /opt/proyecto2.
"""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import ipaddress
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path('/opt/proyecto2')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--kind', choices=['local', 'rehearsal', 'physical'], required=True)
    ap.add_argument('--hostfile', type=Path)
    ap.add_argument('--subnet')
    ap.add_argument('--processes', type=int, required=True)
    ap.add_argument('--mode', choices=['early', 'full'], default='full')
    ap.add_argument('--repeats', type=int, default=3)
    ap.add_argument('--warmups', type=int, default=1)
    ap.add_argument('--upper', type=int, default=1048576)
    ap.add_argument('--timeout', type=int, default=1200)
    a = ap.parse_args()
    stamp = datetime.now(timezone(timedelta(hours=-6))).strftime('%Y%m%d_%H%M%S_%f')
    folder = ROOT / 'fase2/resultados' / f'{stamp}_{a.kind}_p{a.processes}_{a.mode}'
    folder.mkdir(parents=True)
    record = {'inicio_guatemala': stamp, 'kind': a.kind,
              'nota': 'Ensayo en una computadora' if a.kind != 'physical' else 'Requiere capturas y confirmacion de nodos fisicos',
              'config': vars(a).copy(), 'commands': [], 'ok': False}
    record['config']['hostfile'] = str(a.hostfile) if a.hostfile else None

    def execute(label, cmd):
        record['commands'].append({'label': label, 'argv': cmd, 'shell': shlex.join(cmd)})
        try:
            p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=a.timeout)
        except subprocess.TimeoutExpired as e:
            def txt(x):
                return x.decode(errors='replace') if isinstance(x, bytes) else (x or '')
            p = subprocess.CompletedProcess(cmd, 124, txt(e.stdout), txt(e.stderr))
        (folder / f'{label}.stdout.log').write_text(p.stdout)
        (folder / f'{label}.stderr.log').write_text(p.stderr)
        if p.returncode:
            raise RuntimeError(f'{label}: codigo {p.returncode}; revisar logs')
        return p.stdout

    started = time.monotonic()
    try:
        source_hash = hashlib.sha256((ROOT/'src/bruteforce_mpi.c').read_bytes()).hexdigest()
        cipher_hash = hashlib.sha256((ROOT/'fase2/grupo4/texto_cifrado.des').read_bytes()).hexdigest()
        record.update(source_sha256=source_hash, cipher_sha256=cipher_hash)
        execute('versions', ['bash', '-c', 'uname -m; mpirun --version; openssl version; nproc'])
        mpi = ['mpirun', '--bind-to', 'none', '--nooversubscribe',
               '--mca', 'pml', 'ob1', '--mca', 'btl', 'self,vader,tcp']
        if a.kind != 'local':
            if not a.hostfile or not a.subnet:
                raise ValueError('hostfile y subnet son obligatorios')
            subnet = ipaddress.ip_network(a.subnet, strict=False)
            nodes = []
            for line in a.hostfile.read_text().splitlines():
                words = line.split('#', 1)[0].split()
                if not words:
                    continue
                address = ipaddress.ip_address(words[0])
                opts = dict(word.split('=', 1) for word in words[1:])
                slots = int(opts['slots'])
                maximum = int(opts['max_slots'])
                if address not in subnet or slots <= 0 or maximum < slots:
                    raise ValueError('IP fuera de la subred o slots invalidos')
                nodes.append((str(address), slots, maximum))
            if len(nodes) < 2 or len(set(n[0] for n in nodes)) != len(nodes):
                raise ValueError('Se requieren al menos dos IP distintas')
            if a.processes > sum(n[1] for n in nodes) or a.processes < len(nodes):
                raise ValueError('Procesos fuera de slots o insuficientes para usar todos los nodos')
            interfaces = json.loads(execute('interfaces', ['ip', '-j', '-4', 'addr']))
            visible = [ipaddress.ip_address(v['local']) for x in interfaces for v in x.get('addr_info', [])]
            if not any(ip in subnet for ip in visible):
                raise ValueError('La subred no existe dentro del contenedor; revisar limitacion L4 de Docker Desktop y guia Mac')
            for i, (address, slots, maximum) in enumerate(nodes):
                output = execute(f'ssh_{i}', ['ssh', f'root@{address}',
                    'cd /opt/proyecto2 && hostname && nproc && sha256sum src/bruteforce_mpi.c fase2/grupo4/texto_cifrado.des'])
                lines = output.splitlines()
                if len(lines) < 4 or maximum > int(lines[1]):
                    raise ValueError('max_slots supera CPU disponibles en el nodo')
                if source_hash not in output or cipher_hash not in output:
                    raise ValueError('Los nodos no tienen el mismo codigo o criptograma')
            normalized_hosts = folder/'cluster_hosts'
            normalized_hosts.write_text(a.hostfile.read_text())
            mpi += ['--hostfile', str(normalized_hosts), '--map-by', 'node',
                    '--mca', 'btl_tcp_if_include', str(subnet),
                    '--mca', 'oob_tcp_if_include', str(subnet)]
            record['nodes'] = nodes
        mpi += ['-np', str(a.processes)]
        execute('mpi_nodes', mpi + ['./bin/mpi_probe'])
        cmd = mpi + ['./bin/bruteforce_mpi', 'search', '--cipher', 'fase2/grupo4/texto_cifrado.des',
            '--phrase', 'la busqueda distribuida termina cuando aparece la frase clave',
            '--lower', '0', '--upper', str(a.upper), '--strategy', 'block', '--mode', a.mode,
            '--padding', 'none', '--batch', '128', '--repeats', str(a.repeats), '--warmups', str(a.warmups),
            '--stats', str(folder/'ranks'), '--out', str(folder/'texto_recuperado.txt')]
        out = execute('search', cmd)
        rows = [json.loads(line) for line in out.splitlines() if line.startswith('{')]
        if len(rows) != a.repeats or any(r['found'] != 900000 for r in rows):
            raise ValueError('Resultados incompletos o llave distinta a la validada')
        text = (folder/'texto_recuperado.txt').read_bytes()
        if b'la busqueda distribuida termina cuando aparece la frase clave' not in text:
            raise ValueError('Frase ausente')
        record.update(ok=True, results=rows, plain_sha256=hashlib.sha256(text).hexdigest(), plain_bytes=len(text))
    except Exception as e:
        record['error'] = str(e)
    record['wall_s'] = time.monotonic() - started
    (folder/'evidencia.json').write_text(json.dumps(record, ensure_ascii=False, indent=2))
    print(json.dumps(record, ensure_ascii=False, indent=2))
    print(f'EVIDENCIA: {folder}', file=sys.stderr)
    return 0 if record['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
