# Primera compilación y validación local

Validación ejecutada por Codex en Ubuntu-24.04 mediante WSL, en esta computadora Windows.

## Compilación

Desde la raíz interna `Proyecto2/Proyecto2`:

```bash
make -B OPENSSL_PREFIX=/usr
```

Terminó con código 0 y sin advertencias del compilador. Se reemplazó el ejecutable original de macOS ARM64 por un ejecutable Linux ELF x86-64 en `bin/bruteforce_mpi`.

## Resultados observados

- `selftest`: `SELFTEST OK: vector DES y 34 longitudes PKCS#7`.
- Cifrado con llave `135168`: 2557 bytes de texto y 2560 bytes de criptograma.
- Búsqueda `block`, cuatro procesos, rango `[0, 262144)`, lote 128: llave `135168`, rank ganador 2, 16769 intentos, 0.208705420 segundos.
- Búsqueda `cyclic` con el mismo rango y cuatro procesos: llave `135168`, rank ganador 0, 135553 intentos, 1.878373999 segundos.
- Ambas recuperaciones pasaron `cmp` contra `data/texto.txt`: archivos idénticos byte por byte.
- `make test OPENSSL_PREFIX=/usr` terminó con código 0 y mostró:

```text
PASS: 22 comprobaciones; vector conocido, texto completo, limites, llaves grandes y sin coincidencia.
```

Los tiempos corresponden a una sola ejecución de cada estrategia, con distinta cantidad de trabajo en modo `early`; no son un estudio de rendimiento.

## Archivos generados por la prueba manual

| Archivo | Contenido |
| --- | --- |
| `cifrado.des` | Criptograma creado con llave 135168. |
| `recuperado.txt` | Texto recuperado mediante block. |
| `recuperado_cyclic.txt` | Texto recuperado mediante cyclic. |
| `busqueda_block_ranks.csv` | Estadísticas de los cuatro procesos en block. |

Estos archivos están en `pruebas_usuario`. Se conservaron el código fuente y las mediciones originales de `results`.
