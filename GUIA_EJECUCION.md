# Guía del Proyecto 2: DES y búsqueda paralela con MPI

## 1. Ubicación

El proyecto está dentro de dos carpetas llamadas `Proyecto2`.

En Windows:

```text
C:\Users\ianro\OneDrive\Documentos\Uvg\Octavo Semestre\Paralela\Proyecto2\Proyecto2
```

En Ubuntu mediante WSL:

```text
/mnt/c/Users/ianro/OneDrive/Documentos/Uvg/Octavo Semestre/Paralela/Proyecto2/Proyecto2
```

Todos los comandos Bash de esta guía se ejecutan desde esa carpeta.

## 2. ¿Qué hace el proyecto?

El programa cifra un texto con DES y utiliza fuerza bruta paralela con MPI para encontrar la llave con la que se cifró.

```text
Texto original + llave elegida
              ↓
         Cifrado DES
              ↓
       Archivo cifrado
              ↓
Varios procesos prueban distintas llaves
              ↓
Un descifrado contiene la frase conocida
              ↓
       Texto recuperado
```

DES es simétrico: la misma llave sirve para cifrar y descifrar. Trabaja con bloques de 8 bytes y llaves con 56 bits efectivos. El programa utiliza DES-ECB y relleno PKCS#7. DES se usa aquí como ejercicio académico.

La búsqueda recibe el criptograma y una frase conocida del texto, **sin recibir la llave verdadera**. Una coincidencia se reconoce comprobando el relleno y buscando la frase exacta; la comparación final con el original confirma la recuperación completa.

| Comando | Función |
| --- | --- |
| `selftest` | Comprueba DES y el relleno. |
| `encrypt` | Cifra un archivo con una llave indicada. |
| `search` | Busca la llave mediante candidatos distribuidos con MPI. |

## 3. ¿Qué se implementó?

El original está conservado en `original/bruteforce_.c`. La implementación actual es `src/bruteforce_mpi.c`.

- Cifrado y descifrado del mensaje completo: el original procesaba solamente 16 bytes.
- Relleno PKCS#7 para completar múltiplos de 8 bytes y validación al descifrar.
- Conversión del índice de 56 bits a los ocho bytes DES con paridad impar, sin depender de la arquitectura.
- Lectura y escritura de archivos, conservando el criptograma como bytes binarios.
- Repartición de candidatos sin omitir llaves en los límites.
- Coordinación colectiva para comunicar coincidencias y detenerse.
- Terminación cuando no hay solución dentro del rango.
- Mediciones con `MPI_Wtime`, conteo de intentos y estadísticas por proceso.
- Pruebas automáticas de corrección y terminación.

Los experimentos entregados incluyen 36 configuraciones con cinco repeticiones medidas: 180 mediciones, además de calentamientos. Esas mediciones se generaron en un Apple M1 Pro y no representan el rendimiento de esta computadora Windows.

## 4. Funcionamiento de MPI

Cada proceso tiene un identificador llamado **rank**, comenzando en cero. El rank 0 lee el criptograma y lo comparte usando `MPI_Bcast`. Cada proceso mantiene sus propios búferes y prueba diferentes llaves.

### Repartición por bloques: `block`

Con cuatro procesos y el rango `[0, 262144)`:

| Rank | Llaves asignadas |
| --- | --- |
| 0 | 0 a 65535 |
| 1 | 65536 a 131071 |
| 2 | 131072 a 196607 |
| 3 | 196608 a 262143 |

### Repartición cíclica: `cyclic`

Con cuatro procesos, el rank 0 prueba `0, 4, 8...`; el rank 1 prueba `1, 5, 9...`; el rank 2 prueba `2, 6, 10...`; y el rank 3 prueba `3, 7, 11...`.

### Prueba de cada llave y coordinación

La función `tryKey` copia el criptograma, descifra todo el mensaje, valida el relleno y busca la frase con `strstr`.

Después de cada lote, `MPI_Allreduce` comunica la menor llave coincidente reportada. En modo `early` todos se detienen cuando se comunica una coincidencia; en modo `full` se recorre todo el rango. Incluso los procesos sin candidatos participan en la coordinación.

## 5. Abrir Ubuntu y compilar

Desde **PowerShell**:

```powershell
wsl -d Ubuntu-24.04
```

A partir de aquí usa **Bash dentro de Ubuntu**:

