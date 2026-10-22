#!/usr/bin/env python3
"""Genera diagramas editables DOT, SVG y PNG para el informe."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'figures'
OUT.mkdir(exist_ok=True)
STYLE = '''graph [bgcolor="white", pad="0.22", nodesep="0.26", ranksep="0.28", fontname="Arial"];
node [shape=box, style="rounded,filled", fillcolor="#edf5f8", color="#2c6779", fontname="Arial", fontsize=12, margin="0.16,0.10"];
edge [color="#416778", fontname="Arial", fontsize=10, arrowsize=0.7];'''
GRAPHS = {
'des': r'''
digraph DES { rankdir=TB;
start [label="Bloque de entrada: 64 bits", fillcolor="#cdece8"];
ip [label="Permutación inicial IP\nL_0 (32 bits) | R_0 (32 bits)"];
round [label="Ronda i = 1,...,16\nL_i = R_(i-1)\nR_i = L_(i-1) XOR f(R_(i-1), K_i)"];
swap [label="Pre-salida: R_16 | L_16\nIntercambio final de mitades"];
end [label="Permutación inversa IP^-1\nBloque de salida: 64 bits", fillcolor="#cdece8"];
key [label="Llave: 64 bits\n56 datos + 8 de paridad", fillcolor="#fff1d8"];
pc1 [label="PC-1: 64 a 56 bits\nC_0 (28) | D_0 (28)", fillcolor="#fff1d8"];
rot [label="Rotaciones circulares a la izquierda\n1 bit: rondas 1, 2, 9 y 16\n2 bits: las demás rondas", fillcolor="#fff1d8"];
pc2 [label="PC-2: 56 a 48 bits\nSubllaves K_1,...,K_16", fillcolor="#fff1d8"];
f [label="Detalle de f(R,K)\nE: 32 a 48 bits -> XOR con K\n8 cajas S: 8 x (6 a 4 bits)\nP: permutación de 32 bits", fillcolor="#e8edf8"];
start -> ip -> round -> swap -> end;
key -> pc1 -> rot -> pc2;
pc2 -> round [label="Cifrar: K_1 a K_16\nDescifrar: K_16 a K_1"];
round -> f [style=dashed, arrowhead=none];
{rank=same; start; key;} {rank=same; round; pc2;}
}
''',
'crypt': r'''
digraph Crypt {rankdir=TB;
in [label="encrypt(key, buffer, len)\no decrypt(key, buffer, len)", fillcolor="#cdece8"];
valid [label="Comprobar key < 2^56\ny len múltiplo de 8"];
map [label="Dividir el índice en 8 grupos de 7 bits\nColocar datos en bits 7..1 de cada byte"];
parity [label="DES_set_odd_parity\nAjustar el bit 0 de cada byte"];
schedule [label="DES_set_key_unchecked\nConstruir las 16 subllaves una sola vez"];
block [label="Para pos = 0, 8, 16,..., len-8\nCopiar 8 bytes al bloque de entrada"];
des [label="DES_ecb_encrypt(input, output, schedule, mode)\nmode = DES_ENCRYPT o DES_DECRYPT"];
save [label="Copiar bloque resultante a buffer + pos"];
more [shape=diamond, label="¿Quedan bloques?", fillcolor="#fff1d8"];
end [label="buffer transformado en el mismo espacio\nSe procesaron exactamente len bytes", fillcolor="#cdece8"];
in -> valid -> map -> parity -> schedule -> block -> des -> save -> more;
more -> block [label="Sí"]; more -> end [label="No"];
}
''',
'trykey': r'''
digraph Try {rankdir=TB;
orig [label="ORIGINAL: tryKey(key, ciph, len)", fillcolor="#fff1d8"];
o1 [label="Reservar char temp[len+1] en la pila"];
o2 [label="memcpy(temp, ciph, len)\nConservar intacto el criptograma original"];
o3 [label="temp[len] = 0\nAgregar terminador de cadena"];
o4 [label="decrypt(key, temp, len)\nEl original SOLO transforma 16 bytes", fillcolor="#ffe7df"];
o5 [label="strstr(temp, search) != NULL\nDevolver 1 si encuentra la frase, 0 si no"];
new [label="CORREGIDO: scratch reutilizable de len+1 bytes", fillcolor="#cdece8"];
n1 [label="Copiar len bytes del criptograma a scratch"];
n2 [label="Descifrar TODOS los bloques con el candidato"];
n3 [shape=diamond, label="¿PKCS#7 válido?", fillcolor="#fff1d8"];
n4 [label="scratch[plain_len] = 0\nBuscar phrase con strstr"];
n5 [label="Devolver si hay coincidencia\nEl ciphertext compartido no cambia"];
reject [label="Devolver 0", fillcolor="#ffe7df"];
orig -> o1 -> o2 -> o3 -> o4 -> o5;
new -> n1 -> n2 -> n3;
n3 -> reject [label="No"]; n3 -> n4 [label="Sí"]; n4 -> n5;
{rank=same; orig; new;}
}
''',
'memcpy': r'''
digraph Copy {rankdir=TB;
call [label="memcpy(destino, origen, 8)", fillcolor="#cdece8"];
src [shape=box, label="origen (cipher)\nA1  00  C3  7F  10  E5  08  2A"];
copy [label="Copiar 8 BYTES\nEl byte 00 también se copia\nLa función no interpreta texto ni descifra"];
dst [shape=box, label="destino (temp), capacidad 9\nA1  00  C3  7F  10  E5  08  2A  ??"];
term [shape=box, label="Después de temp[8] = 0\nA1  00  C3  7F  10  E5  08  2A  00", fillcolor="#fff1d8"];
call -> src -> copy -> dst -> term;
}
''',
'strstr': r'''
digraph Substring {rankdir=TB;
start [label="strstr(texto, frase)\nEntradas terminadas en NUL", fillcolor="#cdece8"];
scan [label="Considerar posiciones del texto\nantes del primer byte NUL"];
compare [shape=diamond, label="¿Coinciden todos\nlos bytes de frase?", fillcolor="#fff1d8"];
yes [label="Sí: devolver puntero a la primera coincidencia\ntryKey interpreta puntero != NULL como 1", fillcolor="#cdece8"];
more [shape=diamond, label="¿Quedan posiciones?", fillcolor="#fff1d8"];
no [label="No: devolver NULL\ntryKey devuelve 0", fillcolor="#ffe7df"];
start -> scan -> compare;
compare -> yes [label="Sí"]; compare -> more [label="No"];
more -> scan [label="Sí"]; more -> no [label="No"];
}
''',
'mpi': r'''
digraph MPI {rankdir=TB;
init [label="Todos: MPI_Init; obtener rank y P", fillcolor="#cdece8"];
root [label="Rank 0: leer archivo cifrado\nMPI_Bcast: longitud y bytes a todos"];
split [label="Cada rank calcula su inicio, cantidad y stride\nReservar buffer temporal local"];
barrier [label="MPI_Barrier\nt0 = MPI_Wtime()"];
work [label="Probar hasta B = 128 candidatos locales\ntryKey copia, descifra y busca la frase"];
reduce [label="MPI_Allreduce(MPI_MIN)\nCompartir llave candidata o UINT64_MAX"];
found [shape=diamond, label="¿early y llave hallada,\no trabajo agotado?", fillcolor="#fff1d8"];
measure [label="Duración local = MPI_Wtime() - t0\nMPI_Reduce(MPI_MAX): tiempo de búsqueda"];
out [label="Reunir intentos y tiempos de cada proceso\nRank 0: validar, escribir resultado y JSON\nMPI_Finalize", fillcolor="#cdece8"];
init -> root -> split -> barrier -> work -> reduce -> found;
found -> work [label="No; también ranks sin trabajo\nparticipan en el colectivo"];
found -> measure [label="Sí"]; measure -> out;
}
'''
}
for name, body in GRAPHS.items():
    text = body.replace('{rankdir=', '{' + STYLE + '\nrankdir=', 1)
    if name == 'des':
        text = body.replace('{ rankdir=', '{' + STYLE + '\nrankdir=', 1)
    path = OUT / f'{name}.dot'
    path.write_text(text)
    for fmt in ['svg', 'png']:
        subprocess.run(['dot', f'-T{fmt}', '-Gdpi=180', str(path), '-o', str(OUT / f'{name}.{fmt}')], check=True)
print('6 diagramas generados en DOT, SVG y PNG.')
