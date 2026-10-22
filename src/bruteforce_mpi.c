/* Proyecto 2: DES-ECB didactico y busqueda exhaustiva con Open MPI.
 * La busqueda SOLO recibe el criptograma y una frase, nunca la llave real.
 * Las API DES de bajo nivel estan obsoletas en OpenSSL 3; se usan para
 * reproducir este ejercicio, sin configurar proveedores globales.
 */
#define OPENSSL_SUPPRESS_DEPRECATED
#include <openssl/des.h>
#include <mpi.h>
#include <stdint.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <limits.h>

#define KEYSPACE (UINT64_C(1) << 56)
#define NO_KEY UINT64_MAX

static int rank_id;
static int use_pkcs7 = 1;
static void die(const char *message) {
    fprintf(stderr, "rank %d: %s\n", rank_id, message);
    MPI_Abort(MPI_COMM_WORLD, 1);
    exit(1);
}
static void *allocate(size_t n) {
    void *p = malloc(n ? n : 1);
    if (!p) die("memoria insuficiente");
    return p;
}
static uint64_t number(const char *s) {
    char *end = NULL;
    errno = 0;
    if (!s || s[0] == '-') die("numero invalido");
    unsigned long long x = strtoull(s, &end, 0);
    if (errno || end == s || *end) die("numero invalido");
    return (uint64_t)x;
}
static unsigned char *read_file(const char *path, size_t *len) {
    FILE *f = fopen(path, "rb");
    if (!f) die("no se pudo abrir archivo de entrada");
    if (fseek(f, 0, SEEK_END)) die("fseek fallo");
    long n = ftell(f);
    if (n < 0 || n > INT_MAX - 16) die("archivo demasiado grande");
    rewind(f);
    unsigned char *p = allocate((size_t)n + 9);
    if (fread(p, 1, (size_t)n, f) != (size_t)n) die("lectura incompleta");
    fclose(f);
    *len = (size_t)n;
    p[n] = 0;
    return p;
}
static void write_file(const char *path, const unsigned char *data, size_t len) {
    FILE *f = fopen(path, "wb");
    if (!f || fwrite(data, 1, len, f) != len) die("escritura fallo");
    if (fclose(f)) die("cierre de archivo fallo");
}

/* Enumera los 56 bits de datos en orden big-endian, en grupos de 7.
 * El bit menos significativo de cada byte se reserva para paridad impar.
 * El resultado no depende del endian de la CPU ni del tamano de long.
 */
static void key_bytes(uint64_t key, DES_cblock *out) {
    for (unsigned i = 0; i < 8; ++i)
        (*out)[7 - i] = (unsigned char)(((key >> (7 * i)) & 0x7f) << 1);
    DES_set_odd_parity(out);
}
static void crypt_buffer(uint64_t key, unsigned char *data, size_t len, int mode) {
    if (key >= KEYSPACE || len % 8) die("llave o longitud DES invalida");
    DES_cblock bytes;
    DES_key_schedule schedule;
    key_bytes(key, &bytes);
    /* No se descartan llaves debiles: la enumeracion debe cubrirlas tambien. */
    DES_set_key_unchecked(&bytes, &schedule);
    for (size_t pos = 0; pos < len; pos += 8) {
        DES_cblock input, output;
        memcpy(input, data + pos, 8);
        DES_ecb_encrypt(&input, &output, &schedule, mode);
        memcpy(data + pos, output, 8);
    }
}
static void encrypt(uint64_t key, unsigned char *data, size_t len) {
    crypt_buffer(key, data, len, DES_ENCRYPT);
}
static void decrypt(uint64_t key, unsigned char *data, size_t len) {
    crypt_buffer(key, data, len, DES_DECRYPT);
}
/* PKCS#7 agrega siempre de 1 a 8 bytes, todos con el valor del relleno. */
static int unpad(const unsigned char *data, size_t len, size_t *plain_len) {
    if (!len || len % 8) return 0;
    unsigned pad = data[len - 1];
    if (pad < 1 || pad > 8 || pad > len) return 0;
    for (unsigned j = 0; j < pad; ++j)
        if (data[len - 1 - j] != pad) return 0;
    *plain_len = len - pad;
    return 1;
}
static int plain_length(const unsigned char *data, size_t len, size_t *plain_len) {
    if (use_pkcs7) return unpad(data, len, plain_len);
    *plain_len = len;
    return 1;
}
/* scratch se reserva una sola vez por proceso: len+1 bytes.
 * Se descifra TODO el texto para cada candidato, igual en todas las pruebas.
 */
