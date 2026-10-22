# Informe de la fase 2 del Proyecto 2

Computación Paralela y Distribuida | Actualización 21/10/2026

## Resultado del trabajo individual

Se recuperó el texto del grupo 4 con la llave 900000, se comprobó su frase objetivo y se reprodujo exactamente el criptograma al volver a cifrarlo. Se construyó la imagen Docker, se verificaron MPI y SSH y se ejecutó un ensayo distribuido entre dos contenedores de esta misma computadora.

El alcance acordado es completar lo realizable individualmente y entregar instrucciones a los compañeros, especialmente para Mac. La ejecución entre computadoras conectadas al router se realizará cuando el equipo se reúna. Los tiempos de esta entrega son locales y de un ensayo virtual; no se presentan como resultados de una red física.

| Requisito | Estado verificable |
| --- | --- |
| Descifrado cruzado local | Recuperación y recifrado exacto completados |
| Dockerfile y compilación Linux | Imagen construida y probada |
| MPI con dos procesos y SSH sin contraseña | Pruebas locales aprobadas |
| Comunicación entre contenedores | Ensayo virtual con dos nodos completado |
| Red física y participación de compañeros | Instrucciones y ejecutor preparados |
| Comparación física y captura entre máquinas | Pendientes de ejecución del equipo |
| Discusión y evidencias | Incluidas con límites explícitos |

La sección III del enunciado solicita el tiempo local y la recuperación; las secciones IV y V requieren documentar pruebas y evidencias, y la sección VI exige discusión. Este reporte reúne esas evidencias y la bitácora conserva el detalle reproducible.

El informe previo de fase 1 conserva sus resultados originales de macOS. Los nuevos experimentos se ejecutaron en un Intel Core i9-13900H con 14 núcleos y 20 procesadores lógicos, Windows y Ubuntu/WSL. Docker Desktop observado fue 4.40.0 y su motor Linux 28.0.4.

<!-- pagebreak -->

## Validación cruzada con el grupo 4

El usuario proporcionó el Base64 del grupo 4 y la frase exacta siguiente. Se conservó el material original y se decodificó de manera estricta, comprobando que al recodificar se obtiene la misma secuencia.

```text
la busqueda distribuida termina cuando aparece la frase clave
```

| Dato | Resultado |
| --- | --- |
| Base64 recibido | 2924 caracteres sin saltos |
| Criptograma | 2192 bytes |
| Llave numérica recuperada | 900000 |
| Texto recuperado | 2192 bytes UTF-8 y 355 palabras separadas por espacios |
| Frase objetivo | Presente exactamente |
| Recifrado y comparación binaria | Idéntico al archivo recibido |
| Confirmación del equipo emisor | Pendiente de comunicación entre estudiantes |

La primera búsqueda utilizó el intervalo [0, 262144) y PKCS#7, sin coincidencia. El diagnóstico posterior amplió el intervalo a [0, 1048576) y localizó la llave mediante bloques conocidos de la frase. Ese diagnóstico es una herramienta de interoperabilidad y su tiempo no se utiliza como tiempo del programa MPI.

El texto con la llave correcta no termina en un PKCS#7 válido. Se añadió --padding none para conservar todos sus bytes, manteniendo PKCS#7 como predeterminado para los experimentos anteriores. No se retiraron espacios o saltos del mensaje recibido. Se observó la compatibilidad DES-ECB y la representación de índices de nuestro programa; no se afirma que el emisor haya confirmado su convención de relleno general.

Las búsquedas MPI exitosas en WSL utilizaron block, early, lote 128, el mismo intervalo ampliado, un calentamiento y tres repeticiones medidas. El tiempo interno incluye cálculo y coordinación MPI y excluye arranque y E/S final.

| Procesos locales | Media en segundos | Desviación muestral | Repeticiones |
| --- | --- | --- | --- |
| 1 | 34.381041 | 0.577145 | 3 |
| 4 | 5.396849 | 0.053336 | 3 |

En early cambia la cantidad de candidatos procesados según la ubicación de la llave en la partición. Una aceleración mayor que el número de procesos no debe atribuirse únicamente a capacidad de cómputo. Para las mediciones Docker se añadió un recorrido full con trabajo fijo.

<!-- pagebreak -->

## Entorno Docker y comprobaciones

El Dockerfile usa Ubuntu 22.04 e instala build-essential, openmpi-bin, libopenmpi-dev y openssh-server, además de OpenSSL, Python y herramientas de red. El ejecutable se compila dentro de /opt/proyecto2. No se utilizan volúmenes y no se reutiliza el binario de macOS o Windows.

