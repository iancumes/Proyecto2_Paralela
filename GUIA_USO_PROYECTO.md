# Guía de uso y funcionamiento del Proyecto 2

Esta guía explica qué hace el proyecto, qué implementamos en sus dos fases y cómo compilarlo, ejecutar búsquedas y consultar sus evidencias. Incluye rutas para esta computadora Windows y comandos para trabajar con Docker. Para la preparación de los compañeros en Mac y la reunión del clúster, se complementa con [la guía Mac y clúster](fase2/GUIA_MAC_Y_CLUSTER.md).

Para ejecutar en pareja, abrir según el rol la [guía de comandos de la maestra](GUIA_COMANDOS_MAESTRA.md) o la [guía de comandos de la colaboradora](GUIA_COMANDOS_COLABORADORA.md). Ambas señalan los momentos de intercambio y la ubicación exacta de cada dato.

## 1 Qué hace el proyecto

El programa cifra un archivo de texto con DES y después intenta encontrar su llave probando candidatos en paralelo con MPI. Es un ejercicio académico de computación paralela y distribuida.

El flujo de uso es:

1. Preparar un texto y elegir una llave para cifrarlo.
2. Guardar el criptograma como un archivo binario.
3. Entregar a la búsqueda el criptograma y una frase conocida del texto.
4. Dividir las llaves candidatas entre procesos MPI.
5. Descifrar cada candidato y comprobar si aparece la frase.
6. Comunicar la coincidencia y guardar el mensaje recuperado.

**La búsqueda no recibe la llave real.** `--key` solo se utiliza al cifrar; el comando `search` rechaza ese argumento. En el grupo 4 ya conocemos la llave porque la encontramos durante las pruebas, pero no se la pasamos a la búsqueda.

DES es simétrico: la misma llave sirve para cifrar y descifrar. En este proyecto trabaja en modo ECB con bloques de 8 bytes. Las llaves se enumeran mediante índices de 56 bits; el programa transforma cada índice en ocho grupos de siete bits y añade paridad impar a cada byte.

## 2 Qué hicimos y qué falta

### Fase 1

Partimos de `original/bruteforce_.c` y construimos la implementación de `src/bruteforce_mpi.c`. Se corrigieron el cifrado de solo 16 bytes, la conversión de llaves, los límites de los rangos y la terminación cuando no hay coincidencia. Se añadió lectura y escritura binaria, relleno PKCS#7, reparto por bloques y cíclico, mediciones y pruebas automáticas.

El experimento original guardó 180 mediciones principales en un Apple M1 Pro. Después compilamos y verificamos el proyecto en Ubuntu/WSL de esta computadora Windows. Los resultados de ambos entornos se conservan por separado.

### Fase 2 individual

Preparamos nuestro archivo para intercambio y recibimos el criptograma del grupo 4. La primera prueba no encontró la frase: el rango no incluía su llave y se exigía un final PKCS#7 que su mensaje no tiene. Un diagnóstico posterior encontró la llave **900000**. Añadimos `--padding none`, recuperamos el mensaje y comprobamos que al volver a cifrarlo se reproducen exactamente los bytes recibidos.

También creamos y probamos la imagen Docker, SSH sin contraseña, identificación de nodos y un ensayo entre dos contenedores de la misma computadora. Registramos tiempos, hashes, logs y errores corregidos, incluido un hostfile con saltos CRLF de Windows que Open MPI rechazaba.

| Parte | Estado |
| --- | --- |
| Compilación y pruebas de corrección | Realizadas |
| Descifrado del grupo 4 y recifrado exacto | Realizados |
| Docker, MPI y SSH local | Probados |
| Ensayo con dos contenedores en esta PC | Realizado |
| Código e instrucciones para el clúster físico | Preparados |
| Ejecución entre computadoras mediante el router | Pendiente de la reunión |
| Capturas, tiempos físicos y confirmación del otro equipo | Pendientes |

Dos contenedores en una PC permiten comprobar el software y la coordinación; las mediciones de ese ensayo no representan tráfico entre computadoras por un router.

## 3 Dónde están los archivos

La raíz del proyecto en esta computadora es:

```text
C:\Users\ianro\OneDrive\Documentos\Uvg\Octavo Semestre\Paralela\Proyecto2\Proyecto2
```

La misma carpeta desde Ubuntu/WSL es:

```text
/mnt/c/Users/ianro/OneDrive/Documentos/Uvg/Octavo Semestre/Paralela/Proyecto2/Proyecto2
```

