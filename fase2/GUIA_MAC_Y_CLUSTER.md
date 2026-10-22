# Guía para compañeros en Mac y ejecución del clúster físico

## Alcance y trabajo ya preparado

El código incluye el caso del grupo 4. Frase: `la busqueda distribuida termina cuando aparece la frase clave`. Criptograma: `fase2/grupo4/texto_cifrado.des`. Para reproducir la búsqueda usar `[0, 1048576)` y `--padding none`. El texto ya se recuperó en la computadora Windows; la ejecución entre computadoras sigue pendiente de la reunión del equipo.

La imagen compila dentro de Linux en `/opt/proyecto2`. No utiliza volúmenes, no copia el ejecutable Windows/macOS y no distribuye llaves SSH privadas. El puerto SSH de los contenedores es **2222**, para evitar conflictos con Remote Login de macOS.

## 1 Preparar la Mac

Instalar Docker Desktop para el procesador correcto: Apple Silicon para M1/M2/M3/M4 y posteriores, o Intel para Mac Intel. Abrir Docker Desktop, esperar a que el motor esté activo y comprobar desde Terminal:

```bash
uname -m
docker version
docker info --format '{{.NCPU}}'
```

El enunciado exige Docker Desktop 4.34 o superior. En Settings > Resources > Network activar **Enable host networking**, aplicar y reiniciar. Asignar CPU y RAM suficientes en Resources; no anunciar más slots que los CPU realmente asignados al contenedor/VM. Para esta práctica pueden empezar con dos slots por computadora.

Usar la misma revisión del proyecto en todas las máquinas. Si recibieron el ZIP local, extraerlo y entrar a su raíz; si el código actualizado ya fue subido a GitHub, clonar:

```bash
git clone https://github.com/iancumes/Proyecto2_Paralela.git
cd Proyecto2_Paralela
```

Si ya existe el clon, no borrar su trabajo: guardar sus cambios y actualizar a la revisión acordada con el equipo. Comprobar que contiene `Dockerfile`, `cluster/` y `fase2/grupo4/texto_cifrado.des`. La versión publicada anteriormente a estos archivos no basta.

```bash
docker build -t mpi-cluster-image .
docker run --rm mpi-cluster-image mpicc --version
docker run --rm mpi-cluster-image mpirun -np 2 echo 'Proceso MPI ejecutado'
docker run --rm mpi-cluster-image bash cluster/preflight.sh
```

Se debe observar GCC, dos líneas de `Proceso MPI ejecutado`, `SELFTEST OK` y `Conexion SSH sin contrasena exitosa`. La imagen usa Ubuntu 22.04 y Open MPI 4.1.x. Comparar la versión exacta entre nodos antes del lanzamiento.

Docker no convierte un binario x86-64 en ARM. El `docker build` normal compila para la arquitectura nativa de cada Mac. Si el equipo decide usar exclusivamente `linux/amd64`, todos deben construir y arrancar con `--platform linux/amd64`; en Apple Silicon se usará emulación y puede cambiar mucho el rendimiento. Conservar esa elección en las mediciones. No mezclar la línea base nativa con una ejecución emulada sin indicarlo.

## 2 Verificar la red antes de configurar MPI

Conectarse al mismo router privado. Evitar redes de invitados, aislamiento entre clientes, VPN y la red institucional si bloquea tráfico entre estudiantes. Obtener interfaz, IP y máscara reales:

```bash
networksetup -listallhardwareports
ipconfig getifaddr en0
ifconfig en0
```

`en0` es solo un ejemplo: utilizar la interfaz que corresponda. La máscara determina el prefijo; no asumir `/24` ni copiar la IP de ejemplo.

Arrancar un contenedor por computadora:

```bash
docker run -d --network host --name mpi_node mpi-cluster-image
docker exec mpi_node ip -4 addr
docker exec mpi_node bash cluster/preflight.sh
```

### Comprobación importante en Docker Desktop

El host networking de Docker Desktop funciona en capa 4 y no expone directamente las interfaces del Mac/Windows dentro de la VM Linux. Por eso una IP LAN que aparece en `ifconfig` de la Mac puede no aparecer en `docker exec mpi_node ip -4 addr`. SSH a un puerto puede funcionar mientras MPI no puede anunciar direcciones alcanzables.

**Si la subred física del router no aparece dentro del contenedor, detener el lanzamiento MPI con ese filtro.** `cluster/run_experiment.py` lo comprueba y guarda el error. No inventar una interfaz ni reemplazar el filtro por `docker0` para presentar esa prueba como física. El ensayo de dos contenedores de esta entrega solo valida software local.

