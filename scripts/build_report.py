#!/usr/bin/env python3
"""Informe PDF y fuente Markdown; utiliza solamente resultados guardados."""
from pathlib import Path
import json
import csv
import statistics as st
import base64
import hashlib
import textwrap
import re
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, Preformatted, KeepTogether
from PIL import Image as PILImage

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf'
OUT.mkdir(parents=True,exist_ok=True)
META=json.loads((ROOT/'results/metadata.json').read_text())
SUMMARY=json.loads((ROOT/'results/summary.json').read_text())
RAW=[json.loads(x) for x in (ROOT/'results/raw.jsonl').read_text().splitlines()]
TEXT=(ROOT/'data/texto.txt').read_text()
KEYS=[8192,135168,249856]
PS=[1,2,4,8]
for name,filename in [('Arial','Arial.ttf'),('Arial-Bold','Arial Bold.ttf'),('Arial-Italic','Arial Italic.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'/System/Library/Fonts/Supplemental/'+filename))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial-Italic',boldItalic='Arial-Bold')
NAVY=colors.HexColor('#153d51'); TEAL=colors.HexColor('#007f78'); INK=colors.HexColor('#263d4b')
LIGHT=colors.HexColor('#eef5f7'); GOLD=colors.HexColor('#b87921')
styles={
 'body':ParagraphStyle('body',fontName='Arial',fontSize=10.2,leading=14.3,textColor=INK,spaceAfter=8),
 'small':ParagraphStyle('small',fontName='Arial',fontSize=8.4,leading=11.4,textColor=INK,spaceAfter=6),
 'h1':ParagraphStyle('h1',fontName='Arial-Bold',fontSize=19,leading=23,textColor=NAVY,spaceAfter=14),
 'h2':ParagraphStyle('h2',fontName='Arial-Bold',fontSize=12,leading=16,textColor=TEAL,spaceBefore=7,spaceAfter=7),
 'kicker':ParagraphStyle('kicker',fontName='Arial-Bold',fontSize=8.5,leading=12,textColor=TEAL,spaceAfter=6),
 'caption':ParagraphStyle('caption',fontName='Arial-Italic',fontSize=8.3,leading=11,textColor=INK,spaceBefore=5,spaceAfter=9),
 'cell':ParagraphStyle('cell',fontName='Arial',fontSize=8.4,leading=11,textColor=INK),
 'headcell':ParagraphStyle('headcell',fontName='Arial-Bold',fontSize=8.4,leading=11,textColor=colors.white),
 'cover':ParagraphStyle('cover',fontName='Arial-Bold',fontSize=34,leading=39,textColor=NAVY,spaceAfter=20),
 'subtitle':ParagraphStyle('subtitle',fontName='Arial',fontSize=15,leading=21,textColor=TEAL,spaceAfter=20),
 'code':ParagraphStyle('code',fontName='Courier',fontSize=8,leading=10.4,textColor=INK,backColor=LIGHT,borderPadding=9,spaceAfter=12),
}
story=[]; md=[]; expected=[]
def P(text,small=False):
    story.append(Paragraph(text,styles['small' if small else 'body']))
    md.append(re.sub('<[^>]+>','',text)+'\n')
def H(text):
    story.append(Paragraph(text,styles['h2']));md.append('### '+text+'\n')
def page(title,kicker='PROYECTO 2 / COMPUTACIÓN PARALELA'):
    if story: story.append(PageBreak())
    expected.append(title)
    story.append(Paragraph(kicker,styles['kicker']))
    story.append(Paragraph(title,styles['h1']))
    md.append('\n## '+title+'\n')
def code(text,small=False):
    ss=styles['code']
    if small:
        ss=ParagraphStyle('tinycode',parent=ss,fontSize=7.4,leading=9.2)
    story.append(Preformatted(text.strip('\n'),ss))
    md.append('```text\n'+text.strip('\n')+'\n```\n')
def table(headers,rows,widths=None,compact=False):
    data=[[Paragraph(escape(str(x)),styles['headcell']) for x in headers]]
    data += [[Paragraph(escape(str(x)),styles['cell']) for x in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),
       ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
       ('TOPPADDING',(0,0),(-1,-1),2 if compact else 5),('BOTTOMPADDING',(0,0),(-1,-1),2 if compact else 5),
       ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),
       ('LINEBELOW',(0,-1),(-1,-1),.6,colors.HexColor('#cbdce1'))]))
    story.append(t);story.append(Spacer(1,10))
    md.append('| '+' | '.join(map(str,headers))+' |\n| '+' | '.join('---' for _ in headers)+' |\n')
    md.extend('| '+' | '.join(map(str,row))+' |\n' for row in rows)
def fig(name,caption,maxh=330,width=495):
    path=ROOT/'figures'/f'{name}.png'
    im=PILImage.open(path);w,h=im.size
    scale=min(width/w,maxh/h)
    image=Image(str(path),width=w*scale,height=h*scale)
    image.hAlign='CENTER';story.append(image)
    story.append(Paragraph(caption,styles['caption']))
    md.append(f'![{caption}](figures/{name}.png)\n')
def get(k,p,s='block',m='early'):
    return next(x for x in SUMMARY if (x['key'],x['processes'],x['strategy'],x['mode'])==(k,p,s,m))
def fmt(x,d=3):return f'{x:.{d}f}'
def keyhex(k):
    result=[]
    for i in range(7,-1,-1):
        b=((k>>(7*i))&127)<<1
        if b.bit_count()%2==0:b|=1
        result.append(b)
    return bytes(result).hex()