Se incluyen OMPI_ALLOW_RUN_AS_ROOT=1 y OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1. El servidor SSH permite root por llave pública, deshabilita contraseñas y escucha en 2222 para evitar conflictos con el SSH del host. El cliente aplica StrictHostKeyChecking no para el laboratorio. Cada contenedor genera sus llaves al iniciar; solo se comparte la llave pública del maestro.

| Prueba solicitada | Resultado observado |
| --- | --- |
| mpicc --version | GCC Ubuntu 11.4.0 |
| mpirun -np 2 echo | Dos mensajes Proceso MPI ejecutado |
| Inicio de sshd | Daemon activo en el contenedor |
| ssh localhost sin contraseña | Mensaje de conexión exitosa |
| PermitRootLogin | yes |
| Variables de ejecución root MPI | Configuradas en la imagen |
| selftest DES | Vector conocido y 34 longitudes aprobados |

Se conservan docker_build.log, docker_mpicc.log, docker_mpi_echo.log y docker_ssh_local.log en fase2/evidencias. El programa de fase 1 pasó sus 22 comprobaciones. Las pruebas adicionales verificaron block y cyclic sobre el grupo 4, texto UTF-8, recifrado exacto, preservación del PKCS#7 predeterminado y rechazo de longitudes inválidas sin relleno.

El contenedor maestro autorizó su propia llave para localhost. Su llave pública se añadió a authorized_keys del worker con docker exec. SSH remoto verificó hostname y hashes del código y criptograma antes del lanzamiento MPI. La guía entrega el mismo procedimiento para computadoras distintas.

Los procesos son procesos MPI con memoria privada, no hilos de un único proceso. Docker estandariza dependencias del sistema, pero las arquitecturas de CPU siguen importando: las Mac ARM deben compilar para su arquitectura o registrar la emulación elegida. [3]

<!-- pagebreak -->

## Mediciones en una computadora

El ensayo virtual utiliza dos contenedores con cuota de 2 CPU cada uno y red bridge privada. Maestro 172.21.0.3 y worker 172.21.0.2, subred 172.21.0.0/16. Estas direcciones son de Docker y no prueban participación de otras computadoras.

Se midieron tres repeticiones y un calentamiento por configuración, ejecutadas secuencialmente. El modo full recorrió exactamente 1048576 candidatos con lote 128, reparto block, el mismo criptograma y --padding none. Todos los ensayos exitosos recuperaron la llave 900000 y el mismo texto.

| Ejecución | P | Media s | Aceleración | Eficiencia |
| --- | --- | --- | --- | --- |
| Docker un proceso | 1 | 39.454460 | 1.000 | 100.00 % |
| Docker cuatro procesos en cuota de 2 CPU | 4 | 54.432158 | 0.725 | 18.12 % |
| Dos contenedores en la misma PC | 4 | 5.112825 | 7.717 | 192.92 % |

Las desviaciones muestrales fueron Docker un proceso: 0.266078 s; Docker cuatro procesos en cuota de 2 CPU: 0.938702 s; Dos contenedores en la misma PC: 0.106930 s.

La aceleración se calcula como S = T1 / Tp, tomando Docker con un proceso como referencia; la eficiencia convencional es E = S / P por 100. P cuenta procesos MPI. En la configuración de cuatro procesos dentro de un solo contenedor, esos cuatro procesos comparten una cuota de 2 CPU: la fila documenta sobreasignación local y no cuatro núcleos dedicados. En el ensayo de dos contenedores, dos procesos por contenedor disponen de esa cuota de 2 CPU cada uno.

El cociente del ensayo virtual supera cuatro y su eficiencia convencional supera 100 %. Es un resultado observado que no se interpreta como eficiencia física: las cuotas, el planificador y la asignación de núcleos de este procesador híbrido no se controlaron para aislar una causa. Se conserva el resultado sin atribuirlo a velocidad de red ni extrapolarlo a otras computadoras.

El hostfile de ensayo declara slots=2 max_slots=2 por nodo. mpi_probe registró ranks, hostname e interfaces IPv4; las estadísticas por rank conservan intentos y tiempos de cálculo y sincronización. Los registros evidencia.json, logs y CSV están en fase2/resultados.

La tabla no mide latencia del router ni escalamiento entre equipos. Una comparación física deberá repetir la línea base y el caso distribuido con el mismo modo. Para medir estrictamente tiempo hasta encontrar la llave usar early en ambos casos; para comparar volumen fijo usar full en ambos. No mezclar los tiempos WSL con los de Docker para calcular una aceleración de red.

<!-- pagebreak -->

## Red y preparación de las Mac