static int tryKey(uint64_t key, const unsigned char *cipher, size_t len,
                  const char *phrase, unsigned char *scratch) {
    memcpy(scratch, cipher, len);
    decrypt(key, scratch, len);
    size_t plain_len;
    if (!plain_length(scratch, len, &plain_len)) return 0;
    scratch[plain_len] = 0;
    return strstr((char *)scratch, phrase) != NULL;
}
static void selftest(void) {
    DES_cblock known_key = {0x13,0x34,0x57,0x79,0x9b,0xbc,0xdf,0xf1};
    unsigned char plain[8] = {0x01,0x23,0x45,0x67,0x89,0xab,0xcd,0xef};
    unsigned char expected[8] = {0x85,0xe8,0x13,0x54,0x0f,0x0a,0xb4,0x05};
    unsigned char buffer[8];
    uint64_t index = 0;
    for (int i = 0; i < 8; ++i) index = (index << 7) | (known_key[i] >> 1);
    memcpy(buffer, plain, 8);
    encrypt(index, buffer, 8);
    if (memcmp(buffer, expected, 8)) die("vector DES conocido fallo");
    decrypt(index, buffer, 8);
    if (memcmp(buffer, plain, 8)) die("ida y vuelta DES fallo");
    for (size_t n = 0; n <= 33; ++n) {
        unsigned char temp[48];
        memset(temp, 'a', n);
        unsigned pad = 8 - n % 8;
        memset(temp + n, pad, pad);
        size_t recovered;
        encrypt(KEYSPACE - 1, temp, n + pad);
        decrypt(KEYSPACE - 1, temp, n + pad);
        if (!unpad(temp, n + pad, &recovered) || recovered != n)
            die("prueba PKCS#7 fallo");
    }
    if (!rank_id) puts("SELFTEST OK: vector DES y 34 longitudes PKCS#7");
}
static void usage(void) {
    if (!rank_id) {
        puts("Uso:\n"
             "  bruteforce_mpi selftest\n"
             "  bruteforce_mpi encrypt --text FILE --key K --out FILE\n"
             "  mpirun -np P bruteforce_mpi search --cipher FILE --phrase TEXT\n"
             "    [--lower 0] [--upper 72057594037927936] [--strategy block|cyclic]\n"
             "    [--mode early|full] [--batch 128] [--repeats 1] [--warmups 0]\n"
             "    [--stats PREFIX] [--out RECOVERED]\n"
             "    [--padding pkcs7|none] (predeterminado: pkcs7)\n"
             "upper es EXCLUSIVO. full continua despues de encontrar la llave.\n"
             "stdout contiene una linea JSON por repeticion medida.");
    }
}
int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int processes;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank_id);
    MPI_Comm_size(MPI_COMM_WORLD, &processes);
    if (argc < 2) { usage(); MPI_Finalize(); return 1; }
    if (!strcmp(argv[1], "selftest")) { selftest(); MPI_Finalize(); return 0; }
    const char *text_path = NULL, *cipher_path = NULL, *out_path = NULL;
    const char *phrase = NULL, *stats = NULL, *strategy = "block", *mode = "early";
    uint64_t key = NO_KEY, lower = 0, upper = KEYSPACE, batch = 128;
    int repeats = 1, warmups = 0;
    for (int a = 2; a < argc; a += 2) {
        if (a + 1 >= argc) die("falta valor de opcion");
        const char *v = argv[a + 1];
        if (!strcmp(argv[a], "--text")) text_path = v;
        else if (!strcmp(argv[a], "--cipher")) cipher_path = v;
        else if (!strcmp(argv[a], "--out")) out_path = v;
        else if (!strcmp(argv[a], "--key")) key = number(v);
        else if (!strcmp(argv[a], "--phrase")) phrase = v;
        else if (!strcmp(argv[a], "--lower")) lower = number(v);
        else if (!strcmp(argv[a], "--upper")) upper = number(v);
        else if (!strcmp(argv[a], "--batch")) batch = number(v);
        else if (!strcmp(argv[a], "--repeats")) { uint64_t x = number(v); if (x > 10000) die("repeticiones excesivas"); repeats = (int)x; }
        else if (!strcmp(argv[a], "--warmups")) { uint64_t x = number(v); if (x > 10000) die("calentamientos excesivos"); warmups = (int)x; }
        else if (!strcmp(argv[a], "--stats")) stats = v;
        else if (!strcmp(argv[a], "--strategy")) strategy = v;
        else if (!strcmp(argv[a], "--mode")) mode = v;
        else if (!strcmp(argv[a], "--padding")) {
            if (!strcmp(v, "pkcs7")) use_pkcs7 = 1;
            else if (!strcmp(v, "none")) use_pkcs7 = 0;
            else die("relleno invalido");
        }
        else die("opcion desconocida");
    }
    if (!strcmp(argv[1], "encrypt")) {
        if (!text_path || !out_path || key >= KEYSPACE) die("faltan texto, salida o llave valida");
        if (!rank_id) {
            size_t len;
            unsigned char *buffer = read_file(text_path, &len);
            if (memchr(buffer, 0, len)) die("el texto contiene NUL interno");
            if (!use_pkcs7 && len % 8) die("sin relleno el texto debe ser multiplo de ocho");
            unsigned pad = use_pkcs7 ? 8 - len % 8 : 0;
            memset(buffer + len, pad, pad);
            encrypt(key, buffer, len + pad);
            write_file(out_path, buffer, len + pad);
            DES_cblock bytes;
            key_bytes(key, &bytes);
            printf("ENCRYPT OK plain_bytes=%zu cipher_bytes=%zu key_index=%" PRIu64 " key_hex=", len, len + pad, key);
            for (int i = 0; i < 8; ++i) printf("%02x", bytes[i]);
            puts("");
            free(buffer);
        }
        MPI_Finalize(); return 0;
    }
    if (strcmp(argv[1], "search")) die("comando desconocido");
    if (!cipher_path || !phrase || !phrase[0]) die("faltan criptograma o frase no vacia");
    if (key != NO_KEY) die("search no acepta la llave verdadera");
    if (lower >= upper || upper > KEYSPACE || !batch || repeats < 1) die("rango, lote o repeticiones invalidos");
    int cyclic = !strcmp(strategy, "cyclic"), full = !strcmp(mode, "full");
    if ((!cyclic && strcmp(strategy, "block")) || (!full && strcmp(mode, "early"))) die("estrategia o modo invalido");

    size_t len = 0;
    unsigned char *cipher = NULL;
    if (!rank_id) cipher = read_file(cipher_path, &len);
    uint64_t wire_len = len;
    MPI_Bcast(&wire_len, 1, MPI_UINT64_T, 0, MPI_COMM_WORLD);
    len = (size_t)wire_len;
    if (!len || len % 8 || len > INT_MAX) die("criptograma vacio o longitud no multiplo de ocho");
    if (rank_id) cipher = allocate(len + 1);
    MPI_Bcast(cipher, (int)len, MPI_UNSIGNED_CHAR, 0, MPI_COMM_WORLD);
    unsigned char *scratch = allocate(len + 1);

    uint64_t width = upper - lower;
    uint64_t q = width / (uint64_t)processes, rem = width % (uint64_t)processes;
    uint64_t r = (uint64_t)rank_id;
    uint64_t start = cyclic ? lower + r : lower + r * q + (r < rem ? r : rem);
    uint64_t count = cyclic ? (r < width ? 1 + (width - 1 - r) / (uint64_t)processes : 0)
                            : q + (r < rem);
    uint64_t stride = cyclic ? (uint64_t)processes : 1;
    uint64_t max_count = q + (rem != 0);
    uint64_t rounds = max_count / batch + (max_count % batch != 0);
    uint64_t *all_attempts = !rank_id ? allocate((size_t)processes * sizeof(uint64_t)) : NULL;
    double *all_times = !rank_id ? allocate((size_t)processes * 3 * sizeof(double)) : NULL;
    FILE *rank_csv = NULL;
    if (!rank_id && stats) {
        char path[4096];
        if (snprintf(path, sizeof path, "%s_ranks.csv", stats) >= (int)sizeof path) die("ruta muy larga");
        rank_csv = fopen(path, "w");
        if (!rank_csv) die("no se pudo abrir CSV");
        fputs("trial,rank,attempts,elapsed_s,compute_s,sync_s,start,count,stride\n", rank_csv);
    }
    int any_failure = 0;
    for (int trial = -warmups; trial < repeats; ++trial) {
        uint64_t attempted = 0, local_found = NO_KEY, found = NO_KEY;
        double compute = 0, sync = 0;
        MPI_Barrier(MPI_COMM_WORLD);
        double t0 = MPI_Wtime();
        for (uint64_t round = 0; round < rounds; ++round) {
            uint64_t begin = round * batch;
            uint64_t end = begin < count && count - begin < batch ? count : begin + batch;
            if (end > count) end = count;
            double c0 = MPI_Wtime();
            for (uint64_t j = begin; j < end; ++j) {
                uint64_t candidate = start + j * stride;
                ++attempted;
                if (tryKey(candidate, cipher, len, phrase, scratch)) {
                    if (candidate < local_found) local_found = candidate;
                    if (!full) break;
                }
            }
            compute += MPI_Wtime() - c0;
            double s0 = MPI_Wtime();
            MPI_Allreduce(&local_found, &found, 1, MPI_UINT64_T, MPI_MIN, MPI_COMM_WORLD);
            sync += MPI_Wtime() - s0;
            if (!full && found != NO_KEY) break;
        }
        double elapsed = MPI_Wtime() - t0, global_elapsed;
        MPI_Reduce(&elapsed, &global_elapsed, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
        uint64_t total_attempts;
        MPI_Reduce(&attempted, &total_attempts, 1, MPI_UINT64_T, MPI_SUM, 0, MPI_COMM_WORLD);
        int local_winner = local_found == found && found != NO_KEY ? rank_id : INT_MAX, winner;
        MPI_Reduce(&local_winner, &winner, 1, MPI_INT, MPI_MIN, 0, MPI_COMM_WORLD);
        MPI_Gather(&attempted, 1, MPI_UINT64_T, all_attempts, 1, MPI_UINT64_T, 0, MPI_COMM_WORLD);
        double local_times[3] = {elapsed, compute, sync};
        MPI_Gather(local_times, 3, MPI_DOUBLE, all_times, 3, MPI_DOUBLE, 0, MPI_COMM_WORLD);
        if (found == NO_KEY) any_failure = 1;
        if (!rank_id && trial >= 0) {
            printf("{\"trial\":%d,\"processes\":%d,\"strategy\":\"%s\",\"mode\":\"%s\",\"lower\":%" PRIu64 ",\"upper\":%" PRIu64 ",\"batch\":%" PRIu64 ",\"seconds\":%.9f,\"attempts\":%" PRIu64 ",\"found\":", trial, processes, strategy, mode, lower, upper, batch, global_elapsed, total_attempts);
            if (found == NO_KEY) printf("null,\"winner\":null,\"padding\":\"%s\"}\n", use_pkcs7 ? "pkcs7" : "none");
            else printf("%" PRIu64 ",\"winner\":%d,\"padding\":\"%s\"}\n", found, winner, use_pkcs7 ? "pkcs7" : "none");
            fflush(stdout);
            if (rank_csv) for (int node = 0; node < processes; ++node) {
                uint64_t n = (uint64_t)node;
                uint64_t ns = cyclic ? lower + n : lower + n * q + (n < rem ? n : rem);
                uint64_t nc = cyclic ? (n < width ? 1 + (width - 1 - n) / (uint64_t)processes : 0) : q + (n < rem);
                fprintf(rank_csv, "%d,%d,%" PRIu64 ",%.9f,%.9f,%.9f,%" PRIu64 ",%" PRIu64 ",%" PRIu64 "\n", trial, node, all_attempts[node], all_times[3*node], all_times[3*node+1], all_times[3*node+2], ns, nc, stride);
            }
        }
        if (!rank_id && trial == repeats - 1 && out_path && found != NO_KEY) {
            memcpy(scratch, cipher, len);
            decrypt(found, scratch, len);
            size_t plain_len;
            if (!plain_length(scratch, len, &plain_len)) die("relleno final invalido");
            write_file(out_path, scratch, plain_len);
        }
    }
    if (rank_csv) fclose(rank_csv);
    free(cipher); free(scratch); free(all_attempts); free(all_times);
    MPI_Finalize();
    return any_failure ? 2 : 0;
}
