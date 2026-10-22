#!/bin/bash
set -euo pipefail
echo '=== Nodo y entorno ==='
hostname
uname -m
mpirun --version | head -n 1
openssl version
echo "CPU disponibles: $(nproc)"
echo '=== Interfaces visibles dentro del contenedor ==='
ip -4 -o addr show
echo '=== Hash del codigo y criptograma ==='
sha256sum src/bruteforce_mpi.c fase2/grupo4/texto_cifrado.des
echo '=== DES y SSH local ==='
./bin/bruteforce_mpi selftest
ssh localhost echo 'Conexion SSH sin contrasena exitosa'
if [[ $# -gt 0 ]]; then
    echo '=== SSH y codigo en nodos remotos ==='
    for node in "$@"; do
        ssh "root@$node" 'hostname; uname -m; sha256sum /opt/proyecto2/src/bruteforce_mpi.c /opt/proyecto2/fase2/grupo4/texto_cifrado.des'
    done
fi