La guía fase2/GUIA_MAC_Y_CLUSTER.md incluye instalación, build, arquitectura, red host, intercambio de llave pública, hostfile, firewalls, ejecución y exportación de evidencias. El script cluster/run_experiment.py valida IP, slots, presencia de la subred y hashes antes de lanzar el ataque. Usa --nooversubscribe y distribuye procesos por nodo.

El lanzamiento físico incorpora ambos filtros del enunciado. El primero selecciona interfaces para datos TCP y el segundo para coordinación del runtime MPI. [1]

```text
--mca btl_tcp_if_include SUBRED_REAL
--mca oob_tcp_if_include SUBRED_REAL
```

Se observó la interfaz Wi-Fi del host Windows con 10.100.2.57/19 y una interfaz virtual de VirtualBox con 192.168.56.1/24. No se asumió que fueran la red del router de la práctica. No se modificó el firewall de la red institucional. Se entrega una regla PowerShell limitada al backend Docker, perfil Private y subred indicada por el usuario.

Docker Desktop implementa host networking en capa 4 y no expone directamente las interfaces del host dentro de la VM. Por ello no basta con que el puerto SSH responda para garantizar que MPI anuncie direcciones alcanzables. La guía exige comparar la IP física con ip addr dentro del contenedor y detenerse si no existe la subred requerida. [2]

Resultado de la comprobación host networking en esta computadora: El contenedor host muestra redes de la VM Docker, no la subred Wi-Fi 10.100.0.0/19; no valida conexion fisica MPI..

Si las Mac no muestran la subred física, se propone Linux en una VM con adaptador en puente y Docker Engine dentro de esa VM, conservando --network host. UTM dispone de macOS Bridged y advierte que el puente por Wi-Fi puede requerir configuración adicional. Esa alternativa deberá verificarse con las máquinas del equipo. [4]

| Evidencia física requerida | Situación al cierre individual |
| --- | --- |
| IP y CPU de cada compañero | Por registrar en la reunión |
| SSH entre computadoras | Procedimiento preparado |
| Ranks e IP de computadoras distintas | Captura física pendiente |
| Recuperación distribuida y tiempo | Ejecutor preparado |
| Comparación con referencia local | Cálculo preparado y sin valores inventados |

<!-- pagebreak -->

## Discusión de los resultados

### Por qué puede bloquearse MPI sin filtrar interfaces

MPI puede anunciar varias direcciones e intentar conectar pares por redes que considera compatibles. Dos computadoras pueden tener cada una un docker0 con el mismo rango privado aunque esos puentes sean redes independientes. Una dirección de un contenedor local no representa una ruta hacia el contenedor remoto. Las conexiones TCP pueden reintentarse o fallar mientras otros procesos esperan en inicialización o colectivos. Filtrar BTL y OOB hacia una subred realmente visible y alcanzable evita elegir esos caminos; no repara por sí mismo un firewall, SSH o una IP inexistente. No toda ejecución sin filtros se bloquea. [1]

### Problemas observados y soluciones aplicadas

El motor Docker estaba detenido y el cliente devolvía que no existía el pipe del engine. Se inició Docker Desktop y se verificó el servidor. La validación inicial del grupo 4 no encontró la frase porque se exploró un rango que excluía su llave y se exigía PKCS#7. Se amplió el rango y se habilitó la lectura sin retirar ese relleno. Open MPI rechazó además el hostfile enviado desde Windows con CRLF; se corrigió el transporte a bytes y se normalizó a LF en el ejecutor. Las mediciones con cuatro procesos en cuota de 2 CPU muestran la necesidad de registrar límites de recursos, además de nproc. Estos son problemas locales observados; no se atribuyen incidentes a una red física que no se ha probado.

### Tiempo local frente a tiempo del clúster físico

La recuperación local y los tiempos están documentados. El tiempo del clúster físico aún no existe. Al obtenerlo se calculará S = T_local / T_fisico con el mismo protocolo y E = S / P. Los resultados virtuales anteriores sirven para comprobar software y registro, pero no sustituyen esa comparación.

### Treinta y dos procesos sobre cuatro núcleos

Serían ocho procesos por núcleo antes de considerar otros trabajos del sistema. El planificador alternaría su ejecución, aumentaría cambios de contexto y presión de caché, y procesos que esperan en MPI podrían consumir cuota mientras otros necesitan calcular. Una carga DES limitada por CPU no obtiene ocho veces más capacidad al declarar más slots. El rendimiento puede empeorar y debe medirse. max_slots y --nooversubscribe evitan superar los recursos declarados; el hostfile también debe representar los límites reales, incluidas cuotas de Docker. [5]

<!-- pagebreak -->

## Retos de HPC y cierre del alcance

### Vulnerabilidades y retos logísticos

