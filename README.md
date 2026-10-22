# Proyecto 2: DES y búsqueda con MPI

Para ejecutar el proyecto en Windows mediante Ubuntu/WSL, consultar la
[guía paso a paso](GUIA_EJECUCION.md). La primera compilación y las pruebas
realizadas en ese entorno están documentadas en
[validación local](pruebas_usuario/VALIDACION_LOCAL.md).
Se incluye en `bin/bruteforce_mpi` el ejecutable Linux x86-64 validado en WSL.
Para recompilarlo en el entorno de destino, usar `make -B OPENSSL_PREFIX=/usr`
en Ubuntu; en macOS, usar `make -B` con las dependencias instaladas.

El informe está en `output/pdf/Informe_Proyecto2_DES_MPI.pdf`. La fuente de lectura
editable está en `informe_fuente.md`; se genera desde `scripts/build_report.py`.
El archivo original permanece intacto en `original/bruteforce_.c`.

## Compilar y ejecutar

Requiere compilador C11, Open MPI y cabeceras/biblioteca de OpenSSL con API DES.
En el entorno usado ya estaban instalados. El Makefile detecta Homebrew en macOS.
En Linux se puede usar `make OPENSSL_PREFIX=/usr`.

```sh
make
bin/bruteforce_mpi selftest
bin/bruteforce_mpi encrypt --text data/texto.txt --key 135168 --out data/key_135168.des
mpirun --bind-to none -np 4 bin/bruteforce_mpi search \
  --cipher data/key_135168.des --phrase 'ciencia con paciencia' \
  --upper 262144 --strategy block --batch 128 \
  --out data/recuperado.txt
cmp data/texto.txt data/recuperado.txt
make test
```

`--upper` es exclusivo. `search` no recibe la llave verdadera. Sin `--upper`, el
espacio es `[0, 2^56)`. Una búsqueda completa arbitraria no es práctica aquí.
`--lower` permite ventanas; se probaron llaves próximas a `2^54` y a `2^56-1`.
`--strategy cyclic` reparte candidatos intercalados entre procesos.
`--mode full` mantiene el recorrido aun después de encontrar la llave.
`--stats PREFIJO` guarda un CSV con intentos, cálculo y tiempo de Allreduce por rank.
Sin coincidencia se devuelve código de salida 2; los errores de entrada devuelven 1.

La llave numérica es un índice de 56 bits. Se divide de mayor a menor en ocho
grupos de siete bits y se agrega un bit de paridad impar a cada byte. No utiliza
la conversión defectuosa y dependiente de arquitectura del original.
El texto se cifra completamente con DES-ECB y PKCS#7. DES es el objeto del
ejercicio; sus funciones de bajo nivel están obsoletas en OpenSSL 3.

## Reproducir los resultados

Los datos actuales son mediciones reales de este equipo. Estos comandos
**sobrescriben los datos derivados y las mediciones**; guardar una copia si se
quiere conservar el experimento entregado. Ejecutar los benchmarks por separado,
sin otras mediciones simultáneas.

```sh
python3 scripts/benchmark.py
python3 scripts/demo_full56.py
python3 scripts/make_diagrams.py
python3 scripts/analyze.py
python3 scripts/build_report.py
```

Los scripts de pruebas/benchmark solo requieren la biblioteca estándar de Python.
Los diagramas necesitan Graphviz (`dot`). El análisis necesita matplotlib y numpy.
El PDF necesita reportlab y Pillow; su script usa Arial de macOS. En otro sistema,
ajustar las rutas de fuentes al inicio de `scripts/build_report.py`.

La matriz principal tiene 36 casos con cinco repeticiones medidas y un
calentamiento descartado por caso: **180 mediciones + 36 calentamientos**.
Además se ejecutó una demostración favorable de 56 bits, con cinco mediciones y
un calentamiento, para la llave del archivo original.

El tiempo es el máximo de duraciones locales con MPI_Wtime después de una
barrera; incluye el descifrado completo de cada candidato y los Allreduce.
Excluye arranque, lectura, cifrado, escritura y reunión final de estadísticas.

## Archivos principales

| Ruta | Contenido |
| --- | --- |
| `src/bruteforce_mpi.c` | Cifrado, descifrado, prueba de llave y búsqueda MPI |
| `data/texto.txt` | Mensaje original de exactamente 350 palabras |
| `data/key_*.des` | Criptogramas binarios completos |
| `data/recovered_*.txt` | Mensajes recuperados y verificados |
| `results/raw.jsonl` | Las 180 mediciones sin redondear |
| `results/summary.csv` | Medias, sd muestral, speedup, eficiencia e intentos |
| `results/*_ranks.csv` | Cinco repeticiones de estadísticas por proceso |
| `results/metadata.json` | Equipo, herramientas, protocolo y hashes |
| `results/commands.jsonl` | Argumentos exactos de cada configuración |
| `results/original_compile.log` | Error real de compilación del archivo base |
| `tests/verify.py` | Pruebas de corrección y terminación |
| `figures/*.dot`, `*.svg` | Diagramas y gráficas editables |
| `scripts/build_report.py` | Fuente que vuelve a generar PDF y Markdown |

## Completar la portada

Los nombres y carnés no se inventaron. Para incorporarlos, crear
`data/equipo.json` con este formato y volver a generar el informe:

```json
[
  {"nombre": "Nombre del integrante 1", "carne": "Carné 1"},
  {"nombre": "Nombre del integrante 2", "carne": "Carné 2"},
  {"nombre": "Nombre del integrante 3", "carne": "Carné 3"}
]
```

El informe cubre las siete tareas y distingue resultados observados de
extrapolaciones. Los experimentos se ejecutaron en una sola máquina con MPI;
no se afirma haber medido un clúster de varias computadoras.