Dentro de la imagen Docker, el proyecto está en:

```text
/opt/proyecto2
```

Los ejemplos usan rutas relativas a la raíz que corresponda. Si se clona el repositorio en otra ubicación, usar esa nueva raíz; no hace falta reproducir la ruta personal de Windows.

| Archivo o carpeta | Para qué sirve |
| --- | --- |
| `src/bruteforce_mpi.c` | Programa principal DES y MPI |
| `src/mpi_probe.c` | Muestra rank, hostname e interfaces IPv4 |
| `src/diagnose_des.c` | Diagnóstico de interoperabilidad, separado de las mediciones MPI |
| `Makefile` | Compila el programa y `mpi_probe` |
| `data/texto.txt` | Nuestro texto original de 350 palabras |
| `fase2/grupo4/texto_cifrado.des` | Criptograma recibido del grupo 4 |
| `fase2/grupo4/texto_recuperado.txt` | Mensaje del grupo 4 ya recuperado |
| `fase2/grupo4/pruebas/` | Búsquedas locales numeradas y estadísticas |
| `fase2/resultados/` | Experimentos Docker y resumen de mediciones |
| `fase2/evidencias/` | Logs de construcción, SSH y entorno |
| `Dockerfile` y `cluster/` | Imagen, arranque SSH y ejecución entre nodos |
| `tests/` | Pruebas de corrección |
| `BITACORA.md` | Historial de acciones, resultados y pendientes |
| `output/docx/Informe_Proyecto2_Fase2.docx` | Reporte Word de fase 2 |

## 4 Empezar desde Windows con WSL

### Abrir la carpeta correcta

Desde **PowerShell**, entrar a Ubuntu:

```powershell
wsl -d Ubuntu-24.04
```

A partir de aquí, ejecutar estos comandos en **Bash dentro de Ubuntu**:

```bash
cd "/mnt/c/Users/ianro/OneDrive/Documentos/Uvg/Octavo Semestre/Paralela/Proyecto2/Proyecto2"
pwd
ls
```

Deben aparecer `Makefile`, `src`, `data`, `cluster` y `fase2`.

En esta computadora ya se verificaron las herramientas. Para una instalación nueva de Ubuntu, las dependencias del programa y sus pruebas son:

```bash
sudo apt update
sudo apt install build-essential openmpi-bin libopenmpi-dev libssl-dev python3
```

### Compilar y comprobar

```bash
make -B OPENSSL_PREFIX=/usr
./bin/bruteforce_mpi selftest
```

`-B` fuerza la recompilación para el entorno actual. El repositorio incluye binarios Linux x86-64; una Mac debe construirlos para su entorno o usar Docker siguiendo su guía.

Salida esperada del control DES:

```text
SELFTEST OK: vector DES y 34 longitudes PKCS#7
```

## 5 Cifrar y recuperar nuestro propio texto

Estos comandos se ejecutan en **Bash/Ubuntu desde la raíz**. Usan una carpeta de demostración para conservar los resultados anteriores.

```bash
mkdir -p pruebas_manual
./bin/bruteforce_mpi encrypt \
  --text data/texto.txt \
  --key 135168 \
  --out pruebas_manual/nuestro_cifrado.des
```

Debe aparecer `ENCRYPT OK`. Se utiliza PKCS#7 de forma predeterminada: siempre agrega entre uno y ocho bytes para completar bloques de ocho.

Buscar la llave con cuatro procesos:

```bash
mpirun --bind-to none -np 4 ./bin/bruteforce_mpi search \
  --cipher pruebas_manual/nuestro_cifrado.des \
  --phrase "ciencia con paciencia" \
  --lower 0 --upper 262144 \
  --strategy block --mode early --batch 128 \
  --stats pruebas_manual/nuestro_caso \
  --out pruebas_manual/nuestro_recuperado.txt
```

La salida debe incluir `"found":135168`. Para verificar la recuperación completa:

```bash
cmp data/texto.txt pruebas_manual/nuestro_recuperado.txt \
  && echo "OK: archivos identicos"
cat pruebas_manual/nuestro_recuperado.txt
```

Los archivos estarán en Windows dentro de la carpeta raíz indicada antes, subcarpeta `pruebas_manual`.

## 6 Ejecutar el caso del grupo 4

### Búsqueda directa

En **Bash/Ubuntu desde la raíz**:

```bash
mkdir -p pruebas_manual
mpirun --bind-to none -np 4 ./bin/bruteforce_mpi search \
  --cipher fase2/grupo4/texto_cifrado.des \
  --phrase "la busqueda distribuida termina cuando aparece la frase clave" \
  --lower 0 --upper 1048576 \
  --padding none --strategy block --mode early --batch 128 \
  --stats pruebas_manual/grupo4 \
  --out pruebas_manual/grupo4_recuperado.txt
```

Debe encontrar `"found":900000` y mostrar `"padding":"none"`. Para leer y comparar el mensaje con la recuperación ya validada:

```bash
cat pruebas_manual/grupo4_recuperado.txt
cmp fase2/grupo4/texto_recuperado.txt pruebas_manual/grupo4_recuperado.txt \
  && echo "OK: coincide con la recuperacion validada"
```

El mensaje tiene 2192 bytes UTF-8 y 355 palabras separadas por espacios. La longitud es múltiplo de ocho. `--padding none` significa que se conservan todos los bytes descifrados; no elimina espacios ni infiere otro relleno.

### Búsqueda con registro automático

Para guardar una nueva prueba numerada y añadir una entrada a la bitácora:

```bash
python3 scripts/validar_grupo4.py \
  --lower 0 --upper 1048576 --padding none --processes 4
```

Para tres mediciones y un calentamiento descartado:

```bash
python3 scripts/validar_grupo4.py \
  --processes 4 --repeats 3 --warmups 1
```

Se crean archivos `prueba_NNN.json`, stdout, stderr, CSV por rank y texto recuperado dentro de `fase2/grupo4/pruebas`. Los registros anteriores se conservan. El JSON identifica la ruta exacta usada en `--out`.

## 7 Cómo funciona la búsqueda por dentro

1. `MPI_Init` inicia el entorno y asigna un rank a cada proceso.
2. El rank 0 lee el criptograma y lo comparte mediante `MPI_Bcast`.
3. Se reparten los candidatos del intervalo `[lower, upper)`.
4. Cada proceso reserva su memoria y prueba sus llaves.
5. `tryKey` copia y descifra todo el criptograma, valida el relleno si se usa PKCS#7 y busca la frase con `strstr`.
6. Después de cada lote, `MPI_Allreduce` comunica las coincidencias.
7. Se reúnen tiempos e intentos; el rank 0 imprime JSON y, si se solicitó, guarda el texto.

Los procesos tienen memoria privada. MPI comunica datos y resultados entre ellos; no convierte el programa en un conjunto de hilos con memoria compartida.

### Reparto block y cyclic

Con `block`, cuatro procesos y `[0, 1048576)`, el reparto es:

| Rank | Primer candidato | Último candidato incluido |
| --- | --- | --- |
| 0 | 0 | 262143 |
| 1 | 262144 | 524287 |
| 2 | 524288 | 786431 |
| 3 | 786432 | 1048575 |

Con `cyclic`, el rank 0 prueba `0, 4, 8...`; el rank 1, `1, 5, 9...`; y así sucesivamente. Para probarlo, cambiar `--strategy block` por `--strategy cyclic` en una búsqueda.

### Modo early y full

- `early`: se detiene al comunicar una coincidencia. Es el predeterminado.
- `full`: recorre todo el intervalo, incluso después de encontrar una llave. Sirve para comparar un volumen fijo de candidatos.

`--batch 128` permite probar hasta 128 candidatos por proceso antes de coordinarse. Un lote pequeño aumenta la frecuencia de comunicación; uno grande puede aumentar el trabajo realizado antes de que todos se enteren del hallazgo.

El diagnóstico `diagnose_des.c` utiliza bloques conocidos de la frase y admite distintas representaciones para localizar problemas de interoperabilidad. No reemplaza las mediciones de `bruteforce_mpi`; sus tiempos se conservan por separado.

## 8 Referencia de opciones y resultados

| Opción | Significado |
| --- | --- |
| `--text ARCHIVO` | Texto de entrada para `encrypt` |
| `--key NUMERO` | Índice de llave para `encrypt`, no para `search` |
| `--cipher ARCHIVO` | Criptograma binario para `search` |
| `--phrase "TEXTO"` | Frase exacta que debe aparecer |
| `--lower N` | Primera llave incluida; predeterminado 0 |
| `--upper N` | Límite superior exclusivo |
| `--strategy block` o `cyclic` | Distribución entre procesos |
| `--mode early` o `full` | Condición de terminación |
| `--padding pkcs7` o `none` | Tratamiento del relleno; predeterminado PKCS#7 |
| `--batch N` | Tamaño de lote; predeterminado 128 |
| `--repeats N` | Número de repeticiones medidas |
| `--warmups N` | Calentamientos descartados |
| `--stats PREFIJO` | Genera `PREFIJO_ranks.csv` |
| `--out ARCHIVO` | Salida cifrada o texto recuperado, según el comando |