# 1: portada.
expected.append('Portada')
story.append(Spacer(1,42))
story.append(Paragraph('PROYECTO 2 · MPI Y CRIPTOGRAFÍA',styles['kicker']))
story.append(Spacer(1,14))
story.append(Paragraph('Búsqueda exhaustiva<br/>de llaves DES<br/>con Open MPI',styles['cover']))
story.append(Paragraph('Implementación, diagramas y evaluación experimental',styles['subtitle']))
P('Computación Paralela · Octavo semestre<br/>15 de octubre de 2026')
story.append(Spacer(1,14))
teamfile=ROOT/'data/equipo.json'
if teamfile.exists():
    team=json.loads(teamfile.read_text())
    table(['Integrante','Carné'],[[x['nombre'],x['carne']] for x in team],[350,145])
else:
    table(['Integrante','Carné'],[['Por completar','Por completar'] for _ in range(3)],[350,145])
story.append(Spacer(1,12))
H('Alcance del trabajo')
P('Se conserva el archivo base, se corrigen sus defectos de cifrado y búsqueda, y se implementa una solución con memoria privada por proceso. El texto contiene <b>350 palabras</b>. La evaluación comprende <b>180 mediciones reales</b>, además de calentamientos y pruebas de corrección.')
P('Las mediciones principales recorren un subconjunto de 2^18 candidatos y utilizan DES real de 56 bits. Se comparan intervalos contiguos, distribución cíclica y búsqueda con trabajo fijo. Los procesos se ejecutan en un Apple M1 Pro; el estudio no incluye una red de varias máquinas.',small=True)
md.insert(0,'# Búsqueda exhaustiva de llaves DES con Open MPI\n')

# 2.
page('1. Fundamentos de DES')
P('DES es un cifrador <b>simétrico</b>: la misma llave secreta permite cifrar y descifrar. Aunque el enunciado usa “llave privada”, aquí no interviene un par de llaves pública y privada. DES transforma bloques de 64 bits y utiliza 56 bits efectivos; los otros ocho bits de su representación se destinan a paridad. [1]')
H('Transformación de un bloque')
P('La permutación IP reorganiza la entrada y la divide en L_0 y R_0, de 32 bits. En cada una de las 16 rondas se calcula L_i = R_(i-1) y R_i = L_(i-1) XOR f(R_(i-1), K_i). Después se concatena R_16 con L_16 y se aplica IP inversa. [1]')
P('La función f expande R de 32 a 48 bits, aplica XOR con la subllave, transforma ocho grupos de seis bits en ocho grupos de cuatro mediante cajas S y permuta los 32 bits resultantes. PC-1 selecciona 56 bits de llave; rotaciones de dos mitades de 28 bits y PC-2 generan las 16 subllaves de 48 bits. Para descifrar se usan en orden inverso. [1]')
H('Preparación del texto en esta implementación')
table(['Paso','Operación que realiza el programa'],[
 ['1. Codificar','Leer el archivo UTF-8 como bytes. Las palabras se cuentan aparte; DES trabaja con bytes.'],
 ['2. Rellenar','Agregar PKCS#7 hasta completar un múltiplo de 8 bytes. Se agrega relleno incluso si la longitud ya es múltiplo de 8. [3]'],
 ['3. Cifrar','Aplicar DES-ECB a cada bloque completo con la misma llave. ECB no necesita vector de inicialización. [2]'],
 ['4. Guardar','Escribir bytes binarios. No usar strlen para medir el criptograma.'],
 ['5. Recuperar','Descifrar todos los bloques, validar y retirar el relleno; buscar la frase exacta.']],[100,395])
P('DES fue retirado como estándar en 2005. En este proyecto se utiliza con finalidad didáctica; ECB también expone la repetición de bloques iguales. [2, 7]',small=True)

# 3.
page('2. Diagrama del algoritmo DES')
fig('des','Figura 1. Flujo de un bloque DES y generación de subllaves. Elaboración propia a partir de FIPS 46-3 [1].',maxh=435)
H('Cómo leer el diagrama')
P('La rama derecha transforma el bloque. La izquierda prepara las subllaves que utiliza cada ronda. Para el descifrado se conserva el flujo y se invierte la secuencia de subllaves. El recuadro de f amplía la operación interna de una ronda; no representa una ronda adicional.',small=True)
P('Por ejemplo, invertir una ronda permite recuperar R_(i-1) = L_i y L_(i-1) = R_i XOR f(L_i, K_i). Esta identidad explica por qué la estructura de Feistel permite recuperar los datos sin invertir individualmente las cajas S. La biblioteca ejecuta las tablas de permutación y sustitución; nuestro programa distribuye las llaves candidatas.',small=True)

