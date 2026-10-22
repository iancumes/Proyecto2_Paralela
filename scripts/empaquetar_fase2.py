#!/usr/bin/env python3
"""Prepara el paquete de fuentes y evidencias para los companeros."""
from pathlib import Path
import hashlib
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
target = ROOT/'output/Proyecto2_Fase2_Para_Equipo.zip'
excluded = {'output/Proyecto2_DES_MPI_Completo.zip', 'output/Proyecto2_Fase2_Para_Equipo.zip',
            'output/Proyecto2_Fase2_Para_Equipo.sha256'}
names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode('utf-8').split('\0')
files = sorted({n for n in names if n and n not in excluded and (ROOT/n).is_file()})
with ZipFile(target, 'w', compression=ZIP_DEFLATED, compresslevel=6) as archive:
    for name in files:
        archive.write(ROOT/name, 'Proyecto2_Paralela/'+name)
    archive.writestr('Proyecto2_Paralela/LEEME_ENTREGA.txt',
        'Fase 2: leer fase2/GUIA_MAC_Y_CLUSTER.md y output/docx/Informe_Proyecto2_Fase2.docx.\n'
        'El ensayo virtual corresponde a una sola computadora; la prueba fisica se realiza con el equipo.\n'
        'Construir Docker desde las fuentes. Los binarios incluidos son Linux x86-64.\n')
with ZipFile(target) as archive:
    assert archive.testzip() is None
    assert archive.read('Proyecto2_Paralela/fase2/grupo4/texto_cifrado.des') == (ROOT/'fase2/grupo4/texto_cifrado.des').read_bytes()
digest = hashlib.sha256(target.read_bytes()).hexdigest()
target.with_suffix('.sha256').write_text(digest+'  '+target.name+'\n', encoding='utf-8')
print(f'{target}: {len(files)} archivos; {target.stat().st_size} bytes; ZIP verificado')
