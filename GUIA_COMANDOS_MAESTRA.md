# Comandos para la computadora maestra

Esta guía es para quien coordina la ejecución y guarda los resultados. La otra persona debe seguir [la guía de la computadora colaboradora](GUIA_COMANDOS_COLABORADORA.md). Ambas usan los mismos puntos de encuentro: no avanzar a la ejecución distribuida hasta completar el intercambio indicado.

El caso inicial es **dos computadoras**: una maestra y una colaboradora. La maestra también calcula; no se limita a enviar trabajo. Los comandos del programa buscan el texto del grupo 4.

## Orden de trabajo entre las dos personas

| Momento | Maestra | Colaboradora |
| --- | --- | --- |
| A | Prepara código, imagen y nodo | Prepara código, imagen y nodo |
| B | Comprueba su red y recibe IP y slots de la otra | Comprueba su red y envía IP y slots |
| C | Envía `maestro.pub` y su huella | Instala ese archivo en su contenedor y confirma |
| D | Prueba SSH y crea `cluster_hosts` | Mantiene su contenedor encendido |
| E | Mide la referencia y ejecuta MPI distribuido | Deja que MPI lance los procesos por SSH |
| F | Exporta resultados y avisa que terminó | Guarda sus logs y detiene el nodo |

## Datos que vas a recibir y dónde se colocan

| Dato | Quién lo proporciona | Dónde lo colocas |
| --- | --- | --- |
| IP alcanzable de la maestra | Tú la identificas en tu nodo | Variable `IP_MAESTRA` y primera línea de `/opt/proyecto2/cluster_hosts` |
| IP alcanzable de la colaboradora | La otra persona, al terminar B | Variable `IP_COLABORADORA` y segunda línea de ese hostfile |
| Subred común del router | Se verifica entre ambos | Variable `SUBRED`, usada en filtros BTL y OOB |
| Slots de la maestra | Tú, según CPU realmente disponibles | Variable `SLOTS_MAESTRA`, campos `slots` y `max_slots` |
| Slots de la colaboradora | La otra persona | Variable `SLOTS_COLABORADORA`, campos de su línea del hostfile |
| Llave pública de la maestra | Tu contenedor la genera | La exportas como `maestro.pub` y la otra persona la autoriza |

**Las IP de ejemplo de esta guía no son las de sus computadoras.** Los únicos valores de red que debes copiar son los observados durante la reunión. El puerto SSH ya está configurado como **2222**; no se agrega `:2222` a las IP del hostfile.

## A Preparar tu computadora

### A1 Entrar al repositorio desde el host

El **host** es Windows, Mac o la VM Linux donde ejecutas Docker. Todavía no estás dentro del contenedor.

Si utilizas el proyecto existente de esta computadora Windows, abrir **PowerShell**:

```powershell
Set-Location "C:\Users\ianro\OneDrive\Documentos\Uvg\Octavo Semestre\Paralela\Proyecto2\Proyecto2"
```

Si empiezas con un clon nuevo, desde una carpeta de trabajo del host, en PowerShell o Terminal:

```text
git clone https://github.com/iancumes/Proyecto2_Paralela.git
cd Proyecto2_Paralela
```

En un clon existente, comprobar primero que no hay trabajo local pendiente. Si `git status --short` muestra cambios, conservarlos antes de actualizar; no usar un reset para borrarlos.

```text
git status --short
git pull --ff-only
git rev-parse HEAD
```

**Enviar a la otra persona el SHA que imprime el último comando.** Los dos deben construir a partir de la misma revisión. Este SHA identifica el código, no es una llave criptográfica.

### A2 Construir y comprobar Docker

Abrir Docker Desktop y esperar al motor. Los siguientes comandos de una línea funcionan desde PowerShell o Terminal, en la raíz del proyecto:

```text
docker version
docker build -t mpi-cluster-image .
docker run --rm mpi-cluster-image mpicc --version
docker run --rm mpi-cluster-image mpirun -np 2 echo "Proceso MPI ejecutado"
docker run --rm mpi-cluster-image bash cluster/preflight.sh
```

Se deben observar GCC, dos mensajes MPI, `SELFTEST OK` y conexión SSH local sin contraseña.