# 4.
page('3. Revisión del archivo proporcionado')
P('El archivo original se preserva en <b>original/bruteforce_.c</b>. La compilación directa se intentó con mpicc -O3. En este macOS falla porque no existe la cabecera RPC heredada requerida por el ejemplo:')
code("original/bruteforce_.c:6:10: fatal error:\n'rpc/des_crypt.h' file not found")
table(['Hallazgo en el original','Efecto y corrección aplicada'],[
 ['ecb_crypt(..., 16, ...)', 'Cifra y descifra únicamente los primeros dos bloques. Se reemplaza por un ciclo hasta len, sobre todo el mensaje.'],
 ['encrypt(key, ciph)', 'La firma original no recibe len; decrypt sí lo recibe pero lo ignora. Ambas funciones corregidas reciben y usan len.'],
 ['Frase con espacios externos', 'La frase original no coincide con “(los mismos del proyecto 1),”. Se elige una frase que aparece literalmente en el texto.'],
 ['0xFE << i*8', 'La máscara tiene tipo int. Desplazamientos de 32 bits o más causan comportamiento indefinido en este entorno. Se usan uint64_t y bytes explícitos.'],
 ['Límites de los rangos', 'Para ranks intermedios myupper = fin - 1 combinado con i < myupper omite un candidato. Se usan cantidades y límites exclusivos.'],
 ['MPI_Irecv sobre found', 'El programa escribe found mientras hay una recepción pendiente en ese mismo búfer. Se evita ese acceso mediante una reducción colectiva.'],
 ['MPI_Wait sin solución', 'Si no se detecta la frase, rank 0 espera un mensaje que nadie envía. La versión corregida termina al agotar el trabajo.'],
 ['Sin cronómetro ni validación', 'Se agregan MPI_Wtime, conteo por proceso, repeticiones y comparación byte por byte del texto recuperado.']],[155,340])
P('La ejecución válida y las mediciones corresponden a la versión corregida. El original sin cambios no produjo un ejecutable en este entorno; por ello no se presenta un tiempo suyo ni se utiliza como línea base.',small=True)

# 5.
page('4. encrypt y decrypt: funcionamiento')
P('Las funciones reciben un índice de llave y un búfer que modifican en el mismo lugar. En el original, ambas construyen un long k, ajustan paridad con des_setparity y llaman ecb_crypt. El parámetro DES_ENCRYPT o DES_DECRYPT elige la dirección; el literal 16 restringe el trabajo a 16 bytes.')
code('''// Firmas reales del archivo proporcionado:
void encrypt(long key, char *ciph);
void decrypt(long key, char *ciph, int len);

// Contrato de la version corregida:
encrypt(uint64_t key, unsigned char *data, size_t len);
decrypt(uint64_t key, unsigned char *data, size_t len);''')
H('Conversión portable del índice a la llave DES')
P('Se dividen los 56 bits del índice en ocho grupos de siete. Cada grupo ocupa los bits 7 a 1 de un byte; el bit 0 se ajusta para que el byte tenga una cantidad impar de unos. La enumeración big-endian es explícita: no depende del tamaño de long ni del orden de bytes del procesador.')
code('''for (unsigned i = 0; i < 8; ++i)
    bytes[7-i] = ((key >> (7*i)) & 0x7f) << 1;
DES_set_odd_parity(&bytes);
DES_set_key_unchecked(&bytes, &schedule);''')
table(['Índice decimal','Llave DES de 8 bytes, con paridad'],[[f'{k:,}',keyhex(k)] for k in KEYS],[150,345])
P('DES_set_key_unchecked prepara el calendario de subllaves y permite enumerar también llaves débiles. DES_ecb_encrypt procesa un bloque de ocho bytes en la dirección indicada. Estas funciones están obsoletas desde OpenSSL 3.0; se eligieron para adaptar el ejercicio y mantener visible el costo por candidato. [2]')
P('La conversión nueva es una definición explícita del índice; no pretende reproducir la conversión defectuosa del original. Para comparar resultados entre equipos debe conservarse esta misma convención.',small=True)

# 6.
page('4.1 Flujo del cifrado y descifrado')
fig('crypt','Figura 2. Flujo común de encrypt y decrypt en la versión corregida.',maxh=480)
P('La preparación de subllaves ocurre una vez por llamada, antes del ciclo de bloques. Se usan bloques locales de entrada y salida y memcpy para devolver cada resultado a su posición. El texto de 2 557 bytes recibe tres bytes 03 y produce 2 560 bytes cifrados, distribuidos en 320 bloques.',small=True)
P('El descifrado aplica DES a esos mismos 320 bloques; el retiro de PKCS#7 se realiza después. Un resultado binario no se interpreta como cadena hasta colocar un terminador NUL en una posición válida.',small=True)

# 7.
page('5. tryKey: comprobar un candidato')
fig('trykey','Figura 3. Comparación del flujo original y el flujo corregido de tryKey.',maxh=320)
P('En el original, temp[len+1] es un arreglo local de longitud variable. memcpy copia el criptograma; temp[len]=0 reserva un final de cadena; decrypt modifica la copia y strstr determina si aparece search. El retorno es booleano: 1 cuando el puntero obtenido es distinto de NULL y 0 en otro caso.')
P('En la corrección, scratch se reserva una vez por proceso, evitando crear un arreglo grande en la pila para cada llave. <b>Cada intento descifra el mensaje completo</b>. Después se valida el relleno, se fija scratch[plain_len]=0 y se ejecuta strstr. Un relleno inválido descarta el candidato; la frase sigue siendo necesaria para aceptarlo.')
P('La función nunca modifica cipher. Por eso todos los intentos parten de los mismos bytes. Si se descifrara repetidamente el mismo búfer sin restaurarlo, el segundo intento recibiría el resultado del primero y la búsqueda dejaría de ser correcta.')
P('La frase reduce falsos positivos, pero su presencia no constituye una prueba matemática de unicidad. En los experimentos, además se comprobó fuera del tiempo medido que la llave hallada fue la utilizada y que el archivo recuperado coincidió byte por byte con el original.',small=True)

