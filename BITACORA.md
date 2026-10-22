# Bitácora del Proyecto 2 de Computación Paralela

Esta bitácora conserva decisiones, comandos, resultados y pendientes. Las entradas anteriores a su creación se reconstruyeron a partir de la conversación y los archivos del proyecto; no se les asignan horas inventadas. Las pruebas nuevas conservan su hora local de Guatemala en archivos JSON. Agregar entradas sin borrar el historial.

## Antecedentes registrados

### Experimento original del 15 de octubre de 2026

Según `results/metadata.json`, el experimento original se ejecutó en macOS con un Apple M1 Pro. Se guardaron 180 mediciones principales, calentamientos y una demostración favorable con la llave original. Estos resultados pertenecen a la fase 1 y no son mediciones del clúster ni del grupo 4.

### Preparación local y publicación

Entrada retrospectiva de esta sesión, sin hora consignada.

- Se revisó la implementación DES y MPI y se escribió `GUIA_EJECUCION.md`.
- Se compiló en Ubuntu-24.04 mediante WSL con `make -B OPENSSL_PREFIX=/usr`.
- Se verificaron `selftest`, recuperación con `block` y `cyclic`, comparación byte por byte y 22 comprobaciones automáticas. Evidencia: `pruebas_usuario/VALIDACION_LOCAL.md`.
- Se creó el repositorio `https://github.com/iancumes/Proyecto2_Paralela`, se subió la rama `main` y, por solicitud del usuario, se cambió su visibilidad a pública. Se incluyó el ejecutable Linux x86-64.

### Preparación del intercambio entre grupos

Entrada retrospectiva de esta sesión, sin hora consignada.

- Se revisó la fase 2 del enunciado. La sección III pide descifrado cruzado local y registro de tiempo y recuperación antes del despliegue en red.
- Se preparó `entrega_validacion/texto_cifrado.des` a partir de nuestro cifrado existente y se incluyó una nota de formato en `entrega_validacion/LEEME.md`.
- Se verificó la recuperación completa de nuestro texto. Se creó el ZIP para que el usuario lo comparta. No se afirma que el otro grupo ya lo haya recibido o descifrado.

## 21 de octubre de 2026

### Recepción del grupo 4

- El usuario identificó al grupo 4 como equipo de intercambio y proporcionó un criptograma en Base64.
- Frase exacta: `la busqueda distribuida termina cuando aparece la frase clave`.
- Se conservó el Base64 en `fase2/grupo4/cifrado_recibido.b64`, retirando únicamente los saltos y marcadores de continuación del mensaje para decodificarlo.
- La decodificación estricta y la recodificación a Base64 fueron correctas: 2924 caracteres Base64, 2192 bytes binarios, longitud divisible entre 8.
- Archivo binario: `fase2/grupo4/texto_cifrado.des`.
- SHA-256: `508919eb64871841a8b074240f2603c93bcfcf8c00c28080fd2f23177c6fd891`.
- El usuario confirmó que el emisor no especificó formato ni rango. Se acordó probar nuestra representación y el rango inicial `[0, 262144)`. Que las instrucciones sean comunes no confirma igualdad de relleno o representación de llaves.

### Prueba exploratoria 001 a las 19 58 hora de Guatemala

Comando desde la raíz del proyecto en Ubuntu/WSL:

```bash
python3 scripts/validar_grupo4.py
```

- Cuatro procesos locales, estrategia `block`, modo `early`, lote de 128.
- Se agotaron 262144 candidatos en el rango `[0, 262144)`.
- Tiempo interno MPI: **3.021528020 s**. Tiempo externo con arranque y demás trabajo del proceso: **5.830198846 s**.
- Resultado: `found: null`, `winner: null`, código del programa 2. No se generó texto recuperado.
- Evidencia: `fase2/grupo4/pruebas/prueba_001.json`, stdout, stderr y CSV por rank.
- Interpretación: no hubo coincidencia bajo esta combinación de rango, formato y frase. No se concluye que el archivo esté mal ni que se haya agotado DES. No se registra este tiempo como un descifrado exitoso o como una referencia definitiva para speedup.

### Control positivo y documentación

