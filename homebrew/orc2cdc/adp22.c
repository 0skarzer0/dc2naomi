/* adp22.c ENTRADA.ADP SALIDA.A22 : una pista de musica de ORC2CDC (ADPCM de Yamaha del AICA, estereo intercalado por
 * nibbles: nibble bajo = derecho, alto = izquierdo; como la escribe tools/c/musica.c de ORC2CDC) a la mitad de
 * muestras, para sonar a 22050 Hz en vez de 44100 con el mismo tono (comun/musica.c busca MUSn.A22 antes que
 * MUSn.ADP). Decodifica como el AICA (el mismo paso y la misma senal que el codificador de musica.c), filtra
 * paso bajo (FIR de 63 tomas, ventana de Blackman, corte a 0,45 de la frecuencia nueva), diezma 2:1 y vuelve a
 * codificar con el codificador de musica.c. Para que el juego quepa en la NetDIMM de 512 MB (dc2naomi, HANDOFF).
 * gcc -O2 -o adp22 adp22.c -lm */
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static const int DIF[16] = { 1, 3, 5, 7, 9, 11, 13, 15, -1, -3, -5, -7, -9, -11, -13, -15 };
static const int ESC[8] = { 0x0e6, 0x0e6, 0x0e6, 0x0e6, 0x133, 0x199, 0x200, 0x266 };
typedef struct { int senal, paso; } yam_t;
static void yam_paso(yam_t *e, int v)
{
    e->senal += e->paso * DIF[v] / 8;
    if (e->senal > 32767) e->senal = 32767;
    if (e->senal < -32768) e->senal = -32768;
    e->paso = e->paso * ESC[v & 7] >> 8;
    if (e->paso < 0x7f) e->paso = 0x7f;
    if (e->paso > 0x6000) e->paso = 0x6000;
}
static int yam_cod(yam_t *e, int x)             /* = yam_cod de tools/c/musica.c */
{
    int d = x - e->senal, v;
    d = d * 8 / e->paso;
    v = abs(d) / 2;
    if (v > 7) v = 7;
    if (d < 0) v += 8;
    yam_paso(e, v);
    return v;
}

#define NT 63
int main(int argc, char **argv)
{
    FILE *f; long n, i, m; uint8_t *d, *o; float *ch[2]; double h[NT], s = 0; int c;
    yam_t e[2] = { { 0, 0x7f }, { 0, 0x7f } };
    if (argc < 3) { fprintf(stderr, "uso: adp22 entrada.adp salida.a22\n"); return 2; }
    if (!(f = fopen(argv[1], "rb"))) { perror(argv[1]); return 1; }
    fseek(f, 0, SEEK_END); n = ftell(f); fseek(f, 0, SEEK_SET);
    d = malloc(n); if (fread(d, 1, n, f) != (size_t)n) return 1; fclose(f);
    for (c = 0; c < 2; c++) ch[c] = malloc(sizeof(float) * n);
    for (i = 0; i < n; i++) {                   /* decodifica: un byte = una muestra de cada canal */
        int v0 = d[i] >> 4, v1 = d[i] & 15;
        yam_paso(&e[0], v0); ch[0][i] = (float)e[0].senal;
        yam_paso(&e[1], v1); ch[1][i] = (float)e[1].senal;
    }
    for (i = 0; i < NT; i++) {                  /* paso bajo a 0,45 x 22050 (sobre 44100: 0,225) */
        double k = i - (NT - 1) / 2.0, fc = 0.225;
        double x = k == 0 ? 2 * fc : sin(2 * M_PI * fc * k) / (M_PI * k);
        h[i] = x * (0.42 - 0.5 * cos(2 * M_PI * i / (NT - 1)) + 0.08 * cos(4 * M_PI * i / (NT - 1)));
        s += h[i];
    }
    for (i = 0; i < NT; i++) h[i] /= s;
    m = n / 2;
    o = malloc(m);
    e[0].senal = e[1].senal = 0; e[0].paso = e[1].paso = 0x7f;
    for (i = 0; i < m; i++) {
        int y[2];
        for (c = 0; c < 2; c++) {
            double a = 0; int k;
            for (k = 0; k < NT; k++) { long j = 2 * i + k - (NT - 1) / 2; if (j >= 0 && j < n) a += h[k] * ch[c][j]; }
            y[c] = a > 32767 ? 32767 : a < -32768 ? -32768 : (int)lrint(a);
        }
        o[i] = (uint8_t)(yam_cod(&e[1], y[1]) | (yam_cod(&e[0], y[0]) << 4));
    }
    if (!(f = fopen(argv[2], "wb"))) { perror(argv[2]); return 1; }
    fwrite(o, 1, m, f); fclose(f);
    fprintf(stderr, "%s: %ld -> %ld muestras por canal\n", argv[1], n, m);
    return 0;
}