# 8.
page('6. memcpy: conservar el criptograma')
code('void *memcpy(void *destino, const void *origen, size_t n);')
P('memcpy copia n bytes del origen al destino y devuelve el destino. No agrega un terminador ni se detiene ante un byte cero; las regiones no deben superponerse. [4, §7.24.2.1]')
fig('memcpy','Figura 4. Copia de bytes binarios y terminador agregado por el programa.',maxh=290)
H('Dentro de este programa')
P('La copia inicial permite cifrar un búfer sin perder el texto de referencia. En tryKey se copian exactamente len bytes de cipher a scratch. Cada proceso tiene su propio scratch; MPI no comparte ese puntero entre procesos. El ejemplo de la figura copia el byte 00 de la segunda posición, igual que cualquier otro byte.')
P('El espacio adicional permite escribir el terminador. Ese byte lo escribe el programa, no memcpy. Colocarlo al final evita leer fuera del búfer, pero no elimina posibles ceros internos de un descifrado incorrecto. Por esta razón la longitud del criptograma proviene del archivo, y no de strlen(cipher).',small=True)
P('El costo de la copia es lineal en len. En nuestras mediciones se incluye en cada intento, junto con la preparación de subllaves y el descifrado completo; todas las configuraciones ejecutan el mismo trabajo por candidato.',small=True)

# 9.
page('7. strstr: validar la frase de búsqueda')
code('char *strstr(const char *texto, const char *frase);')
P('strstr devuelve un puntero a la primera aparición de la secuencia buscada, o NULL si no existe. La frase vacía devuelve el inicio; por eso el programa la rechaza. Ambas entradas se interpretan como cadenas terminadas en NUL. [4, §7.24.5.7]')
fig('strstr','Figura 5. Modelo conceptual de búsqueda; la biblioteca puede usar una implementación optimizada.',maxh=280)
H('Coincidencia literal en el experimento')
P('La frase <b>ciencia con paciencia</b> aparece en el segundo párrafo, comienza en el desplazamiento de byte 771 (desde cero) y tiene 21 bytes ASCII. Se compara como secuencia de bytes, incluyendo espacios y mayúsculas. “Ciencia con paciencia” no coincide con nuestra frase. El archivo UTF-8 preserva los acentos del resto del mensaje.')
P('Un descifrado incorrecto puede contener un byte NUL antes de la frase aparente; strstr deja de explorar allí. El mensaje válido no contiene NUL interno. La frase del original, con espacios a ambos lados, no coincide con el fragmento que está entre paréntesis: corregir solo el cifrado no resolvería ese defecto.',small=True)
P('Es posible imaginar un buscador binario de longitud explícita para entradas generales. Aquí se mantiene strstr porque el ejercicio utiliza texto y solicita explicar esa función.',small=True)

# 10.
page('8. Coordinación de los procesos MPI')
fig('mpi','Figura 6. Flujo colectivo de la búsqueda paralela.',maxh=440)
P('MPI_Bcast distribuye el criptograma desde rank 0. Cada proceso conserva una copia y prueba sus candidatos. Cada lote termina con MPI_Allreduce(MPI_MIN): el valor UINT64_MAX representa “sin hallazgo” y cualquier índice válido lo reemplaza. El colectivo entrega el mismo resultado a todos. [5]',small=True)
P('Todos ejecutan la misma secuencia de colectivos, incluso los ranks cuyo rango ya se agotó. El modo early termina al detectar una coincidencia global; full continúa hasta cubrir el espacio completo. De esa forma también se resuelve el caso sin coincidencia sin esperar mensajes inexistentes.',small=True)
P('El lote de 128 amortiza la coordinación a cambio de trabajo adicional antes de detenerse. En la ronda ganadora, cada rank distinto del ganador puede completar hasta 128 intentos. La memoria total crece con P, mientras que el mensaje de reducción contiene solo un índice de llave.',small=True)

# 11.
page('8.1 Distribución del espacio de llaves')
P('El intervalo se define como [L, U), con W=U-L. Para P procesos: q=floor(W/P) y r=W mod P. El rank i recibe c_i=q+1 si i&lt;r y q en otro caso. En la estrategia contigua su inicio es a_i=L+i*q+min(i,r). Cada rank prueba [a_i, a_i+c_i), sin huecos ni duplicación.')
P('En la estrategia cíclica, rank i prueba L+i, L+i+P, L+i+2P, mientras la llave sea menor que U. Su cantidad es cero si i≥W y, en otro caso, 1+floor((W-1-i)/P). La diferencia entre cantidades asignadas no excede una llave.')
fig('partition','Figura 7. Ubicación de las tres llaves frente a particiones contiguas de 2 y 4 procesos.',maxh=225)
H('Orden de búsqueda y tiempo hasta el hallazgo')
P('Si W es divisible entre P y la llave es K, en intervalos el ganador realiza d=(K-L) mod (W/P)+1 intentos. En cíclica realiza d=floor((K-L)/P)+1. Otros ranks pueden completar el lote de la ronda ganadora. Estas expresiones describen posiciones, no una reducción del costo criptográfico por llave.')
P('Para la llave original K=2^54 y el espacio completo W=2^56, P=4 coloca K exactamente al inicio del rango de rank 1; P=8 la coloca al inicio de rank 2. Una búsqueda secuencial desde cero requeriría K+1 intentos. Este caso muestra por qué una llave elegida favorablemente puede distorsionar el speedup.',small=True)