`-np N` pertenece a `mpirun` y establece cuántos procesos se lanzan. `--bind-to none` también pertenece a MPI y desactiva la fijación a núcleos.

El programa no crea las carpetas de salida de `--out` o `--stats`: crearlas antes con `mkdir -p`. Los archivos de una demostración se sobrescriben si se repite la misma ruta; los scripts de registro utilizan números o fechas para conservar el historial.

La búsqueda imprime una línea JSON por repetición medida. Sus campos principales son:

| Campo | Cómo leerlo |
| --- | --- |
| `trial` | Número de repetición desde cero |
| `processes` | Cantidad de procesos MPI |
| `seconds` | Máximo de las duraciones locales de búsqueda |
| `attempts` | Total de candidatos probados por los procesos |
| `found` | Llave encontrada o `null` |
| `winner` | Rank que reportó la coincidencia o `null` |
| `padding` | Tratamiento del relleno utilizado |

El tiempo interno incluye descifrado de candidatos y coordinación MPI. Excluye arranque, lectura, escritura final y reunión final de estadísticas. El tiempo externo de un script puede ser mayor.

Códigos del programa: `0` éxito; `2` búsqueda agotada sin coincidencia; `1` error de entrada o ejecución. En Bash, consultar inmediatamente el último código con `echo $?`. MPI puede añadir mensajes propios cuando un proceso termina con un código distinto de cero.

## 9 Usar Docker desde Windows o Mac

Abrir Docker Desktop y esperar a que el motor esté activo. Ejecutar los comandos siguientes desde la raíz del repositorio, en **PowerShell o Terminal de Mac**. Cada comando Docker de este apartado está en una sola línea y sirve en ambos shells.

```text
docker version
docker build -t mpi-cluster-image .
docker run --rm mpi-cluster-image mpicc --version
docker run --rm mpi-cluster-image mpirun -np 2 echo "Proceso MPI ejecutado"
docker run --rm mpi-cluster-image bash cluster/preflight.sh
```

Se deben observar GCC, dos mensajes de MPI, el control DES y la conexión SSH local exitosa. El Dockerfile compila dentro de Linux e instala las dependencias. No necesita que el host tenga Open MPI o OpenSSL instalados.

### Recuperar el grupo 4 y sacar el archivo del contenedor

El siguiente contenedor termina después de la búsqueda, pero conserva su sistema de archivos porque no se usa `--rm`:

```text
docker run --name proyecto2-demo-grupo4 mpi-cluster-image mpirun --bind-to none -np 4 ./bin/bruteforce_mpi search --cipher fase2/grupo4/texto_cifrado.des --phrase "la busqueda distribuida termina cuando aparece la frase clave" --upper 1048576 --padding none --out /opt/proyecto2/fase2/grupo4/recuperado_demo.txt
docker cp proyecto2-demo-grupo4:/opt/proyecto2/fase2/grupo4/recuperado_demo.txt ./recuperado_grupo4_demo.txt
```

El archivo queda en la raíz del repositorio del host. Después de comprobarlo, se puede retirar únicamente ese contenedor:

```text
docker rm proyecto2-demo-grupo4
```

Si ese nombre ya existe de una prueba anterior, usar otro nombre o exportar y retirar primero ese contenedor. Con `docker run --rm`, un archivo que solo existe dentro del contenedor desaparece al terminar: por eso aquí se conserva y se extrae con `docker cp`.

## 10 Reproducir el ensayo individual con dos contenedores

Este ensayo utiliza Docker Compose, dos contenedores con cuota de 2 CPU cada uno y una red bridge privada. No utiliza volúmenes y no requiere otra computadora.

La subred predeterminada del ensayo es `192.168.240.0/24`. Si coincide con la
LAN u otra red del equipo, definir `P2_ENSAYO_SUBNET` con una subred privada libre
antes de crear los contenedores. Evitar solapamientos: una red Docker
`172.20.0.0/16`, por ejemplo, intercepta las direcciones de una Wi-Fi
`172.20.10.0/28`. Conservar los resultados antes de retirar y recrear una red.

