#!/usr/bin/env python3
"""Promedios, desviaciones muestrales y graficas a partir de datos reales."""
from pathlib import Path
import csv
import json
import statistics as st
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'
FIGURES = ROOT / 'figures'
rows = [json.loads(line) for line in (RESULTS / 'raw.jsonl').read_text().splitlines()]
assert len(rows) == 180, f'Experimento incompleto: {len(rows)}/180'
groups = defaultdict(list)
for row in rows:
    groups[(row['key'], row['processes'], row['strategy'], row['mode'])].append(row)
summary = []
for (key, p, strategy, mode), samples in sorted(groups.items()):
    times = [x['seconds'] for x in samples]
    assert len(times) == 5
    attempts = [x['attempts'] for x in samples]
    baseline = st.mean(x['seconds'] for x in groups[(key, 1, strategy, mode)])
    mean = st.mean(times)
    summary.append(dict(key=key, processes=p, strategy=strategy, mode=mode,
        n=5, mean_s=mean, sd_s=st.stdev(times), cv_percent=100*st.stdev(times)/mean,
        min_s=min(times), max_s=max(times), speedup=baseline/mean,
        efficiency_percent=100*baseline/(p*mean), mean_attempts=st.mean(attempts),
        min_attempts=min(attempts), max_attempts=max(attempts),
        throughput_keys_s=st.mean(attempts)/mean, winner=samples[0]['winner']))
with open(RESULTS / 'summary.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=list(summary[0]))
    writer.writeheader(); writer.writerows(summary)
(RESULTS / 'summary.json').write_text(json.dumps(summary, indent=2))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
    'axes.spines.right':False,'axes.labelcolor':'#263d4b','text.color':'#263d4b',
    'axes.titleweight':'bold','figure.facecolor':'white','axes.facecolor':'white'})
keys = [8192,135168,249856]
colors = ['#008577','#b87921','#445caa']
def get(key,p,strategy,mode):
    return next(r for r in summary if (r['key'],r['processes'],r['strategy'],r['mode'])==(key,p,strategy,mode))
def save(fig,name):
    fig.savefig(FIGURES / f'{name}.png', dpi=200, bbox_inches='tight')
    fig.savefig(FIGURES / f'{name}.svg', bbox_inches='tight')
    plt.close(fig)

fig,axes = plt.subplots(1,2,figsize=(10,3.5))
for ax,strategy,title in zip(axes,['block','cyclic'],['Intervalos contiguos','Distribución cíclica']):
    for key,color in zip(keys,colors):
        values=[get(key,p,strategy,'early') for p in [1,2,4,8]]
        ax.errorbar([1,2,4,8],[r['mean_s'] for r in values],yerr=[r['sd_s'] for r in values],
                    marker='o',capsize=3,label=f'K = {key:,}',color=color)
    ax.set_xticks([1,2,4,8]); ax.set_xlabel('Procesos MPI'); ax.set_title(title)
    ax.grid(axis='y',alpha=.18)
axes[0].set_ylabel('Tiempo medio de búsqueda (s)')
axes[1].legend(fontsize=9)
fig.tight_layout(); save(fig,'early_times')

fig,axes = plt.subplots(1,2,figsize=(10,3.5))
for ax,strategy,title in zip(axes,['block','cyclic'],['Intervalos: speedup aparente','Cíclica: speedup aparente']):
    for key,color in zip(keys,colors):
        ax.plot([1,2,4,8],[get(key,p,strategy,'early')['speedup'] for p in [1,2,4,8]],
                marker='o',label=f'K = {key:,}',color=color)
    ax.plot([1,2,4,8],[1,2,4,8],linestyle='--',color='#888888',label='S = P')
    ax.set_xticks([1,2,4,8]); ax.set_xlabel('Procesos MPI'); ax.set_title(title)
    ax.grid(axis='y',alpha=.18)
axes[0].set_ylabel('S = media T1 / media TP'); axes[1].legend(fontsize=8)
fig.tight_layout(); save(fig,'early_speedups')

fig,axes = plt.subplots(1,2,figsize=(10,3.5))
for key,color in zip(keys,colors):
    values=[get(key,p,'block','full') for p in [1,2,4,8]]
    axes[0].errorbar([1,2,4,8],[r['mean_s'] for r in values],yerr=[r['sd_s'] for r in values],
                     marker='o',capsize=3,label=f'K = {key:,}',color=color)
    axes[1].plot([1,2,4,8],[r['speedup'] for r in values],marker='o',label=f'K = {key:,}',color=color)
axes[0].set_ylabel('Tiempo medio (s)'); axes[0].set_title('Trabajo fijo: 262 144 candidatos')
axes[1].plot([1,2,4,8],[1,2,4,8],linestyle='--',color='#888888',label='S = P')
axes[1].set_ylabel('Speedup'); axes[1].set_title('Escalamiento con trabajo constante')
for ax in axes:
    ax.set_xticks([1,2,4,8]);ax.set_xlabel('Procesos MPI');ax.grid(axis='y',alpha=.18)
axes[1].legend(fontsize=8);fig.tight_layout();save(fig,'full_scaling')

case = 'k249856_p8_block_full'
rank_rows=list(csv.DictReader(open(RESULTS / f'{case}_ranks.csv')))
fig,ax=plt.subplots(figsize=(9,3.2))
xs=np.arange(8)
compute=[st.mean(float(r['compute_s']) for r in rank_rows if int(r['rank'])==p) for p in xs]
sync=[st.mean(float(r['sync_s']) for r in rank_rows if int(r['rank'])==p) for p in xs]
ax.bar(xs,compute,color='#008577',label='Cálculo medido')
ax.bar(xs,sync,bottom=compute,color='#dba64f',label='Allreduce: comunicación y espera')
ax.set_xlabel('Rank');ax.set_ylabel('Segundos medios por proceso');ax.set_xticks(xs)
ax.legend(fontsize=9,loc='upper center',ncol=2,bbox_to_anchor=(.5,1.2))
fig.tight_layout();save(fig,'rank_times')

fig,axes=plt.subplots(2,1,figsize=(9,3.8))
for ax,p in zip(axes,[2,4]):
    width=262144//p
    for r in range(p):
        ax.broken_barh([(r*width,width)],(0,1),facecolors=['#c9e8e3','#dfe5f6','#ffe5b3','#d9e9f5'][r],edgecolor='white')
        ax.text(r*width+width/2,.5,f'rank {r}',ha='center',va='center',fontsize=9)
    for key in keys:
        ax.axvline(key,color='#ad403a',ymax=.9,linewidth=1.5)
        ax.annotate(f'{key:,}',(key,1),xytext=(0,8),textcoords='offset points',ha='center',fontsize=9)
    ax.set_xlim(0,262144);ax.set_ylim(0,1.45);ax.set_yticks([]);ax.set_title(f'P = {p}',loc='left',fontsize=10)
    ax.set_xticks([0,65536,131072,196608,262144]);ax.ticklabel_format(axis='x',style='plain')
axes[1].set_xlabel('Índice de llave en el intervalo [0, 262144)')
fig.tight_layout();save(fig,'partition')
print('36 resúmenes y 6 gráficas generados; 180 mediciones verificadas.')