- El `selftest` del ejecutable pasó. Un control con nuestro criptograma y la ventana `[135168, 135169)` encontró su llave en un intento y recuperó un archivo idéntico a `data/texto.txt`.
- Entorno observado: Ubuntu/WSL x86-64, Open MPI 4.1.6 y OpenSSL 3.0.13. Evidencia: `fase2/grupo4/pruebas/control_positivo.log`.
- Se inició un reporte de fase 2 en `fase2/INFORME_FASE2.md` y su versión Word en `output/docx/Informe_Proyecto2_Fase2.docx`.
- Se conservó el informe previo de fase 1 y se añadió una referencia al avance de fase 2. No se regeneró el PDF anterior de la fase 1.
- Se revisaron visualmente las cuatro páginas del Word. El renderizador habitual no encontró LibreOffice en el entorno; se exportó el documento con Microsoft Word y se inspeccionaron las imágenes de todas las páginas. Las imágenes y el PDF de revisión se guardan en `tmp/docx_qa_fase2`, fuera del versionado.

### Pendientes

1. Acordar con el grupo 4 el intervalo de búsqueda y confirmar DES-ECB, relleno y conversión del índice de llave. No es necesario solicitarles la llave real.
2. Recuperar la frase y el texto completo; registrar entonces un tiempo local de referencia con una configuración documentada.
3. Obtener confirmación de la prueba del otro grupo sobre nuestro criptograma.
4. Continuar después con Docker, SSH, red física y pruebas de clúster; todavía no se han ejecutado.

Las siguientes ejecuciones de `scripts/validar_grupo4.py` conservarán nuevos registros numerados y añadirán una entrada en esta bitácora. El reporte se actualiza con `scripts/actualizar_reporte_fase2.py` usando el Python de documentos del entorno de Codex.

## Continuación de la fase 2 y alcance individual

El usuario pidió completar la fase 2 y aclaró después que los compañeros aún no estaban disponibles. Se acordó ejecutar todo lo posible en una computadora y preparar procedimientos para Mac. El clúster físico, sus capturas y las opiniones de compañeros se mantienen como pendientes reales.

### Recuperación del grupo 4

- Se creó `src/diagnose_des.c`, un diagnóstico DES-ECB separado de las mediciones MPI. Cifra ocho bloques posibles de la frase conocida para detectar coincidencias sin suponer relleno, y valida descifrando el mensaje completo. Se verificó primero con nuestro criptograma conocido.
- Se exploró el intervalo `[0, 1048576)` con la representación big7 y se encontró la llave **900000**. El texto descifrado no termina con PKCS#7 válido.
- Se añadió `--padding none` a `src/bruteforce_mpi.c`, manteniendo PKCS#7 como predeterminado. No se cambió el cifrado de los experimentos anteriores.
- `tests/verify.py` pasó las 22 comprobaciones. `tests/verify_phase2.py` pasó block, cyclic, UTF-8, recifrado exacto, preservación del valor predeterminado y rechazo de longitud inválida sin relleno.
- Se registraron las búsquedas MPI exitosas en `prueba_002.json` y `prueba_003.json`, con un calentamiento y tres repeticiones. Medias early: 34.381041 s con un proceso y 5.396849 s con cuatro. La cantidad de trabajo cambia en early y esos cocientes no representan por sí solos escalamiento del hardware.
- Se conservó el texto estable en `fase2/grupo4/texto_recuperado.txt`: 2192 bytes UTF-8, 355 palabras por separación de espacios y frase exacta presente.
- SHA-256 del texto: `8d1cd8c9a596155e1501bae3fe73db27ab3e99a73b958fa6dfecbd41baeb9505`.
- `scripts/certificar_grupo4.py` volvió a cifrar ese texto y obtuvo exactamente los bytes recibidos. Certificado en `fase2/grupo4/validacion_recuperacion.json`. La confirmación humana del grupo emisor sigue pendiente.

### Docker MPI y SSH

