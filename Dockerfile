FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    OMPI_ALLOW_RUN_AS_ROOT=1 \
    OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential openmpi-bin libopenmpi-dev openssh-server openssh-client \
    libssl-dev python3 ca-certificates iproute2 iputils-ping netcat-openbsd \
    && rm -f /etc/ssh/ssh_host_* \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/proyecto2
COPY Makefile ./
COPY src/ src/
COPY data/texto.txt data/key_135168.des data/
COPY fase2/grupo4/texto_cifrado.des fase2/grupo4/
COPY scripts/validar_grupo4.py scripts/
COPY cluster/ cluster/
RUN make -B OPENSSL_PREFIX=/usr && \
    rm -f /etc/ssh/ssh_host_* && \
    chmod +x cluster/*.sh && \
    mkdir -p /run/sshd /root/.ssh fase2/resultados && \
    chmod 700 /root/.ssh && \
    printf '%s\n' 'Port 2222' 'PermitRootLogin yes' 'PubkeyAuthentication yes' \
      'PasswordAuthentication no' 'KbdInteractiveAuthentication no' \
      'UsePAM no' 'PidFile /run/sshd.pid' > /etc/ssh/sshd_config && \
    printf '%s\n' 'Host *' '    Port 2222' '    StrictHostKeyChecking no' \
      '    UserKnownHostsFile /dev/null' '    BatchMode yes' \
      '    ConnectTimeout 5' '    LogLevel ERROR' >> /etc/ssh/ssh_config

# Cada contenedor genera sus propias llaves al iniciar; la imagen no lleva secretos.
EXPOSE 2222
ENTRYPOINT ["/opt/proyecto2/cluster/entrypoint.sh"]
CMD ["/usr/sbin/sshd", "-D", "-e"]
