#!/usr/bin/env python3
"""Ensayo reproducible con dos contenedores en una computadora, sin volumenes."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
import argparse
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'fase2/evidencias'
OUT.mkdir(parents=True, exist_ok=True)
COMPOSE = ['docker', 'compose', '-f', 'cluster/compose.local.yaml']


def run(args, data=None):
    p = subprocess.run(args, cwd=ROOT, capture_output=True,
                       input=data.encode('utf-8') if data is not None else None, timeout=1800)
    if p.returncode:
        raise RuntimeError(f'{args}: {p.stdout.decode(errors="replace")}\n{p.stderr.decode(errors="replace")}')
    return p.stdout.decode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only-rehearsal', action='store_true', help='Reanudar el ensayo entre nodos sin repetir las mediciones locales')
    args = parser.parse_args()
    run(COMPOSE+['up', '-d'])
    master = run(COMPOSE+['ps', '-q', 'master']).strip()
    worker = run(COMPOSE+['ps', '-q', 'worker']).strip()
    inventory = json.loads(run(['docker', 'inspect', master, worker]))
    network = next(iter(inventory[0]['NetworkSettings']['Networks']))
    master_ip, worker_ip = [v['NetworkSettings']['Networks'][network]['IPAddress'] for v in inventory]
    subnet = json.loads(run(['docker', 'network', 'inspect', network]))[0]['IPAM']['Config'][0]['Subnet']
    pub = run(['docker', 'exec', master, 'cat', '/root/.ssh/id_rsa.pub'])
    run(['docker', 'exec', '-i', worker, 'bash', '-c', 'cat >> /root/.ssh/authorized_keys; chmod 600 /root/.ssh/authorized_keys'], pub)
    hosts = f'{master_ip} slots=2 max_slots=2\n{worker_ip} slots=2 max_slots=2\n'
    run(['docker', 'exec', '-i', master, 'bash', '-c', 'cat > /opt/proyecto2/cluster_hosts'], hosts)
    preflight = run(['docker', 'exec', master, 'bash', 'cluster/preflight.sh', worker_ip])
    (OUT/'ensayo_preflight.log').write_text(preflight, encoding='utf-8')
    manifest = {'fecha_guatemala': datetime.now(timezone(timedelta(hours=-6))).isoformat(),
                'tipo': 'ensayo virtual en una sola computadora; no cluster fisico',
                'master': master_ip, 'worker': worker_ip, 'subnet': subnet,
                'cpus_por_contenedor': 2, 'hostfile': hosts,
                'image': inventory[0]['Image']}
    (OUT/'ensayo_entorno.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    # Medir secuencialmente; el mismo modo full usa el mismo millon de candidatos.
    cases = [('rehearsal', 4)] if args.only_rehearsal else [('local', 1), ('local', 4), ('rehearsal', 4)]
    for kind, count in cases:
        cmd = ['docker', 'exec', master, 'python3', 'cluster/run_experiment.py',
               '--kind', kind, '--processes', str(count), '--mode', 'full']
        if kind != 'local':
            cmd += ['--hostfile', 'cluster_hosts', '--subnet', subnet]
        print(f'Iniciando {kind} con {count} procesos', flush=True)
        output = run(cmd)
        (OUT/f'ensayo_{kind}_p{count}.log').write_text(output, encoding='utf-8')
        print(f'Completado {kind} p{count}', flush=True)
        run(['docker', 'cp', f'{master}:/opt/proyecto2/fase2/resultados', str(ROOT/'fase2')])
    print('Ensayo finalizado; los contenedores quedan disponibles para inspeccion.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        (OUT/'ensayo_error.log').write_text(str(exc), encoding='utf-8')
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