```bash
cd "/mnt/c/Users/ianro/OneDrive/Documentos/Uvg/Octavo Semestre/Paralela/Proyecto2/Proyecto2"
pwd
ls
```

Las herramientas necesarias son un compilador C, Open MPI, Make, Python 3 y las cabeceras de OpenSSL. En esta distribución se verificó su presencia. Si preparas otra instalación de Ubuntu, puedes instalarlas con:

```bash
sudo apt update
sudo apt install build-essential openmpi-bin libopenmpi-dev libssl-dev python3
```

Compila:

```bash
make -B OPENSSL_PREFIX=/usr
```

`-B` fuerza la compilación. Es necesario en la primera ejecución porque el ejecutable incluido originalmente era de macOS ARM64. El nuevo ejecutable Linux queda en `bin/bruteforce_mpi`.

## 6. Comprobar DES

```bash
./bin/bruteforce_mpi selftest
```

Salida esperada:

```text
SELFTEST OK: vector DES y 34 longitudes PKCS#7
```

## 7. Cifrar el texto

Usa una carpeta independiente para conservar los resultados entregados:

```bash
mkdir -p pruebas_usuario
./bin/bruteforce_mpi encrypt \
  --text data/texto.txt \
  --key 135168 \
  --out pruebas_usuario/cifrado.des
```

Debe aparecer `ENCRYPT OK`. `--text` es la entrada, `--key` es el índice de llave elegido y `--out` es el criptograma binario de salida.

## 8. Buscar la llave con cuatro procesos

```bash
mpirun --bind-to none -np 4 ./bin/bruteforce_mpi search \
  --cipher pruebas_usuario/cifrado.des \
  --phrase "ciencia con paciencia" \
  --lower 0 \
  --upper 262144 \
  --strategy block \
  --mode early \
  --batch 128 \
  --stats pruebas_usuario/busqueda_block \
  --out pruebas_usuario/recuperado.txt
```

| Opción | Significado |
| --- | --- |
| `-np 4` | Cuatro procesos MPI. |
| `--bind-to none` | Desactiva la fijación de procesos a núcleos. |
| `--cipher` | Criptograma que se intentará descifrar. |
| `--phrase` | Frase exacta que debe aparecer en el mensaje. |
| `--lower 0` | Primera llave incluida. |
| `--upper 262144` | Límite superior exclusivo: la última llave es 262143. |
| `--strategy block` | Intervalos continuos por proceso. |
| `--mode early` | Detención al comunicar una coincidencia. |
| `--batch 128` | Hasta 128 candidatos por proceso antes de coordinarse. |
| `--stats` | Prefijo para generar un CSV por rank. |
| `--out` | Archivo del texto recuperado. |

La salida JSON debe incluir `"found":135168`, `"processes":4` y `"winner":2`. El rank 2 contiene esa llave en la distribución por bloques. El tiempo depende del equipo.

Otros campos son `seconds` (duración de búsqueda), `attempts` (total de candidatos probados) y `trial` (número de repetición, comenzando en cero).

## 9. Validar la recuperación

```bash
cmp data/texto.txt pruebas_usuario/recuperado.txt \
  && echo "OK: el texto recuperado es idéntico al original"
cat pruebas_usuario/recuperado.txt
head pruebas_usuario/busqueda_block_ranks.csv
```

`cmp` compara byte por byte. Si no hay diferencias, no imprime nada y permite ejecutar el mensaje `OK`.

El archivo recuperado se encuentra en Windows en:

```text
C:\Users\ianro\OneDrive\Documentos\Uvg\Octavo Semestre\Paralela\Proyecto2\Proyecto2\pruebas_usuario\recuperado.txt
```

## 10. Probar la estrategia cíclica

```bash
mpirun --bind-to none -np 4 ./bin/bruteforce_mpi search \
  --cipher pruebas_usuario/cifrado.des \
  --phrase "ciencia con paciencia" \
  --upper 262144 \
  --strategy cyclic \
  --batch 128 \
  --out pruebas_usuario/recuperado_cyclic.txt
cmp data/texto.txt pruebas_usuario/recuperado_cyclic.txt \
  && echo "OK: recuperación con cyclic"
```

Debe encontrar la misma llave. Puede cambiar el rank ganador por la repartición intercalada.

## 11. Comparar uno y cuatro procesos

