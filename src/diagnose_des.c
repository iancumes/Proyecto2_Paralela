/* Diagnostico DES-ECB de interoperabilidad, separado del benchmark MPI.
 * Una frase >=15 bytes contiene un bloque entero para cualquier alineacion.
 * Se cifran sus ocho posibles bloques iniciales y se busca el resultado en
 * los bloques del criptograma; solo ante coincidencia se descifra completo.
 * No necesita suponer el relleno para localizar la frase. */
#define OPENSSL_SUPPRESS_DEPRECATED
#include <openssl/des.h>
#include <stdint.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>

static uint64_t *blocks;
static size_t nblocks, length, phrase_len;
static unsigned char *cipher;
static const char *phrase;
static int found;
static uint64_t winner;
static int winner_format;
static const char *names[] = {"big7", "little7", "rawbe", "rawle"};

static int compare(const void *a, const void *b) {
    uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
    return (x > y) - (x < y);
}
static void keybytes(uint64_t value, int format, DES_cblock *bytes) {
    for (unsigned i = 0; i < 8; ++i) {
        unsigned pos = format == 0 || format == 2 ? 7-i : i;
        (*bytes)[pos] = format < 2 ? (unsigned char)(((value >> (7*i)) & 127) << 1)
                                           : (unsigned char)(value >> (8*i));
    }
    DES_set_odd_parity(bytes);
}
static int check(uint64_t value, int format) {
    DES_cblock bytes;
    DES_key_schedule schedule;
    keybytes(value, format, &bytes);
    DES_set_key_unchecked(&bytes, &schedule);
    for (unsigned offset = 0; offset < 8; ++offset) {
        DES_cblock input, output;
        memcpy(input, phrase+offset, 8);
        DES_ecb_encrypt(&input, &output, &schedule, DES_ENCRYPT);
        uint64_t block;
        memcpy(&block, output, 8);
        if (!bsearch(&block, blocks, nblocks, sizeof(uint64_t), compare)) continue;
        unsigned char *plain = malloc(length+1);
        if (!plain) exit(1);
        for (size_t j = 0; j < length; j += 8) {
            memcpy(input, cipher+j, 8);
            DES_ecb_encrypt(&input, &output, &schedule, DES_DECRYPT);
            memcpy(plain+j, output, 8);
        }
        int matched = 0;
        for (size_t j = 0; j+phrase_len <= length; ++j)
            if (!memcmp(plain+j, phrase, phrase_len)) { matched = 1; break; }
        free(plain);
        if (matched) return 1;
    }
    return 0;
}
int main(int argc, char **argv) {
    if (argc != 6) {
        fprintf(stderr, "Uso: diagnose_des CIPHER PHRASE LOWER UPPER OUT\n");
        return 1;
    }
    phrase = argv[2]; phrase_len = strlen(phrase);
    if (phrase_len < 15) { fputs("La frase necesita >=15 bytes\n", stderr); return 1; }
    uint64_t lower = strtoull(argv[3], NULL, 0), upper = strtoull(argv[4], NULL, 0);
    if (lower >= upper || upper > (UINT64_C(1)<<56)) return 1;
    FILE *f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END); long size = ftell(f); rewind(f);
    if (size <= 0 || size % 8) { fclose(f); return 1; }
    length = (size_t)size; nblocks = length/8;
    cipher = malloc(length); blocks = malloc(length);
    if (!cipher || !blocks) return 1;
    if (fread(cipher, 1, length, f) != length) return 1;
    fclose(f); memcpy(blocks, cipher, length);
    qsort(blocks, nblocks, sizeof(uint64_t), compare);
    const uint64_t common[] = {0,1,8192,135168,249856,123456,1234567,12345678,
        123456789,1234567890,2026,23236,UINT64_C(1)<<54,(UINT64_C(1)<<56)-1};
    double start = omp_get_wtime();
    for (int format = 0; format < 4 && !found; ++format) {
        for (unsigned i = 0; i < sizeof(common)/sizeof(common[0]) && !found; ++i) {
            if (check(common[i], format)) { found = 1; winner=common[i]; winner_format=format; }
        }
    }
    for (int format = 0; format < 4 && !found; ++format) {
        fprintf(stderr, "Explorando %s [ %" PRIu64 ", %" PRIu64 " )\n", names[format], lower, upper);
        #pragma omp parallel for schedule(static)
        for (uint64_t value = lower; value < upper; ++value) {
            int done;
            #pragma omp atomic read
            done = found;
            if (done || !check(value, format)) continue;
            #pragma omp critical
            {
                if (!found) { winner=value; winner_format=format; }
                #pragma omp atomic write
                found = 1;
            }
        }
    }
    if (!found) {
        printf("{\"found\":null,\"lower\":%" PRIu64 ",\"upper\":%" PRIu64 ",\"seconds\":%.9f}\n", lower, upper, omp_get_wtime()-start);
        free(cipher); free(blocks); return 2;
    }
    DES_cblock bytes; DES_key_schedule schedule;
    keybytes(winner, winner_format, &bytes);
    DES_set_key_unchecked(&bytes, &schedule);
    unsigned char *plain = malloc(length);
    if (!plain) return 1;
    for (size_t j=0; j<length; j+=8) {
        DES_cblock in, out; memcpy(in, cipher+j, 8);
        DES_ecb_encrypt(&in, &out, &schedule, DES_DECRYPT); memcpy(plain+j,out,8);
    }
    size_t usable = length; const char *padding="none_or_other";
    unsigned pad=plain[length-1];
    if (pad>=1 && pad<=8) {
        int ok=1; for (unsigned j=0;j<pad;++j) if(plain[length-1-j]!=pad)ok=0;
        if(ok){usable-=pad;padding="pkcs7";}
    }
    if(usable==length && plain[length-1]==0){while(usable && plain[usable-1]==0)--usable;padding="zero";}
    f=fopen(argv[5],"wb"); if(!f)return 1;
    if(fwrite(plain,1,usable,f)!=usable)return 1;
    fclose(f);
    printf("{\"found\":%" PRIu64 ",\"key_format\":\"%s\",\"padding\":\"%s\",\"plain_bytes\":%zu,\"seconds\":%.9f,\"key_hex\":\"",winner,names[winner_format],padding,usable,omp_get_wtime()-start);
    for(int i=0;i<8;++i)printf("%02x",bytes[i]);
    puts("\"}");
    free(cipher);free(blocks);free(plain);return 0;
}
