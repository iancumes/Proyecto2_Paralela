#!/usr/bin/env python3
"""Resume evidencias reales, sin sustituir el ensayo virtual por un cluster fisico."""
from pathlib import Path
import json
import statistics as st
import csv

ROOT = Path(__file__).resolve().parents[1]
rows = []
for f in sorted((ROOT/'fase2/resultados').glob('*/evidencia.json')):
    record = json.loads(f.read_text(encoding='utf-8'))
    if not record.get('ok'):
        continue
    values = [x['seconds'] for x in record['results']]
    rows.append({'kind': record['kind'], 'processes': record['config']['processes'],
                 'mode': record['config']['mode'], 'upper': record['config']['upper'],
                 'n': len(values), 'mean_s': st.mean(values),
                 'sd_s': st.stdev(values) if len(values)>1 else 0,
                 'attempts': [x['attempts'] for x in record['results']],
                 'found': [x['found'] for x in record['results']],
                 'sha256_plain': record['plain_sha256'],
                 'evidence': str(f.relative_to(ROOT))})
baseline = next((r for r in rows if r['kind']=='local' and r['processes']==1 and r['mode']=='full'), None)
for row in rows:
    if baseline and row['mode']==baseline['mode'] and row['upper']==baseline['upper']:
        row['speedup'] = baseline['mean_s']/row['mean_s']
        row['efficiency_percent'] = 100*row['speedup']/row['processes']
summary = {'nota': 'Todas las mediciones Docker actuales pertenecen a una sola computadora; no son resultados de red fisica.',
           'docker_cpus_por_contenedor_en_ensayo': 2, 'rows': rows,
           'cluster_fisico_ejecutado': False}
out = ROOT/'fase2/resultados'
out.mkdir(exist_ok=True)
(out/'resumen.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
fields = ['kind','processes','mode','upper','n','mean_s','sd_s','speedup','efficiency_percent','evidence']
with (out/'resumen.csv').open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
    writer.writeheader(); writer.writerows(rows)
print(json.dumps(summary, indent=2, ensure_ascii=False))