# 12.
page('9. Texto elegido y cifrado completo')
P('<b>350 palabras</b>, contadas por separación en espacios en blanco; <b>2 557 bytes UTF-8</b>, incluidos saltos de línea. Frase exacta: <b>ciencia con paciencia</b>. El texto se redactó para este ejercicio.')
for paragraph in TEXT.strip().split('\n\n'):
    P(escape(paragraph),small=True)
table(['Dato del criptograma principal','Valor'],[
 ['Índice de llave', '135168'],['Llave DES con paridad',keyhex(135168)],
 ['Modo y relleno','DES-ECB y PKCS#7'],['Tamaño y bloques','2 560 bytes; 320 bloques de 8 bytes'],
 ['Archivo completo','data/key_135168.des; Base64 íntegro en el Anexo B']],[180,315])

# 13.
page('10. Compilación, ejecución y verificación')
P('El ejecutable corregido se construyó con Open MPI 5.0.11, Apple clang 17.0.0 y OpenSSL 3.6.4. El Makefile detecta la instalación Homebrew de OpenSSL; en Linux permite OPENSSL_PREFIX=/usr. La compilación con -Wall -Wextra -Wpedantic finalizó sin advertencias.')
code('''make
bin/bruteforce_mpi selftest

bin/bruteforce_mpi encrypt --text data/texto.txt \\
  --key 135168 --out data/key_135168.des

mpirun --bind-to none -np 4 bin/bruteforce_mpi search \\
  --cipher data/key_135168.des --phrase 'ciencia con paciencia' \\
  --upper 262144 --strategy block --mode early \\
  --batch 128 --repeats 5 --warmups 1 \\
  --out data/recuperado.txt

cmp data/texto.txt data/recuperado.txt
make test
python3 scripts/benchmark.py
python3 scripts/analyze.py''')
H('Pruebas ejecutadas')
table(['Verificación','Resultado'],[
 ['Vector DES de referencia','K=133457799BBCDFF1, P=0123456789ABCDEF, C=85E813540F0AB405. Cifrado y descifrado coinciden.'],
 ['PKCS#7','34 longitudes, de 0 a 33 bytes, incluidas longitudes múltiplo de ocho.'],
 ['Límites de búsqueda','Llaves 0, 3, 4, 7, 9 y 10 en [0,11), con 3 procesos y ambas distribuciones.'],
 ['Casos especiales','Más procesos que llaves; ventanas alrededor de 2^54 y del último índice válido 2^56-1.'],
 ['Terminación y validación','Ausencia de coincidencia termina con código 2; archivo de longitud inválida se rechaza.'],
 ['Recuperación completa','22 comprobaciones del verificador, más validación de las 180 corridas medidas. Todos los archivos recuperados coinciden byte por byte.']],[130,365])
P('Los detalles están en results/tests.log y en los archivos de resultados. La búsqueda no recibe --key: la llave se proporciona únicamente al comando encrypt. El verificador externo conoce la llave para comprobar el resultado, después de medir.',small=True)

# 14.
page('11. Metodología de las mediciones')
table(['Condición','Configuración utilizada'],[
 ['Equipo','Apple M1 Pro; 8 núcleos reportados; 16 GiB de RAM.'],
 ['Sistema',META['platform']],
 ['Entorno paralelo','Un equipo; procesos MPI independientes; --bind-to none; sin fijar afinidad.'],
 ['Espacio principal','[0, 262144) = 2^18 candidatos. DES conserva las 16 rondas y sus 56 bits efectivos.'],
 ['Llaves','8192 (3.125% del rango), 135168 (51.5625%) y 249856 (95.3125%).'],
 ['Configuraciones','3 llaves x 4 cantidades de procesos x 2 distribuciones con parada temprana; más 3 x 4 casos de trabajo fijo con intervalos.'],
 ['Repeticiones','36 casos; 1 calentamiento descartado y 5 corridas medidas por caso: 180 mediciones y 36 calentamientos.'],
 ['Orden y lote','Casos en orden aleatorio reproducible, semilla 20261015; repeticiones consecutivas dentro de cada caso; lotes de 128.']],[125,370])
H('Definición exacta del tiempo')
P('Cada corrida inicia con MPI_Barrier. Cada rank mide una duración local con MPI_Wtime y se toma el máximo mediante MPI_Reduce(MPI_MAX). Así no se comparan marcas absolutas de relojes distintos. El intervalo incluye tryKey y los Allreduce; excluye arranque de mpirun, lectura, cifrado, escritura y recolección posterior de estadísticas. [6]')
code('''media = sum(T_j) / 5
sd = sqrt(sum((T_j - media)^2) / 4)
S_P = media(T_1) / media(T_P)
E_P = 100 * S_P / P
R_P = media(intentos totales) / media(T_P)''')
P('T_1 es el mismo programa corregido con un proceso, para la misma llave, modo y estrategia. sd es la desviación estándar muestral; las barras de error muestran ±sd. En early, S_P se llama aparente porque puede cambiar el trabajo total. En full, se prueban exactamente 262144 candidatos por corrida y se mide escalamiento con trabajo constante.',small=True)
P('No se descartaron valores atípicos de las cinco repeticiones. Las aplicaciones del equipo y el planificador pueden introducir variación; no se afirma aislamiento térmico ni afinidad a un tipo concreto de núcleo.',small=True)

