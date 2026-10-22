#!/usr/bin/env python3
"""Demostracion favorable de la llave original al inicio de un intervalo."""
from pathlib import Path
import subprocess
import json
import os

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
binary=str(ROOT/'bin/bruteforce_mpi')
key=1<<54
p=subprocess.run([binary,'encrypt','--text','data/texto.txt','--key',str(key),'--out','data/key_original_2pow54.des'],capture_output=True,text=True,check=True)
(ROOT/'results/encrypt_full56.log').write_text(p.stdout)
args=['mpirun','--bind-to','none','-np','4',binary,'search','--cipher','data/key_original_2pow54.des',
    '--phrase','ciencia con paciencia','--strategy','block','--batch','128','--repeats','5','--warmups','1',
    '--stats','results/full56_demo','--out','data/recovered_full56.txt']
p=subprocess.run(args,capture_output=True,text=True,check=True,timeout=45)
rows=[json.loads(x) for x in p.stdout.splitlines() if x.startswith('{')]
assert len(rows)==5 and all(r['found']==key and r['winner']==1 and r['upper']==1<<56 for r in rows)
assert Path('data/recovered_full56.txt').read_bytes()==Path('data/texto.txt').read_bytes()
Path('results/full56_demo.jsonl').write_text(p.stdout)
Path('results/full56_command.json').write_text(json.dumps(args,indent=2))
print(p.stdout,end='')