Si usas Docker Desktop, habilitar **Settings > Resources > Network > Enable host networking**, aplicar y reiniciar antes de arrancar el nodo. La comprobación B2 sigue siendo obligatoria: habilitar la opción no garantiza que la subred física aparezca dentro del contenedor.

### A3 Arrancar el nodo maestro

Desde el host:

```text
docker run -d --network host --name mpi_node mpi-cluster-image
docker exec mpi_node hostname
docker exec mpi_node bash cluster/preflight.sh
```

Si `mpi_node` ya existe, inspeccionarlo con `docker ps -a` y, si es el nodo correcto de esta práctica, reanudarlo con `docker start mpi_node`. No retirarlo para resolver un nombre duplicado sin exportar primero sus resultados. Si cambió la imagen y necesitan recrearlo, deberán repetir después el intercambio de llaves.

## B Comprobar la red e intercambiar datos

### B1 Identificar tu IP y prefijo en el host

En **PowerShell de Windows**:

```powershell
Get-NetIPAddress -AddressFamily IPv4 | Format-Table InterfaceAlias,IPAddress,PrefixLength
```

Elegir la interfaz conectada al router de la práctica. No elegir VirtualBox, Bluetooth, loopback ni un puente Docker.

En una **Mac**, usar Terminal para identificar la interfaz y sustituir `en0` si corresponde otra:

```bash
networksetup -listallhardwareports
ipconfig getifaddr en0
ifconfig en0
```

En una **VM Linux conectada en puente**, usar su terminal:

```bash
ip -4 -o addr show scope global
```

Si el nodo corre en una VM en puente, la IP que interesa a MPI es la de esa VM alcanzable desde el router; no se sustituye por la IP del host Windows/Mac.

### B2 Comparar con las interfaces del contenedor

Desde el host:

```text
docker exec mpi_node ip -4 addr
```

**Antes de avanzar:** la dirección que pondrás en el hostfile debe corresponder al nodo Linux y ser alcanzable desde la otra computadora. La subred real del router debe aparecer dentro del contenedor y los dos nodos deben poder comunicarse por ella.

En esta computadora se observó que Docker Desktop mostraba redes de su VM, sin la subred física de Wi-Fi. Si sucede lo mismo, **no continuar con IP ficticias ni con una IP 172.x de Docker que solo existe localmente**. Seguir la sección de VM Linux en puente de [la guía Mac y clúster](fase2/GUIA_MAC_Y_CLUSTER.md), construir/arrancar allí el nodo y repetir B1 y B2. Los pasos que siguen aplican una vez resuelta esa conectividad.

Los firewalls deben permitir SSH y el tráfico TCP de MPI entre los nodos en la LAN privada. Ver la sección de firewalls de la guía anterior; no desactivar globalmente el firewall.

### B3 Recibir los datos de la colaboradora

Pedirle este mensaje después de que termine su comprobación B:

```text
IP de mi nodo Linux: ...
Prefijo o máscara: ...
Slots que puedo asignar: ...
Hostname del contenedor: ...
Versión Open MPI: ...
SHA del repositorio: ...
Subred visible dentro de mi contenedor: sí/no
```

Enviar tus datos equivalentes. No continuar si los SHA o las versiones MPI difieren, si la subred no es visible o si todavía no acuerdan los recursos. Dos slots por computadora son un punto de partida únicamente si cada nodo dispone de al menos dos CPU asignadas; `nproc` por sí solo no refleja necesariamente una cuota Docker.

### B4 Colocar las IP recibidas en la sesión Linux

Desde el host, abrir **Bash dentro del contenedor**:

```text
docker exec -it mpi_node bash
```

Ahora todos los bloques marcados **Bash del contenedor** se ejecutan en esa misma sesión. Funciona igual aunque el host sea Windows o Mac.

```bash
cd /opt/proyecto2
IP_MAESTRA='192.168.1.10'
IP_COLABORADORA='192.168.1.11'
SUBRED='192.168.1.0/24'
SLOTS_MAESTRA=2
SLOTS_COLABORADORA=2
TOTAL_PROCESOS=$((SLOTS_MAESTRA + SLOTS_COLABORADORA))
```

