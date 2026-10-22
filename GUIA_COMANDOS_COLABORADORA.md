# Comandos para la computadora colaboradora

Esta guía es para la persona que aporta una segunda computadora, especialmente una Mac. La persona que coordina debe seguir [la guía de la maestra](GUIA_COMANDOS_MAESTRA.md).

**Tu computadora ejecutará procesos MPI, pero no tienes que lanzar por tu cuenta el ataque distribuido.** La maestra los inicia por SSH. Necesitas el mismo código y criptograma, un nodo accesible y la llave pública de la maestra autorizada.

## Orden de coordinación

| Momento | Qué haces tú | Qué hace la maestra |
| --- | --- | --- |
| A | Preparas código, imagen y nodo | Prepara su nodo |
| B | Compruebas tu red y envías IP y slots | Recibe tus datos y comparte los suyos |
| C | Recibes e instalas `maestro.pub` | Te envía su archivo y su huella |
| D | Confirmas que estás lista y mantienes el nodo activo | Prueba SSH, crea el hostfile y comprueba MPI |
| E | Dejas que los procesos remotos trabajen | Ejecuta y registra la búsqueda |
| F | Esperas confirmación, guardas logs y detienes tu nodo | Exporta resultados y avisa que terminó |

## Datos de la otra computadora que necesitas

| Dato recibido de la maestra | Dónde se utiliza en tu computadora |
| --- | --- |
| SHA de Git | Compararlo con `git rev-parse HEAD` antes de construir |
| IP alcanzable de la maestra | Prueba de conectividad del apartado B; no va en `authorized_keys` |
| Subred o máscara del router | Comprobar que ambos nodos pertenecen a la LAN acordada |
| Archivo `maestro.pub` | Copiar a `/root/.ssh/maestro.pub` y añadir a `/root/.ssh/authorized_keys`, dentro de tu contenedor |
| Huella de esa llave pública | Compararla con `ssh-keygen -lf` antes de autorizar |

**Tú no tienes que crear el hostfile de MPI ni introducir tu IP en el código C.** Envías tu IP y tus slots a la maestra; ella los escribe en `/opt/proyecto2/cluster_hosts` de su propio contenedor.

## A Preparar la Mac y el proyecto

### A1 Abrir el proyecto en Terminal del host

Instalar/abrir Docker Desktop para tu arquitectura y esperar al motor. En esta guía, **host** significa la Mac o, si necesitas una VM en puente, la VM Linux desde la que se ejecuta Docker.

En **Terminal de Mac**, desde una carpeta de trabajo, para un clon nuevo:

```bash
git clone https://github.com/iancumes/Proyecto2_Paralela.git
cd Proyecto2_Paralela
```

Si ya tienes el clon, entrar a su carpeta en lugar de clonarlo otra vez. Comprobar primero el estado y conservar cualquier cambio local antes de actualizar:

```bash
git status --short
git pull --ff-only
git rev-parse HEAD
```

Comparar el último SHA con el que te envió la maestra. Si no coincide, avísale y acuerden la revisión antes de construir; no borrar cambios para resolverlo.

### A2 Construir y comprobar

Desde **Terminal del host**, en la raíz del proyecto:

```bash
uname -m
docker version
docker build -t mpi-cluster-image .
docker run --rm mpi-cluster-image mpicc --version
docker run --rm mpi-cluster-image mpirun -np 2 echo 'Proceso MPI ejecutado'
docker run --rm mpi-cluster-image bash cluster/preflight.sh
```

Se deben observar compilador, dos mensajes MPI, `SELFTEST OK` y conexión SSH local exitosa.

En Docker Desktop, habilitar **Settings > Resources > Network > Enable host networking**, aplicar y reiniciar. La comprobación B2 determina si además puedes participar en la red física requerida.

En Apple Silicon, el build normal compila para ARM; no copies ni ejecutes directamente el binario Linux x86-64 que viene en `bin`. Acuerden con la maestra si trabajarán con compilaciones nativas o con una plataforma común emulada. La explicación está en [la guía Mac y clúster](fase2/GUIA_MAC_Y_CLUSTER.md).

### A3 Arrancar tu nodo

Desde **Terminal del host**:

```bash
docker run -d --network host --name mpi_node mpi-cluster-image
docker exec mpi_node hostname
docker exec mpi_node bash cluster/preflight.sh
```