Usa `full` para que ambas configuraciones prueben exactamente 262144 candidatos. Se ejecutan secuencialmente para evitar mediciones simultáneas.

```bash
for p in 1 4; do
  mpirun --bind-to none -np "$p" ./bin/bruteforce_mpi search \
    --cipher pruebas_usuario/cifrado.des \
    --phrase "ciencia con paciencia" \
    --upper 262144 \
    --strategy block \
    --mode full \
    --batch 128 \
    --warmups 1 \
    --repeats 5 \
    --stats "pruebas_usuario/comparacion_p${p}"
done
```

Cada configuración imprime cinco líneas medidas y descarta un calentamiento. Todas deben indicar `"attempts":262144` y `"found":135168`.

La aceleración es el tiempo promedio con un proceso dividido entre el promedio con varios procesos. La eficiencia es esa aceleración dividida entre el número de procesos; multiplicada por 100 da el porcentaje.

El tiempo reportado es el máximo de las duraciones locales, después de una barrera. Incluye el descifrado de candidatos y la coordinación de los lotes. Excluye arranque, lectura, escritura y reunión final de estadísticas.

## 12. Ejecutar las pruebas automáticas

```bash
make test OPENSSL_PREFIX=/usr
```

Salida final esperada:

```text
PASS: 22 comprobaciones; vector conocido, texto completo, limites, llaves grandes y sin coincidencia.
```

Las pruebas cubren cifrado y recuperación, ambas estrategias, rangos no divisibles entre procesos, más procesos que candidatos, ventanas próximas a `2^54` y `2^56`, ausencia de solución, criptogramas mal formados y el texto de 350 palabras. Usan archivos temporales.

## 13. Límites y problemas frecuentes

- **No ejecutar el binario de macOS en Linux:** recompila con `make -B OPENSSL_PREFIX=/usr`.
- **Archivo no encontrado:** comprueba `pwd` y entra a la carpeta interna `Proyecto2/Proyecto2`.
- **Faltan slots MPI:** agrega `--oversubscribe` después de `mpirun` para una prueba local. Esto permite ejecutar más procesos que slots disponibles, pero puede afectar el rendimiento.
- **No encuentra la llave:** comprueba que esté dentro de `[lower, upper)` y que la frase aparezca literalmente en el texto original.
- **Códigos de salida:** `0` indica éxito, `2` indica búsqueda sin coincidencia y `1` corresponde a errores de entrada o ejecución del programa. En Bash puedes consultar el código inmediatamente después de un comando con `echo $?`.
- **Rango completo:** sin `--upper`, se busca en `[0, 2^56)`. No es una prueba rápida general.
- **Demostración favorable de 56 bits:** `scripts/demo_full56.py` usa la llave `2^54`, que queda justo al inicio del intervalo del rank 1 con cuatro procesos. Su rapidez no demuestra que se haya recorrido todo el espacio.
- **Scripts de macOS:** `scripts/benchmark.py` consulta hardware mediante `sysctl` y `clang`; debe adaptarse antes de reproducir el experimento en Ubuntu. `scripts/build_report.py` usa rutas de fuentes de macOS y también requiere adaptación.
- **Resultados existentes:** los scripts de experimentación y generación pueden sobrescribir resultados y artefactos entregados. Las pruebas manuales de esta guía escriben en `pruebas_usuario`.

## 14. Archivos principales

| Ruta relativa a la raíz del proyecto | Contenido |
| --- | --- |
| `src/bruteforce_mpi.c` | Implementación actual. |
| `original/bruteforce_.c` | Código original conservado. |
| `Makefile` | Compilación y ejecución de pruebas. |
| `data/texto.txt` | Texto original de 350 palabras. |
| `tests/verify.py` | Pruebas automáticas. |
| `results/raw.jsonl` | Mediciones originales. |
| `results/summary.csv` | Resumen de tiempos y aceleración. |
| `results/metadata.json` | Equipo y protocolo de las mediciones originales. |
| `scripts/` | Experimentación, análisis y generación de informe. |
| `figures/` | Diagramas y gráficas. |
| `informe_fuente.md` | Informe en Markdown. |
| `output/pdf/Informe_Proyecto2_DES_MPI.pdf` | Informe completo en PDF. |

La validación local de la primera compilación se documenta por separado en `pruebas_usuario/VALIDACION_LOCAL.md`.