Si sucede esta limitación, la alternativa es ejecutar Linux en una VM con adaptador **bridged/puente** conectado al router, y Docker Engine dentro de esa VM. En Mac Apple Silicon se puede usar una VM Ubuntu ARM64 en UTM con `macOS Bridged`; en Mac Intel, una VM Ubuntu x86-64 con puente. El puente por Wi-Fi puede necesitar configuración adicional; Ethernet suele simplificar la práctica. En Windows se necesita igualmente una VM Linux con un adaptador de red externo/puente, si WSL/Docker Desktop no expone la subred requerida.

Dentro de esa VM, instalar Docker Engine siguiendo la documentación oficial para Ubuntu, copiar el proyecto, construir la misma imagen y ejecutar `docker run -d --network host --name mpi_node mpi-cluster-image`. Verificar que la VM y el contenedor muestran una IP del router alcanzable desde las otras máquinas. Usar esa IP de la VM en el hostfile. Registrar la adaptación en el reporte; sigue utilizando Docker con host networking sobre Linux y computadoras físicas distintas.

La configuración de red física debe verificarse en el aula. No se afirma que la alternativa se haya probado con las Mac del equipo.

## 3 Intercambiar únicamente la llave pública del maestro

Elegir la computadora maestra. En la terminal de su host:

```bash
docker exec mpi_node cat /root/.ssh/id_rsa.pub > maestro.pub
```

El maestro comparte **maestro.pub**, nunca `/root/.ssh/id_rsa`. En cada Mac trabajadora, guardar ese archivo y autorizarlo:

```bash
docker exec -i mpi_node bash -c 'cat >> /root/.ssh/authorized_keys; chmod 600 /root/.ssh/authorized_keys' < maestro.pub
```

Desde el maestro, probar hacia la IP real de cada worker:

```bash
docker exec mpi_node ssh root@192.168.1.11 'hostname; uname -m; nproc'
docker exec mpi_node bash cluster/preflight.sh 192.168.1.11
```

Las direcciones anteriores son ejemplos. `ssh` dentro del contenedor ya utiliza el puerto 2222. La llave del propio maestro se autoriza automáticamente al iniciar, por lo que `ssh localhost` también funciona. Al recrear un contenedor se generan nuevas llaves y debe repetirse el intercambio. No hay contraseñas SSH habilitadas.

## 4 Crear el hostfile con los recursos reales

Copiar `cluster/cluster_hosts.example` a `cluster_hosts` y sustituir IP y recursos. Ejemplo para DOS computadoras con dos slots cada una:

```text
192.168.1.10 slots=2 max_slots=2
192.168.1.11 slots=2 max_slots=2
```

En Open MPI 4 el atributo es **max_slots**, con guion bajo. El enunciado muestra además un ejemplo con `max-slots`; se utiliza aquí la sintaxis admitida por Open MPI. Los slots son recursos declarados al planificador; configurarlos por encima de CPU reales no crea núcleos.

Copiarlo al maestro sin volumen:

```bash
docker cp cluster_hosts mpi_node:/opt/proyecto2/cluster_hosts
```

Mantener el mismo código, versión MPI, criptograma y ruta `/opt/proyecto2` en todos los nodos. El script compara los hashes del código y del criptograma en los workers antes de medir. Comparar también la arquitectura y las versiones; las imágenes compiladas para arquitecturas diferentes tendrán hashes binarios diferentes, aunque compartan fuente.

## 5 Firewalls sin desactivarlos globalmente

Permitir conexiones entrantes del router privado al backend de Docker Desktop en macOS/Windows. SSH necesita TCP 2222 y Open MPI 4 utiliza además conexiones TCP dinámicas para datos y control. El firewall no debe permitir solo SSH: eso puede lanzar workers y bloquear luego `MPI_Init` o las reducciones.

En macOS, revisar Settings > Network > Firewall > Options y permitir el backend Docker para esta práctica. No activar Block all incoming connections. Si se usa una VM en puente, revisar también su firewall y permitir tráfico entre las IP de los nodos dentro de la LAN privada.

En Windows, usar un perfil **Private** solamente para el router de confianza. Se incluye `cluster/permitir_red_privada.ps1`, que agrega una regla para el backend Docker limitada a una subred indicada; requiere PowerShell como administrador. No cambia el perfil ni desactiva el firewall. No se aplicó esta regla a la red institucional observada durante el desarrollo.

```powershell
.\cluster\permitir_red_privada.ps1 -Subnet '192.168.1.0/24'
```

La subred es un ejemplo. Después de la práctica, retirar esa regla con:

```powershell
Remove-NetFirewallRule -DisplayName 'Proyecto2 MPI Docker LAN privada'
```

## 6 Ejecutar y conservar las evidencias

Desde el host maestro, medir primero una referencia local en el mismo contenedor, sin otras mediciones simultáneas:

```bash
docker exec mpi_node python3 cluster/run_experiment.py --kind local --processes 1 --mode early
```

Después ejecutar el caso distribuido; cambiar la subred y el total de procesos por los valores reales:

```bash
docker exec mpi_node python3 cluster/run_experiment.py \
  --kind physical --hostfile cluster_hosts --subnet 192.168.1.0/24 \
  --processes 4 --mode early
```

El script usa estas opciones MPI:

```text
--hostfile cluster_hosts --map-by node --nooversubscribe
--mca pml ob1 --mca btl self,vader,tcp
--mca btl_tcp_if_include SUBRED_REAL
--mca oob_tcp_if_include SUBRED_REAL
```

Primero lanza `mpi_probe` para mostrar rank, hostname e IP; después ejecuta la búsqueda sin recibir la llave como argumento. Guarda comandos, hashes, versiones, hostfile, logs, tres mediciones y estadísticas por rank. El valor esperado de la llave se usa únicamente después para validar la salida del experimento.

Las mediciones emplean un calentamiento descartado. El mismo intervalo, texto, relleno, lote, estrategia y modo deben mantenerse en la referencia y en el clúster. Para una comparación adicional con trabajo fijo, repetir ambos comandos con `--mode full`. En `early`, la ubicación de la llave puede reducir el trabajo al aumentar procesos; explicarlo al interpretar aceleraciones grandes.

Conservar evidencia fuera del contenedor antes de detenerlo:

```bash
docker cp mpi_node:/opt/proyecto2/fase2/resultados ./resultados_cluster
```

Abrir el archivo `evidencia.json` de cada ejecución para consultar los comandos y resultados. Los logs `mpi_nodes.stdout.log` y `search.stdout.log` muestran las identidades y la llave. Para la captura requerida por el enunciado, mostrar en la terminal el comando físico, esas identidades y la recuperación; tomar una captura real durante la reunión. No usar imágenes del ensayo virtual como prueba de computadoras distintas.

## 7 Datos que deben devolver al reporte

- Nombres de integrantes y equipo; modelo, arquitectura y CPU/slots asignados a cada nodo.
- IP reales, subred, router, ruta usada y versión Docker/Open MPI.
- Logs completos y capturas de ejecución física, errores encontrados y correcciones reales.
- Tiempo local y físico, modo, intentos, repeticiones y hash del texto recuperado.
- Confirmación del grupo 4 si el texto coincide con su original y resultado de ellos sobre nuestro texto.
- Opinión real del equipo sobre lo que más y menos les gustó y qué mejorarían.

Con estos datos se completa la comparación física. Las opiniones de los compañeros no se inventan en el reporte.

## 8 Diagnóstico rápido

| Síntoma | Revisar |
| --- | --- |
| Connection refused en 2222 | Contenedor activo, `sshd`, puerto y firewall del host/VM. |
| Permission denied publickey | Llave pública correcta en `authorized_keys` y permisos 700/600; el contenedor pudo haberse recreado. |
| SSH funciona pero MPI se cuelga | Alcance de direcciones anunciadas, IP visibles dentro del contenedor, filtros BTL/OOB y TCP dinámico. |
| No TCP interfaces match | La subred del router no existe dentro del contenedor; comprobar la limitación de Docker Desktop. |
| Not enough slots | Ajustar procesos/slots a CPU reales; no activar oversubscription para ocultarlo. |
| Exec format error | Ejecutable de otra arquitectura; construir dentro de la imagen adecuada. |
| Frase no encontrada | Usar el archivo correcto, rango `[0, 1048576)` y `--padding none` para el grupo 4. |

## Referencias técnicas

- [Docker host networking y limitaciones de Desktop](https://docs.docker.com/engine/network/drivers/host/).
- [Docker para distintas arquitecturas](https://docs.docker.com/build/building/multi-platform/).
- [Open MPI 4 y selección de interfaces TCP](https://www.open-mpi.org/faq/?category=tcp).
- [Open MPI 4 mpirun y slots](https://www.open-mpi.org/doc/v4.1/man1/mpirun.1.php).
- [UTM y adaptadores de red en puente](https://docs.getutm.app/settings-qemu/devices/network/network/).
- [Instalación oficial de Docker Engine en Ubuntu](https://docs.docker.com/engine/install/ubuntu/).