Si ya existe el contenedor correcto de esta práctica, inspeccionarlo con `docker ps -a` y reanudarlo con `docker start mpi_node`. Recrearlo genera nuevas llaves y obliga a repetir la autorización de la maestra.

## B Identificar tu IP y enviarla a la maestra

### B1 Obtener los datos de tu red

En **Terminal de Mac**:

```bash
networksetup -listallhardwareports
ipconfig getifaddr en0
ifconfig en0
```

Cambiar `en0` si tu conexión al router utiliza otra interfaz. Anotar la IP y la máscara; no elegir loopback, un adaptador de VPN ni una red Docker interna.

Si ejecutas Docker en una **VM Linux en puente**, estos comandos se sustituyen por los de la terminal de la VM:

```bash
ip -4 -o addr show scope global
```

En ese caso debes enviar la IP alcanzable de la VM Linux, no la IP distinta que pueda tener macOS.

### B2 Comprobar las interfaces de tu contenedor

Desde **Terminal del host**:

```bash
docker exec mpi_node ip -4 addr
docker exec mpi_node nproc
docker exec mpi_node mpirun --version
docker exec mpi_node hostname
```

La subred del router debe aparecer dentro del contenedor y ser alcanzable desde la maestra. `nproc` muestra procesadores visibles; los slots acordados no deben superar la cuota/CPU que realmente asignaste a Docker o a la VM.

**Si ves solamente redes internas de Docker/VM y no la subred física, no envíes una IP 172.x local como si fuera tu dirección accesible desde la otra computadora.** Avisar a la maestra y seguir la alternativa de VM Linux con red en puente de [la guía Mac y clúster](fase2/GUIA_MAC_Y_CLUSTER.md). Repetir el arranque y la comprobación en el entorno corregido antes de continuar.

### B3 Mensaje que debes enviar

Completar con tus datos reales:

```text
IP de mi nodo Linux: ...
Prefijo o máscara: ...
Slots que puedo asignar: ...
Hostname del contenedor: ...
Versión Open MPI: ...
SHA del repositorio: ...
Subred visible dentro de mi contenedor: sí/no
```

La maestra colocará tu IP en su variable `IP_COLABORADORA`, tus slots en `SLOTS_COLABORADORA` y ambos en la segunda línea de su hostfile. Tú no necesitas editar esos datos en tu programa.

Recibir también la IP de su nodo y la subred común. Como comprobación TCP opcional, entrar a **Bash de tu contenedor**:

```bash
docker exec -it mpi_node bash
```

Ya dentro, sustituir la IP de ejemplo por la que te envió la maestra:

```bash
IP_MAESTRA='192.168.1.10'
nc -vz "$IP_MAESTRA" 2222
exit
```

Esta prueba solo comprueba el puerto SSH de la maestra; no demuestra conectividad completa de MPI. No necesitas hacer `ssh` hacia ella para el caso de dos computadoras ni enviarle tu llave privada.

## C Recibir e instalar la llave pública de la maestra

### C1 Colocar el archivo recibido en la raíz de tu proyecto

Esperar a que la maestra te envíe **`maestro.pub` y su huella**. Es la llave pública generada por su contenedor.

Si el archivo recibido está en Downloads, desde **Terminal de Mac**, estando en la raíz del repositorio:

```bash
cp "$HOME/Downloads/maestro.pub" ./maestro.pub
docker cp ./maestro.pub mpi_node:/root/.ssh/maestro.pub
docker exec mpi_node ssh-keygen -lf /root/.ssh/maestro.pub
```

Si lo guardaste en otra carpeta, cambiar solamente la ruta del primer comando. La copia final debe quedar en `/root/.ssh/maestro.pub` **dentro de tu contenedor**.

Comparar la huella impresa con la que recibiste de la maestra. Si no coincide o el archivo no es una llave pública válida, detenerse y pedir el archivo correcto.

### C2 Autorizar a la maestra

Desde **Terminal del host**:

```bash
docker exec -it mpi_node bash
```

Ahora, en **Bash dentro de tu contenedor**:

```bash
mkdir -p /root/.ssh
chmod 700 /root/.ssh
touch /root/.ssh/authorized_keys
grep -qxF "$(cat /root/.ssh/maestro.pub)" /root/.ssh/authorized_keys || cat /root/.ssh/maestro.pub >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
ssh-keygen -lf /root/.ssh/authorized_keys
exit
```

