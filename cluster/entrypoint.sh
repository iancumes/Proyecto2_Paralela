#!/bin/bash
set -euo pipefail
mkdir -p /run/sshd /root/.ssh
chmod 700 /root/.ssh
ssh-keygen -A >/dev/null
if [[ ! -f /root/.ssh/id_rsa ]]; then
    ssh-keygen -q -t rsa -b 3072 -N '' -f /root/.ssh/id_rsa
fi
touch /root/.ssh/authorized_keys
pub=$(cat /root/.ssh/id_rsa.pub)
grep -qxF "$pub" /root/.ssh/authorized_keys || printf '%s\n' "$pub" >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
# Permite comandos de prueba con SSH y arranca el daemon una sola vez.
if [[ "$1" != /usr/sbin/sshd ]]; then
    /usr/sbin/sshd
fi
exec "$@"