- El cliente Docker estaba instalado, pero inicialmente no existía el pipe del motor Linux. Se inició Docker Desktop 4.40.0; se verificó Engine 28.0.4.
- Se creó el Dockerfile de Ubuntu 22.04 con compilador, Open MPI, OpenSSL, SSH, Python y herramientas de red. El build y la compilación dentro del contenedor pasaron.
- Se configuraron las dos variables root exigidas por el enunciado, PermitRootLogin yes y StrictHostKeyChecking no. Se deshabilitaron contraseñas y se utilizó TCP 2222 para SSH.
- Las llaves de acceso de cada contenedor se generan al iniciar. Solo se intercambió la llave pública del maestro; no se guardó una llave privada en el proyecto.
- Las pruebas mostraron GCC 11.4.0, dos mensajes MPI, SELFTEST OK y SSH localhost sin contraseña. Logs en `fase2/evidencias`.

### Ensayo virtual con dos contenedores

- Se crearon maestro y worker con cuota de 2 CPU por contenedor, sin volúmenes, en una red bridge local. IP observadas: 172.21.0.3 y 172.21.0.2; subred 172.21.0.0/16. No son computadoras físicas distintas.
- La primera ejecución entre nodos falló al leer el hostfile. `od` mostró CRLF por el transporte de texto desde Windows. Se cambió a entrada binaria y el ejecutor guarda una copia normalizada LF antes de llamar a MPI. El fallo se conserva en su carpeta de evidencia.
- La repetición pasó SSH a ambos nodos, comparación de hashes, mpi_probe con cuatro ranks en dos hostnames/IP y recuperación de la llave 900000.
- Se midieron secuencialmente tres repeticiones y un calentamiento en full, con 1048576 candidatos por ejecución. Medias: 39.454460 s (Docker un proceso), 54.432158 s (cuatro procesos en una cuota de 2 CPU) y 5.112825 s (dos contenedores, cuatro procesos en total).
- La sobreasignación local fue más lenta que un proceso. El cociente del ensayo de dos contenedores supera cuatro; se conserva sin interpretarlo como eficiencia física, porque cuotas, planificación y ubicación en los núcleos híbridos no se controlaron para aislar la causa. No se extrapola a un router ni a una Mac.
- Resultados íntegros, CSV por rank, comandos y hashes en `fase2/resultados`; resumen calculado por `scripts/resumir_fase2.py`.

### Red y entrega para compañeros

- Se preparó `fase2/GUIA_MAC_Y_CLUSTER.md`, con arquitectura Apple Silicon/Intel, build, SSH, hostfile, firewalls privados, pruebas físicas y exportación de evidencias.
- Se comprobó `--network host`: dentro del contenedor aparecen redes 192.168.65.x y puentes Docker, sin la subred Wi-Fi real 10.100.0.0/19. La documentación oficial confirma la limitación de capa 4 de Desktop. El ejecutor rechaza una subred que no existe dentro del contenedor.
- Se preparó una alternativa con VM Linux en puente si las Mac presentan esa limitación. No se afirma haber probado las Mac del equipo.
- Se agregó una regla PowerShell opcional para el backend Docker limitada al perfil Private y a la subred declarada. No se aplicó ninguna regla a la red institucional ni se desactivó el firewall.
- Se habilitó HostNetworkingEnabled en Docker Desktop para completar la prueba local de puertos y se conservó una copia de la configuración anterior en AppData Docker. La prueba posterior se guarda en `fase2/evidencias/host_network.json`.

### Estado al cierre de esta continuación

Quedan resueltos la recuperación local del grupo 4, el entorno Docker y SSH y el ensayo virtual. El reporte Word incorpora la discusión solicitada por la sección VI. Siguen pendientes únicamente la ejecución entre computadoras del equipo, sus capturas, la comparación física, la confirmación del emisor y las valoraciones personales de los integrantes.

### Cierre de evidencias y revisión del documento