# 15.
page('12. Resultados: intervalos contiguos')
table(['K','P','Media ± sd (s)','S aparente','Intentos totales'],[
 [f'{k:,}',p,f'{get(k,p)["mean_s"]:.4f} ± {get(k,p)["sd_s"]:.4f}',f'{get(k,p)["speedup"]:.2f}',f'{get(k,p)["mean_attempts"]:,.0f}']
 for k in KEYS for p in PS],[75,30,135,95,160])
fig('early_times','Figura 8. Tiempos con parada temprana; media de cinco corridas y barras de ±sd.',maxh=200)
middle=get(135168,2)
P(f'Para K=135168, el tiempo pasa de {get(135168,1)["mean_s"]:.4f} s a {middle["mean_s"]:.4f} s con dos procesos: S={middle["speedup"]:.2f}. La posición local de la llave cae de 135169 intentos a 4097. Ese cambio de trabajo explica el speedup superior al número de procesos.',small=True)
P('Para K=8192, el ganador sigue estando en rank 0 y conserva una posición local de 8193 intentos. Agregar procesos apenas acorta ese recorrido y agrega coordinación. El número total de intentos crece porque también trabajan los otros ranks.',small=True)

# 16.
page('12.1 Resultados: distribución cíclica')
table(['K','P','Media ± sd (s)','S aparente','Intentos totales'],[
 [f'{k:,}',p,f'{get(k,p,"cyclic")["mean_s"]:.4f} ± {get(k,p,"cyclic")["sd_s"]:.4f}',f'{get(k,p,"cyclic")["speedup"]:.2f}',f'{get(k,p,"cyclic")["mean_attempts"]:,.0f}']
 for k in KEYS for p in PS],[75,30,135,95,160])
fig('early_speedups','Figura 9. Speedup por llave. La línea discontinua indica S=P; los dos paneles usan escalas verticales distintas.',maxh=200)
P('En cíclica, la posición local depende de floor(K/P)+1. Se mantiene una exploración aproximadamente ascendente del prefijo del espacio y el total de candidatos queda cerca de K+1, más el excedente del lote. Por eso el resultado es menos sensible a que K coincida con una frontera de intervalo.',small=True)
P('Con K=8192 y ocho procesos, los lotes cortos y los costos de sincronización son una fracción mayor del tiempo. La estrategia cíclica reduce el sesgo de ubicación, pero no elimina la sobrecarga ni garantiza que ocho procesos siempre sean más rápidos.',small=True)

# 17.
page('12.2 Resultados: trabajo fijo')
table(['K','P','Media ± sd (s)','S','E (%)'],[
 [f'{k:,}',p,f'{get(k,p,"block","full")["mean_s"]:.4f} ± {get(k,p,"block","full")["sd_s"]:.4f}',f'{get(k,p,"block","full")["speedup"]:.2f}',f'{get(k,p,"block","full")["efficiency_percent"]:.1f}']
 for k in KEYS for p in PS],[75,30,170,90,130])
fig('full_scaling','Figura 10. Cada corrida prueba 262144 candidatos aunque encuentre antes la llave.',maxh=200)
full4=[get(k,4,'block','full')['speedup'] for k in KEYS]
full8=[get(k,8,'block','full')['speedup'] for k in KEYS]
P(f'Con cuatro procesos, el speedup va de {min(full4):.2f} a {max(full4):.2f}; con ocho, de {min(full8):.2f} a {max(full8):.2f}. Los cambios de posición de llave ya no alteran el número de intentos. Las diferencias restantes se deben a los tiempos observados de cálculo, espera y ejecución del sistema.',small=True)
P('La saturación entre cuatro y ocho procesos muestra el límite práctico en este equipo y con este lote. El experimento por sí solo no permite atribuirla exclusivamente a la red, la caché, la temperatura o un tipo de núcleo.',small=True)

# 18.
page('12.3 Trabajo y espera de cada proceso')
rankrows=list(csv.DictReader(open(ROOT/'results/k249856_p8_block_full_ranks.csv')))
rankstats=[]
for p in range(8):
    samples=[r for r in rankrows if int(r['rank'])==p]
    rankstats.append((p,st.mean(int(r['attempts']) for r in samples),st.mean(float(r['compute_s']) for r in samples),st.mean(float(r['sync_s']) for r in samples)))
table(['Rank','Intentos','Cálculo medio (s)','Allreduce medio (s)'],[
 [p,f'{n:,.0f}',f'{c:.4f}',f'{s:.4f}'] for p,n,c,s in rankstats],[50,100,170,175])
fig('rank_times','Figura 11. Caso K=249856, P=8, modo full; medias de cinco corridas.',maxh=210)
P('Todos reciben 32768 candidatos. La diferencia de cantidades es cero, pero el tiempo de cálculo varía entre ranks. Los procesos que completan antes un lote pasan más tiempo dentro del colectivo esperando al resto. El tiempo de Allreduce incluye comunicación, espera y posibles pausas del planificador; no es una medición pura de latencia de red.')
P('La suma de cálculo y Allreduce por rank se aproxima a su duración local. Las pequeñas diferencias corresponden al control del ciclo y a llamadas del cronómetro. No se suman las duraciones de todos los procesos para obtener T_P: se usa el máximo.',small=True)
H('Consistencia al cambiar la llave')
for p in [1,4,8]:
    means=[get(k,p,'block','full')['mean_s'] for k in KEYS]
    spread=100*(max(means)-min(means))/st.mean(means)
    P(f'P={p}: las medias con las tres llaves abarcan {min(means):.4f} a {max(means):.4f} s; amplitud relativa respecto a su media: {spread:.2f}%.',small=True)

