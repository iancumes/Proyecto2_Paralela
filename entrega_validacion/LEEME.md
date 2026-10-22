# Texto para validación cruzada local - Proyecto 2, fase 2

## Archivos y objetivo

- Archivo a descifrar: `texto_cifrado.des`.
- Frase objetivo exacta: `ciencia con paciencia` (minúsculas y espacios simples).
- Tamaño del criptograma: 2560 bytes.
- El mensaje original es texto UTF-8 de 350 palabras y 2557 bytes.
- No se incluye la llave ni el texto plano en este paquete.

SHA-256 del criptograma:

```text
ac3150377dfb06120f5cecd6230137bab17bd28941b1e8e4e461eaedd5ade675
```

## Formato para interoperabilidad

El archivo contiene bytes binarios DES-ECB, sin cabecera, sin salt y sin vector de inicialización. No es hexadecimal ni Base64. No es un archivo generado por `openssl enc` con contraseña.

Se cifró todo el mensaje, bloque por bloque de 8 bytes, con relleno PKCS#7. Al descifrar, validar y retirar el relleno antes de guardar el texto recuperado.

La llave candidata se representa como un índice entero sin signo de 56 bits. Sus bits se distribuyen de mayor a menor en ocho grupos de siete bits. Cada grupo ocupa los siete bits más significativos de un byte y el bit menos significativo se ajusta para obtener paridad impar. Pseudocódigo:

```text
para i desde 0 hasta 7:
    bytes[7 - i] = ((indice >> (7 * i)) & 0x7f) << 1
ajustar paridad impar en cada byte
```

Si su programa usa otra conversión de índices a llaves DES, deben acordar esta representación antes de comparar resultados. Abrir el criptograma en modo binario y utilizar su tamaño real; no medirlo con `strlen`.

## Rango de demostración local

Para una prueba acotada, el archivo es recuperable dentro del rango `[0, 262144)`: desde 0 hasta 262143 inclusive. Este rango es una facilidad de esta entrega, no un requisito adicional del enunciado. Mantener el mismo rango al comparar local y clúster.

## Ejemplo con la interfaz de nuestro programa

Si se utiliza nuestro ejecutable compilado, colocar el archivo en la raíz del proyecto receptor y ejecutar desde esa raíz:

```bash
mpirun --bind-to none -np 4 ./bin/bruteforce_mpi search \
  --cipher texto_cifrado.des \
  --phrase "ciencia con paciencia" \
  --lower 0 --upper 262144 \
  --strategy block --mode early --batch 128 \
  --out texto_recuperado.txt
```

Si utilizan su propia implementación, adapten la entrada y el criterio de coincidencia manteniendo el formato anterior. No es necesario usar nuestro código para la validación.

## Evidencia que debe registrar el grupo receptor

Según la sección III del enunciado: identificar al equipo emisor, registrar el archivo y la frase objetivo, ejecutar localmente en una sola computadora, guardar el tiempo de búsqueda y certificar la recuperación del texto plano. Conservar comando, cantidad de procesos y salida de consola para poder comparar después con el clúster.

Registrar el tiempo local con su configuración concreta. Si calculan además aceleración respecto de un proceso, medir también esa configuración y dejar explícita la referencia utilizada.