En **PowerShell**, desde la raíz de este proyecto, usar el Python disponible en esta instalación de Codex:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts/ensayo_local.py
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts/resumir_fase2.py
```

En **Terminal de Mac**, con Python 3 disponible:

```bash
python3 scripts/ensayo_local.py
python3 scripts/resumir_fase2.py
```

Los scripts de ensayo y resumen usan la biblioteca estándar de Python. Antes debe estar construida la imagen con `docker build -t mpi-cluster-image .`.

El script crea maestro y worker, autoriza la llave pública del maestro, prepara un hostfile con saltos LF, verifica los hashes y ejecuta secuencialmente:

1. Un proceso en el contenedor maestro.
2. Cuatro procesos dentro del maestro, compartiendo su cuota de 2 CPU.
3. Cuatro procesos repartidos entre maestro y worker.

Cada configuración usa `full`, 1048576 candidatos, tres repeticiones y un calentamiento. Puede tardar varios minutos; no es necesario repetirla para una demostración rápida del descifrado.

Para inspeccionar los contenedores:

```text
docker compose -f cluster/compose.local.yaml ps
docker compose -f cluster/compose.local.yaml logs
```

Los resultados se exportan a `fase2/resultados`. Si una ejecución falla antes de la exportación o se quieren conservar de nuevo, desde la raíz del host:

```text
docker cp proyecto2-ensayo-master-1:/opt/proyecto2/fase2/resultados ./fase2
```

Para detenerlos sin eliminar sus archivos internos:

```text
docker compose -f cluster/compose.local.yaml stop
```

Para retirar los contenedores y la red del ensayo, hacerlo después de exportar los resultados:

```text
docker compose -f cluster/compose.local.yaml down
```

## 11 Cómo interpretar las mediciones existentes

Las mediciones Docker guardadas son las siguientes. Son observaciones de esta computadora, no promesas de tiempos para otra máquina:

| Caso | Media de búsqueda full |
| --- | --- |
| Un proceso Docker | 39.454460 s |
| Cuatro procesos en un contenedor con cuota de 2 CPU | 54.432158 s |
| Cuatro procesos en dos contenedores de esta PC | 5.112825 s |

Se calculan `S = T1 / Tp` y `E = S / P × 100`. En estos datos el cociente del ensayo entre contenedores supera cuatro. No se interpreta como eficiencia física: cuotas, planificación y colocación en núcleos híbridos no se controlaron para aislar una causa. En particular, cuatro procesos compartiendo cuota de 2 CPU son una sobreasignación, aunque `nproc` muestre más procesadores visibles.

Para comparar ejecuciones, conservar el mismo criptograma, intervalo, relleno, lote, estrategia y modo. `full` fija la cantidad de candidatos; `early` puede cambiar el trabajo total según dónde quede la llave. Tampoco mezclar una referencia WSL con un caso Docker para atribuir el cociente a la red.

## 12 Pruebas de corrección

Después de compilar, ejecutar desde **Bash/Ubuntu**:

```bash
python3 tests/verify.py
python3 tests/verify_phase2.py
```

La primera batería comprueba DES, relleno, recuperación completa, rangos, llaves grandes y terminación sin coincidencia. Debe terminar con `PASS: 22 comprobaciones...`.

La segunda comprueba el grupo 4 con `block` y `cyclic`, texto UTF-8, recifrado exacto, comportamiento PKCS#7 predeterminado y rechazo de una entrada no alineada al cifrar sin relleno. Debe terminar con `PASS fase 2...`.

Estas pruebas usan archivos temporales para sus salidas. No hace falta ejecutar todos los benchmarks para comprobar la corrección.

## 13 Continuar con el clúster físico

Seguir [GUIA_MAC_Y_CLUSTER.md](fase2/GUIA_MAC_Y_CLUSTER.md). Allí están los pasos que deben hacer los compañeros, las IP de ejemplo que deben sustituir y los comandos de ejecución física.

En resumen, el equipo debe conectarse al mismo router, comprobar qué interfaces son visibles dentro de los contenedores, intercambiar solo la llave pública del maestro, definir slots reales y verificar SSH. El ejecutor físico comprueba IP, subred, recursos declarados y hashes antes de lanzar MPI.

Docker Desktop no debe asumirse equivalente a Linux nativo en red host: la guía incluye el diagnóstico de la subred y una alternativa con VM Linux en puente si no aparece la IP física. Habilitar un puerto no demuestra que MPI pueda anunciar una dirección alcanzable.

No se han registrado todavía la prueba entre computadoras, sus capturas ni su tiempo. Esos datos y la confirmación del grupo 4 se incorporarán cuando el equipo los obtenga.

## 14 Bitácora reporte y paquete de entrega

- `scripts/validar_grupo4.py` agrega automáticamente el resultado de cada búsqueda local a `BITACORA.md`.
- `cluster/run_experiment.py` conserva JSON, comandos y logs por experimento; su interpretación se incorpora a la bitácora narrativa.
- `scripts/resumir_fase2.py` calcula las tablas de las mediciones Docker exportadas.
- `scripts/contenido_fase2.py` mantiene la explicación y las conclusiones del reporte. Debe actualizarse cuando se obtengan resultados físicos; la narrativa no se cierra automáticamente al copiar logs.
- `scripts/actualizar_reporte_fase2.py` genera el Markdown y el Word. Requiere `python-docx`, disponible en el Python de documentos de esta instalación de Codex.

Para regenerar el Word desde **PowerShell**, en la raíz:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts/actualizar_reporte_fase2.py
```