# 19.
page('13. Por qué unas llaves aparecen antes')
P('<b>La magnitud numérica de una llave no hace más costoso descifrar un bloque DES.</b> El costo cambia principalmente por cuántos candidatos se prueban antes de llegar a ella, por el reparto y por el tiempo hasta comunicar el hallazgo. Con longitud y algoritmo fijos, el trabajo de una prueba sigue siendo esencialmente el mismo.')
table(['Estrategia','P','Rank ganador','Posición local de K=135168'],[
 [s,p,get(135168,p,s)['winner'],f'{(135168 % (262144//p)+1) if s=="block" else (135168//p+1):,}']
 for s in ['block','cyclic'] for p in [1,2,4,8]],[120,35,110,230])
H('Interpretación del speedup aparente')
P('En intervalos, K=135168 está 4096 posiciones después del inicio 131072 para P=2, 4 y 8. Todos esos casos tienen la misma profundidad local de 4097 candidatos. El tiempo no se divide nuevamente entre dos al duplicar P; incluso puede aumentar por espera. Una eficiencia aparente superior al 100% refleja una búsqueda diferente, no capacidad de cómputo creada por MPI.')
P('En cambio, K=249856 conserva un recorrido largo dentro de su rango y muestra aceleraciones más moderadas. K=8192 es un caso desfavorable para intervalos porque no se reparte el prefijo que debe recorrer rank 0. Seleccionar únicamente la llave central daría una conclusión sesgada.')
H('Si la llave fuera uniforme en todo el rango')
P('Sin considerar lotes y suponiendo tasas iguales, la profundidad esperada del ganador es aproximadamente W/(2P) tanto con intervalos como con cíclica. Sin embargo, para una misma llave individual, los intervalos pueden presentar saltos bruscos al cambiar P. Tres llaves ilustran este mecanismo; no estiman por sí solas el rendimiento promedio de todas las llaves posibles.',small=True)
P('El modo full mantiene el trabajo total y responde a otra pregunta: cuánto acelera MPI una carga fija. Ambos experimentos son útiles, siempre que se informe qué se está comparando.',small=True)

# 20.
page('14. Alcance y conclusiones')
H('Lo demostrado con las mediciones')
P('La implementación cifra todo el mensaje y recupera sus bytes originales mediante búsqueda de candidatos. Los rangos tienen cobertura completa, las dos distribuciones terminan colectivamente y el caso sin coincidencia está probado. La búsqueda acepta cualquier índice DES válido y límites hasta 2^56.')
P('La distribución por intervalos produce resultados muy sensibles a la ubicación de K. La cíclica reduce esa sensibilidad en búsquedas desde un límite conocido. El experimento de trabajo fijo permite evaluar el escalamiento sin atribuir a MPI el beneficio de una llave favorable.')
H('Demostración adicional en el espacio de 56 bits')
demo_path=ROOT/'results/full56_demo.jsonl'
if demo_path.exists():
    demo=[json.loads(x) for x in demo_path.read_text().splitlines()]
    dm=st.mean(r['seconds'] for r in demo)
    ds=st.stdev(r['seconds'] for r in demo)
    P(f'También se cifró el mensaje con la llave del archivo base, K=18014398509481984=2^54, y se buscó con P=4 sobre [0,2^56). En cinco corridas, rank 1 encontró esa llave con media {dm:.6f} ± {ds:.6f} s y {demo[0]["attempts"]} intentos totales por corrida. El resultado es posible porque la llave ocupa la primera posición de su rango; no representa explorar todo DES.')
else:
    raise RuntimeError('Falta ejecutar la demostracion de espacio completo')
H('Límites de lo que se puede concluir')
P('Las 180 mediciones principales utilizan 2^18 candidatos. No se recorrieron exhaustivamente las 2^56 llaves. Los ensayos de llaves grandes prueban direccionamiento y parada temprana en posiciones conocidas; no demuestran un tiempo práctico para romper una llave arbitraria de 56 bits.')
rate=st.mean(get(k,1,'block','full')['throughput_keys_s'] for k in KEYS)
years=((1<<56)/rate)/(365.25*24*3600)
P(f'La tasa secuencial media en full fue aproximadamente {rate:,.0f} candidatos/s. Mantenerla sobre 2^56 candidatos daría unos {years:,.0f} años para el peor caso y la mitad en promedio bajo una llave uniforme. Es una extrapolación lineal orientativa del programa, no un resultado medido ni una estimación de hardware especializado.',small=True)
P('Los procesos se ejecutaron en una sola máquina. Para generalizar a memoria distribuida entre máquinas faltaría repetir la matriz con una red real, documentar latencias, arquitectura de cada nodo y política de afinidad, y ampliar el muestreo de llaves. El código emplea tipos MPI de ancho explícito y envía bytes del criptograma para favorecer portabilidad.',small=True)