El acceso root y la desactivación de verificación de host facilitan el ejercicio, pero aumentan el impacto de una llave comprometida o de una suplantación de nodo. Por eso se mantienen contraseñas deshabilitadas, llaves nuevas por contenedor y el intercambio limitado a llaves públicas en la LAN de práctica. No se desactiva el firewall globalmente ni se incorpora una llave privada al repositorio.

También se deben coordinar versiones MPI, arquitecturas, rutas, archivos, subredes, puertos y recursos. Un nodo más lento puede extender las esperas de una reducción colectiva. NAT, interfaces repetidas, redes Wi-Fi con aislamiento y CPU compartidas complican el diagnóstico. Los logs, hashes y controles de conectividad ayudan a distinguir incompatibilidad de datos, falta de rutas y contención de CPU. Son implicaciones de la configuración y del modelo de ejecución, no incidentes físicos inventados.

### Objetivo logrado y aspectos por mejorar

Se cumplió el alcance individual solicitado: recuperación del grupo 4, pruebas locales, imagen reproducible, SSH, ensayo entre contenedores, bitácora y procedimientos para Mac. El objetivo global del enunciado, con computadoras físicas distintas conectadas al router, requiere la participación posterior del equipo.

La ventaja comprobada fue poder reproducir la recuperación y verificarla mediante recifrado exacto. La dificultad técnica principal fue separar formato criptográfico, límites de búsqueda y entorno de ejecución. Se recomienda acordar esos parámetros desde el intercambio, comprobar interfaces antes de lanzar MPI y asignar slots según cuotas reales. La valoración personal sobre lo que más y menos gustó debe completarla cada integrante después de la práctica física.

### Continuación con los compañeros

Elegir maestro y workers, conectar el router privado y registrar IP, arquitectura y CPU. Seguir la guía Mac, intercambiar la llave pública y ejecutar el preflight. Medir referencia y caso físico sin otras mediciones simultáneas. Guardar los logs y la captura exigida, confirmar el texto con el grupo 4 y añadir los resultados y opiniones reales al reporte.

### Referencias

[1] Open MPI 4 y comunicación TCP. https://www.open-mpi.org/faq/?category=tcp

[2] Docker y host networking. https://docs.docker.com/engine/network/drivers/host/

[3] Docker y arquitecturas. https://docs.docker.com/build/building/multi-platform/

[4] UTM y red bridged. https://docs.getutm.app/settings-qemu/devices/network/network/

[5] Open MPI 4 mpirun y slots. https://www.open-mpi.org/doc/v4.1/man1/mpirun.1.php

Fuente de requisitos: Paralela Proyecto 2 P2 (1).pdf, secciones III a VI, páginas 2 a 9.

<!-- pagebreak -->

## Bitácora y archivos de evidencia

BITACORA.md conserva el historial completo, incluidos resultados negativos. Las búsquedas se guardan con números nuevos y los experimentos Docker con fecha y hora de Guatemala, evitando sobrescribir mediciones.

| Etapa | Evidencia |
| --- | --- |
| Fase 1 y compilación WSL | pruebas_usuario/VALIDACION_LOCAL.md |
| Primera búsqueda sin coincidencia | fase2/grupo4/pruebas/prueba_001.json |
| Diagnóstico de la llave 900000 | fase2/diagnostico/grupo4.json |
| Recuperaciones MPI exitosas | fase2/grupo4/pruebas/prueba_002.json y prueba_003.json |
| Integridad del mensaje recuperado | fase2/grupo4/validacion_recuperacion.json |
| Construcción y pruebas Docker | fase2/evidencias |
| Ensayo virtual y medidas | fase2/resultados y resumen.csv |
| Instrucciones de compañeros | fase2/GUIA_MAC_Y_CLUSTER.md |

SHA-256 del texto recuperado

```text
8d1cd8c9a596155e1501bae3fe73db27
ab3e99a73b958fa6dfecbd41baeb9505
```

El texto estable para lectura está en fase2/grupo4/texto_recuperado.txt. Los archivos JSON identifican comandos, parámetros, hashes, duración y resultados. No se entrega una llave SSH privada.

Para reproducir la validación desde Ubuntu/WSL, en la raíz del proyecto

```text
make -B OPENSSL_PREFIX=/usr
python3 tests/verify.py
python3 tests/verify_phase2.py
python3 scripts/validar_grupo4.py
```

Para el ensayo Docker, construir la imagen y ejecutar scripts/ensayo_local.py con Python 3 desde el host. Los contenedores no representan computadoras distintas. Antes de eliminarlos, exportar fase2/resultados con docker cp. Los futuros resultados físicos deben incorporarse como una nueva categoría, conservando las mediciones previas.