Revisar visualmente el Word antes de entregarlo. El reporte de fase 2 está en `output/docx/Informe_Proyecto2_Fase2.docx`; el PDF de `output/pdf` corresponde al informe previo de fase 1.

Para rehacer el paquete con el contenido actual, desde **PowerShell**:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts/empaquetar_fase2.py
```

Se generan `output/Proyecto2_Fase2_Para_Equipo.zip` y su hash `.sha256`. El empaquetador toma archivos que Git conoce y nuevos archivos no ignorados; revisar el estado del repositorio antes de empaquetar. Excluye Git, temporales ignorados y el propio ZIP de destino.

Los scripts antiguos `benchmark.py` y `build_report.py` corresponden a la fase 1: tienen detalles de macOS y pueden sobrescribir resultados anteriores. No son necesarios para usar el programa o demostrar el grupo 4.

## 15 Solución de problemas

| Problema | Qué hacer |
| --- | --- |
| No encuentra un archivo | Revisar `pwd` o `Get-Location` y entrar a la raíz correcta. |
| `mpicc` o `mpirun` no existe | Trabajar en Ubuntu con sus dependencias o dentro de Docker. |
| `Exec format error` | Recompilar para el entorno actual; no ejecutar el binario Linux directamente en Windows o macOS. |
| Docker no conecta con el engine | Abrir Docker Desktop, esperar al motor y comprobar `docker version`. |
| No se puede escribir la salida | Crear antes la carpeta de `--out` y de `--stats`. |
| El grupo 4 no aparece con `[0, 262144)` | Usar `[0, 1048576)` y `--padding none`. |
| El JSON muestra `found: null` | Revisar rango, frase exacta, archivo, representación y relleno; no implica por sí solo un archivo corrupto. |
| Faltan slots MPI | Usar recursos declarados correctamente y menos procesos; no ocultarlo aumentando slots ficticios. |
| El hostfile produce parse error | Guardarlo como texto UTF-8 sin BOM y con saltos LF. El ejecutor incluido normaliza sus saltos. |
| El contenedor de demostración ya existe | Exportar sus archivos y retirarlo, o elegir un nombre distinto. |
| SSH funciona pero MPI entre máquinas se bloquea | Seguir el diagnóstico de interfaces, BTL/OOB y firewall de la guía Mac. |
| El programa parece no terminar | Comprobar el rango: sin `--upper`, el espacio predeterminado es `[0, 2^56)`, no una demostración corta. |

## 16 Recorrido recomendado para presentar el proyecto

1. Explicar el flujo texto, cifrado, candidatos y frase conocida.
2. Mostrar `selftest` y una recuperación del grupo 4 con cuatro procesos.
3. Abrir el texto recuperado y el certificado de recifrado exacto.
4. Explicar `block`, `cyclic`, `early`, `full` y el intervalo exclusivo.
5. Mostrar el Dockerfile y los logs de MPI y SSH.
6. Mostrar las identidades de los dos contenedores en `mpi_nodes.stdout.log` de un ensayo exitoso.
7. Abrir el resumen de mediciones, la bitácora y el reporte Word.
8. Indicar expresamente que la prueba con router y computadoras distintas se completará con el equipo.

Repositorio: [iancumes/Proyecto2_Paralela](https://github.com/iancumes/Proyecto2_Paralela).