# 21.
page('Referencias y trazabilidad')
refs=[
 ('1','National Institute of Standards and Technology. (1999). FIPS PUB 46-3: Data Encryption Standard. Especificación de DES y tablas; publicación archivada.','https://csrc.nist.gov/files/pubs/fips/46-3/final/docs/fips46-3.pdf'),
 ('2','OpenSSL Project. DES_random_key y funciones DES. Documentación de OpenSSL 3.6: bloques, paridad, calendario y estado de obsolescencia.','https://docs.openssl.org/3.6/man3/DES_random_key/'),
 ('3','Housley, R. (2009). RFC 5652, sección 6.3. Regla de relleno de contenido usada para PKCS#7.','https://www.rfc-editor.org/rfc/rfc5652#section-6.3'),
 ('4','ISO/IEC JTC1/SC22/WG14. (2011). Borrador público N1570 de C11, §§7.24.2.1 y 7.24.5.7: memcpy y strstr.','https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf'),
 ('5','Open MPI. MPI_Allreduce. Combinación de valores y distribución del resultado entre procesos.','https://docs.open-mpi.org/en/main/man-openmpi/man3/MPI_Allreduce.3.html'),
 ('6','Open MPI. MPI_Wtime. Duraciones locales, unidades y limitaciones de sincronización de relojes.','https://docs.open-mpi.org/en/main/man-openmpi/man3/MPI_Wtime.3.html'),
 ('7','NIST. (2005). Anuncio de retiro de FIPS 46-3. Contexto histórico del uso de DES.','https://csrc.nist.gov/news/2005/withdrawal-of-fips-46-3-fips-74-and-fips-81'),
]
for n,desc,url in refs:
    P(f'<b>[{n}]</b> {desc}<br/><link href="{url}" color="#007f78">Consultar fuente oficial</link>')
P('Fuentes consultadas el 15 de octubre de 2026. Se usaron fuentes primarias para las especificaciones técnicas. Los diagramas y el análisis de resultados son elaboración propia.',small=True)
H('Material y evidencia local')
P('Archivo base entregado: original/bruteforce_.c. Implementación: src/bruteforce_mpi.c. Datos experimentales: results/raw.jsonl; tabla derivada: results/summary.csv; datos por proceso: results/*_ranks.csv; entorno: results/metadata.json. Cada comando exacto se guarda en results/commands.jsonl.',small=True)
P('SHA-256 del texto UTF-8:<br/><font name="Courier" size="7.4">'+META['text_sha256']+'</font>',small=True)
P('El paquete incluye el código, el texto, los criptogramas, las recuperaciones, los comandos, los diagramas editables y los scripts para volver a producir las tablas y el informe. Los datos medidos corresponden al entorno documentado; una nueva ejecución puede producir tiempos distintos.',small=True)

# 22.
page('Anexo A. Las cinco repeticiones de cada caso')
P('Tiempos en segundos, redondeados a cuatro decimales. El promedio y la sd se calcularon con los valores completos de results/raw.jsonl. C=intervalos contiguos; R=cíclica; E=parada temprana; F=trabajo fijo.',small=True)
data=[]
for r in SUMMARY:
    sample=sorted([x for x in RAW if x['key']==r['key'] and x['processes']==r['processes'] and x['strategy']==r['strategy'] and x['mode']==r['mode']],key=lambda x:x['trial'])
    tag=('C' if r['strategy']=='block' else 'R')+('E' if r['mode']=='early' else 'F')
    data.append([f'{r["key"]}',str(r['processes'])+' '+tag]+[f'{x["seconds"]:.4f}' for x in sample])
table(['K','P / tipo','T1','T2','T3','T4','T5'],data,[65,65,73,73,73,73,73],compact=True)

# 23.
page('Anexo B. Criptograma completo en Base64')
cipher=(ROOT/'data/key_135168.des').read_bytes()
P('Representación completa de data/key_135168.des, cifrado con índice K=135168. Base64 es solo una codificación para mostrar los bytes; no es el método de cifrado. Al decodificar se obtienen exactamente 2560 bytes.')
P('SHA-256 del criptograma:<br/><font name="Courier" size="7.4">'+hashlib.sha256(cipher).hexdigest()+'</font>',small=True)
code('\n'.join(textwrap.wrap(base64.b64encode(cipher).decode(),76)),small=True)
P('El archivo binario está incluido en el paquete. Para comprobar el descifrado, ejecutar el comando search de la sección 10 y comparar el archivo recuperado con data/texto.txt. El ciphertext no almacena la llave ni el texto plano.',small=True)

def decorate(canvas,doc):
    canvas.saveState()
    w,h=A4
    if doc.page>1:
        canvas.setFont('Arial-Bold',8)
        canvas.setFillColor(TEAL)
        canvas.drawString(50,h-31,'DES + MPI')
        canvas.setFont('Arial',8)
        canvas.setFillColor(INK)
        canvas.drawRightString(w-50,h-31,'Proyecto 2 · Computación Paralela')
        canvas.setStrokeColor(colors.HexColor('#d4e1e5'))
        canvas.line(50,h-39,w-50,h-39)
    canvas.setStrokeColor(colors.HexColor('#d4e1e5'))
    canvas.line(50,40,w-50,40)
    canvas.setFont('Arial',7.5);canvas.setFillColor(INK)
    canvas.drawString(50,27,'Datos experimentales y código reproducible · 15/10/2026')
    canvas.drawRightString(w-50,27,str(doc.page))
    canvas.restoreState()

doc=SimpleDocTemplate(str(OUT/'Informe_Proyecto2_DES_MPI.pdf'),pagesize=A4,
    rightMargin=50,leftMargin=50,topMargin=55,bottomMargin=53,
    title='Proyecto 2 - Busqueda exhaustiva de llaves DES con Open MPI',
    author='Equipo de Proyecto 2',subject='DES, MPI, speedup y posicion de llaves')
doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
(ROOT/'informe_fuente.md').write_text('\n'.join(md))
(ROOT/'results/report_expected_pages.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2))
print(f'Informe generado: {len(expected)} paginas previstas.')