`authorized_keys` contiene **llaves públicas**, una por línea. Aquí no se coloca una IP ni un nombre de computadora. La llave de tu propio contenedor puede aparecer también: la preparación local la autoriza para `ssh localhost`.

El comando con `grep` evita volver a añadir la misma línea si repites este paso. Nunca reemplazar este archivo por la llave privada de nadie.

### C3 Confirmar a la maestra

Enviar este mensaje, completando la IP:

```text
Llave pública instalada y huella comprobada.
Mi nodo sigue en: ...
El contenedor mpi_node está encendido.
Ya puedes probar SSH desde tu contenedor.
```

Este es el momento en que la maestra pasa a D. Si aún no instalaste la llave, debe esperar.

## D Mantener tu nodo listo para la prueba SSH y MPI

Desde **Terminal del host** puedes comprobar:

```bash
docker ps --filter name=mpi_node
docker logs mpi_node
```

Si la maestra recibe `Permission denied`, revisar C y confirmar que no recreaste el contenedor. Si recibe `Connection refused` o timeout, revisar que siga encendido, las IP, el puerto 2222, la red y los firewalls. No resolverlo desactivando globalmente el firewall.

En Mac, permitir el backend de Docker en las opciones del firewall para la práctica. Si usas una VM, revisar también su firewall. MPI necesita TCP adicional para datos y coordinación; que SSH funcione por sí solo no completa la prueba.

No copiar `cluster_hosts` de la maestra a tu nodo. Tampoco modificar manualmente la frase ni la llave del código: el mismo programa y el mismo criptograma ya están dentro de la imagen.

## E Mientras la maestra ejecuta

- Mantener encendida la computadora, sin suspensión y conectada al mismo router.
- Mantener activo `mpi_node`; no detener Docker Desktop.
- No lanzar a la vez tu propio benchmark ni otra búsqueda del proyecto.
- Dejar que la maestra complete la referencia local y la búsqueda distribuida.

Puedes ver los procesos sin lanzar otro ataque:

```bash
docker exec mpi_node ps -eo pid,etime,args
```

Durante la búsqueda deberían aparecer procesos del programa. La maestra registra `mpi_probe` con los ranks e IP; el texto recuperado y las estadísticas reunidas se guardan en su contenedor. No es un error que tu carpeta local no reciba ese archivo.

## F Guardar tu información y cerrar

Esperar el mensaje **«Prueba terminada y resultados exportados»** de la maestra.

Desde **Terminal del host**, en la raíz de tu repositorio:

```bash
docker logs mpi_node > colaboradora_reunion_01.log 2>&1
docker exec mpi_node hostname
docker exec mpi_node uname -m
docker exec mpi_node nproc
docker stop mpi_node
```

Enviar a la maestra tu log, modelo/arquitectura de la Mac o VM, CPU/slots asignados, IP, versión y cualquier problema real observado. Para otra reunión, cambiar el nombre del log a uno nuevo.

`docker stop` conserva el contenedor. Si después lo eliminas y vuelves a crearlo, reinstalar `maestro.pub` antes de una nueva prueba.

## Resumen de dónde va cada dato

| Dato | En tu computadora colaboradora | En la maestra |
| --- | --- | --- |
| Tu IP | La identificas y se la envías | `IP_COLABORADORA` y segunda línea de `cluster_hosts` |
| Tus slots | Los acuerdas según recursos reales | `SLOTS_COLABORADORA` y campos de tu línea del hostfile |
| IP de la maestra | Se usa opcionalmente en `nc -vz IP 2222` | Primera línea de `cluster_hosts` |
| `maestro.pub` | `/root/.ssh/maestro.pub`, añadido a `authorized_keys` | Se exporta de `/root/.ssh/id_rsa.pub` |
| Llave privada de la maestra | No se recibe ni se copia | Permanece en su contenedor |
| Resultado del descifrado | Lo registra y exporta la maestra | Carpeta fechada en `/opt/proyecto2/fase2/resultados` |

Esta guía cubre la pareja de dos computadoras. Para sumar más workers se debe ampliar el hostfile y revisar las autorizaciones SSH entre nodos de lanzamiento; no asumir que la configuración de una pareja basta para cualquier cantidad de computadoras.