**Editar esas cinco asignaciones con los valores reales antes de ejecutarlas.** La segunda IP y sus slots son los datos que acabas de recibir de la colaboradora. La subred debe coincidir con su máscara real; no asumir `/24`.

Para calcular un CIDR a partir de una IP y máscara conocidas, puedes ejecutar dentro del contenedor, sustituyendo ambas:

```bash
python3 -c 'import ipaddress; print(ipaddress.ip_network("192.168.1.10/255.255.255.0", strict=False))'
```

Las variables solo existen en esta sesión Bash. Si cierras y vuelves a entrar, debes asignarlas de nuevo. El hostfile que crearás después sí queda guardado en el contenedor.

Salir al host para el intercambio del archivo:

```bash
exit
```

## C Enviar tu llave pública y esperar autorización

Desde **PowerShell o Terminal del host**, en la raíz del repositorio:

```text
docker cp mpi_node:/root/.ssh/id_rsa.pub ./maestro.pub
docker exec mpi_node ssh-keygen -lf /root/.ssh/id_rsa.pub
```

**Enviar a la colaboradora el archivo `maestro.pub` y la huella que imprime el segundo comando.** El archivo queda en la raíz del repositorio del host. No enviar `/root/.ssh/id_rsa`: ese archivo sin `.pub` es la llave privada.

La otra persona debe terminar su paso C y confirmar que la huella coincide. Hasta recibir su mensaje **«Llave pública instalada; nodo encendido»**, no iniciar la búsqueda distribuida.

## D Probar SSH y crear el hostfile

### D1 Volver a Bash del contenedor y restaurar las variables

Desde el host:

```text
docker exec -it mpi_node bash
```

Volver a ejecutar las asignaciones **reales** del paso B4. En esta sesión permanecerás hasta terminar la ejecución y revisar los logs.

Comprobar SSH hacia la IP recibida de la colaboradora:

```bash
cd /opt/proyecto2
ssh -p 2222 "root@$IP_COLABORADORA" 'hostname; uname -m; nproc; mpirun --version | head -n 1'
bash cluster/preflight.sh "$IP_COLABORADORA"
```

No debe pedir contraseña. El preflight muestra los hashes del código y criptograma de ambos nodos. La IP identifica a dónde conectarse; la autorización SSH procede del contenido de `authorized_keys` en la colaboradora.

### D2 Escribir exactamente el archivo que utilizará MPI

En **Bash del contenedor maestro**:

```bash
cat > /opt/proyecto2/cluster_hosts <<EOF
$IP_MAESTRA slots=$SLOTS_MAESTRA max_slots=$SLOTS_MAESTRA
$IP_COLABORADORA slots=$SLOTS_COLABORADORA max_slots=$SLOTS_COLABORADORA
EOF
cat /opt/proyecto2/cluster_hosts
printf 'Procesos totales: %s\nSubred: %s\n' "$TOTAL_PROCESOS" "$SUBRED"
```

El contenido esperado para el **ejemplo** sería:

```text
192.168.1.10 slots=2 max_slots=2
192.168.1.11 slots=2 max_slots=2
```

Ese archivo se crea **solo en la maestra**, dentro de su contenedor, y usa `max_slots` con guion bajo. No contiene llaves SSH, nombres de usuario ni puertos. La colaboradora no tiene que copiarlo a su computadora.

### D3 Comprobar que MPI realmente usa ambos nodos

En **Bash del contenedor maestro**:

```bash
mpirun --bind-to none --nooversubscribe \
  --hostfile /opt/proyecto2/cluster_hosts --map-by node \
  --mca pml ob1 --mca btl self,vader,tcp \
  --mca btl_tcp_if_include "$SUBRED" \
  --mca oob_tcp_if_include "$SUBRED" \
  -np "$TOTAL_PROCESOS" ./bin/mpi_probe
```

Se deben observar ranks en **dos hostnames** y las IP acordadas. Si solo aparece una computadora, se bloquea o hay error, detenerse y revisar el hostfile, SSH, interfaces y firewall. No medir todavía ni presentar esa salida como éxito físico.

## E Medir y ejecutar la búsqueda

La colaboradora debe mantener el nodo encendido y evitar otras mediciones. Solo tú lanzas estos comandos.

### E1 Referencia local en la maestra

En **Bash del contenedor maestro**:

```bash
python3 cluster/run_experiment.py --kind local --processes 1 --mode early
```

### E2 Ejecución en las dos computadoras

En la **misma sesión Bash**, con las variables reales y el hostfile ya comprobado:

```bash
python3 cluster/run_experiment.py \
  --kind physical \
  --hostfile /opt/proyecto2/cluster_hosts \
  --subnet "$SUBRED" \
  --processes "$TOTAL_PROCESOS" \
  --mode early
```

El ejecutor utiliza automáticamente el criptograma del grupo 4, su frase exacta, `[0, 1048576)`, `--padding none`, tres repeticiones y un calentamiento. No recibe la llave real como argumento de búsqueda. El resultado esperado es llave `900000`, texto de 2192 bytes y `"ok": true`.

Para comparar trabajo fijo, pueden repetir **los dos comandos** con `--mode full`. No comparar un tiempo local `early` con un tiempo distribuido `full`.

## F Mostrar evidencia y guardar los archivos fuera de Docker

### F1 Revisar la última ejecución física

En **Bash del contenedor maestro**:

```bash
CARPETA_FISICA="$(find fase2/resultados -mindepth 1 -maxdepth 1 -type d -name '*_physical_*' | sort | tail -n 1)"
printf 'Carpeta de esta ejecucion: %s\n' "$CARPETA_FISICA"
```

Comprobar que la ruta impresa corresponde a la ejecución que acaban de hacer. Si no imprime una carpeta, no ejecutar los siguientes `cat`: revisar primero el error.

```bash
cat "$CARPETA_FISICA/evidencia.json"
cat "$CARPETA_FISICA/mpi_nodes.stdout.log"
cat "$CARPETA_FISICA/search.stdout.log"
cat "$CARPETA_FISICA/texto_recuperado.txt"
```

Tomar la captura real con el comando, los nodos/IP participantes y la llave encontrada. Los logs del ejecutor son la evidencia; una carpeta marcada `physical` por sí sola no certifica que usaron computadoras distintas. Si `ok` es falso, conservar los logs del fallo y corregirlo antes de dar la práctica por completada.

### F2 Volver al host y exportar

Salir del contenedor:

```bash
exit
```

En **PowerShell o Terminal del host**, dentro de la raíz del repositorio:

```text
docker cp mpi_node:/opt/proyecto2/fase2/resultados ./resultados_reunion_01
docker cp mpi_node:/opt/proyecto2/cluster_hosts ./cluster_hosts_reunion_01
docker logs mpi_node
```

Los resultados quedan en el host, en `resultados_reunion_01`. Para otra reunión, elegir un nombre nuevo, por ejemplo `resultados_reunion_02`, para no mezclar entregas.

Confirmar que se exportaron `evidencia.json`, logs, CSV y texto. Enviar al reporte las capturas, IP, slots, versiones y resultados. Avisar a la colaboradora **«Prueba terminada y resultados exportados; ya puedes detener tu nodo»**.

Después, desde el host:

```text
docker stop mpi_node
```

`stop` conserva los archivos. No eliminar el contenedor antes de exportarlos.

## Si cambia algún dato

| Cambio | Qué debes repetir |
| --- | --- |
| Cambió la IP de la colaboradora | Actualizar `IP_COLABORADORA`, recrear el hostfile y repetir SSH y `mpi_probe` |
| Cambió tu IP | Actualizar `IP_MAESTRA`, avisar a la otra persona y recrear el hostfile |
| Cambió la subred | Actualizar `SUBRED`, verificar interfaces y revisar reglas de firewall de la LAN |
| Cambiaron slots | Actualizar variables, hostfile y `TOTAL_PROCESOS` |
| Recreaste tu contenedor | Exportar la nueva `maestro.pub`, repetir C y restaurar variables y hostfile |
| La colaboradora recreó el suyo | Debe volver a instalar tu llave pública; repetir SSH |
| Cambió el código | Construir en los dos nodos con la misma revisión y volver a verificar |

Para más de dos computadoras, el maestro debe agregar una línea por worker y revisar la autorización SSH necesaria entre los nodos de lanzamiento. Esta guía valida la coordinación de la pareja maestra-colaboradora; no asumir que copiar solo un hostfile completa una topología mayor.