- Tras habilitar host networking, la conexión TCP desde Windows a localhost:2222 obtuvo el banner SSH del contenedor. Antes de habilitarlo no respondía. Esto verifica el puerto local, no una ruta MPI entre computadoras. `host_network.json` conserva ambos resultados y las interfaces visibles.
- La imagen final elimina las llaves SSH generadas por el instalador en la misma capa de instalación y genera llaves nuevas al arrancar cada contenedor. Se verificó la ausencia de llaves activas en la imagen antes del entrypoint y se repitieron selftest, SSH, búsqueda de tres procesos y recifrado exacto. Evidencias: `docker_final_keys.log`, `docker_final_smoke.log` e `imagen_final.json`.
- Se detuvieron los contenedores del ensayo y el de prueba host después de exportar sus resultados. Docker permanece disponible; no queda un SSH del ensayo escuchando permanentemente.
- Se actualizó el Word a ocho páginas y se revisaron visualmente todas después de exportarlas mediante Microsoft Word. No se observaron recortes, desbordamientos ni tablas partidas. Las imágenes de revisión quedan en `tmp` y no se publican como evidencias físicas.
- Comando de compilación del diagnóstico, ejecutado en WSL: `gcc -O3 -Wall -Wextra -fopenmp src/diagnose_des.c -lcrypto -o bin/diagnose_des`. El caso del grupo 4 se diagnosticó con frase exacta e intervalo `[0, 1048576)`; su JSON se conserva separado de los tiempos MPI.
- Se entrega un paquete de fuentes, instrucciones, Word y evidencias en `output/Proyecto2_Fase2_Para_Equipo.zip`, con hash SHA-256 y comprobación de integridad. Se excluyen archivos temporales, Git y llaves privadas. La versión del proyecto se sincroniza en la rama main del repositorio público para que los compañeros puedan obtener los mismos archivos.

## Nueva prueba prueba_002

Fecha local: 2026-10-21T20:11:21.763294-06:00.

```bash
mpirun --bind-to none -np 1 ./bin/bruteforce_mpi search --cipher fase2/grupo4/texto_cifrado.des --phrase 'la busqueda distribuida termina cuando aparece la frase clave' --lower 0 --upper 1048576 --strategy block --mode early --batch 128 --padding none --repeats 3 --warmups 1 --stats fase2/grupo4/pruebas/prueba_002 --out fase2/grupo4/pruebas/prueba_002_recuperado.txt
```

Código de salida: 0. Evidencia: `fase2/grupo4/pruebas/prueba_002.json`.

Resultado observado: `[{"trial": 0, "processes": 1, "strategy": "block", "mode": "early", "lower": 0, "upper": 1048576, "batch": 128, "seconds": 34.469275845, "attempts": 900001, "found": 900000, "winner": 0, "padding": "none"}, {"trial": 1, "processes": 1, "strategy": "block", "mode": "early", "lower": 0, "upper": 1048576, "batch": 128, "seconds": 34.908987268, "attempts": 900001, "found": 900000, "winner": 0, "padding": "none"}, {"trial": 2, "processes": 1, "strategy": "block", "mode": "early", "lower": 0, "upper": 1048576, "batch": 128, "seconds": 33.764859227, "attempts": 900001, "found": 900000, "winner": 0, "padding": "none"}]`.

## Nueva prueba prueba_003

Fecha local: 2026-10-21T20:13:40.885469-06:00.

```bash
mpirun --bind-to none -np 4 ./bin/bruteforce_mpi search --cipher fase2/grupo4/texto_cifrado.des --phrase 'la busqueda distribuida termina cuando aparece la frase clave' --lower 0 --upper 1048576 --strategy block --mode early --batch 128 --padding none --repeats 3 --warmups 1 --stats fase2/grupo4/pruebas/prueba_003 --out fase2/grupo4/pruebas/prueba_003_recuperado.txt
```

Código de salida: 0. Evidencia: `fase2/grupo4/pruebas/prueba_003.json`.

Resultado observado: `[{"trial": 0, "processes": 4, "strategy": "block", "mode": "early", "lower": 0, "upper": 1048576, "batch": 128, "seconds": 5.344241034, "attempts": 454561, "found": 900000, "winner": 3, "padding": "none"}, {"trial": 1, "processes": 4, "strategy": "block", "mode": "early", "lower": 0, "upper": 1048576, "batch": 128, "seconds": 5.395420789, "attempts": 454561, "found": 900000, "winner": 3, "padding": "none"}, {"trial": 2, "processes": 4, "strategy": "block", "mode": "early", "lower": 0, "upper": 1048576, "batch": 128, "seconds": 5.450885256, "attempts": 454561, "found": 900000, "winner": 3, "padding": "none"}]`.
