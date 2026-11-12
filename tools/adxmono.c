/* adxmono.c : ADX (CRI, type 3, 4-bit, header version 3 or 4) stereo -> mono, or a mono/stereo ADX at half its sample
 * rate, so that a game's music and voices take half the disc (used for Metropolis Street Racer, see tools/afsmono.py).
 *
 *   adxmono IN.ADX OUT.ADX [--half-rate]
 *
 * Decoding is the standard ADX one (vgmstream's decode_adx: sample = nibble * (scale + 1) + (c1*h1 + c2*h2) >> 12, with
 * c1/c2 from the header's high-pass cutoff and sample rate). The two channels are averaged and encoded again as one
 * channel with the same coefficients: each 32-sample frame tries a few scales around max|residual| / 7 with the decoder's
 * own history (closed loop) and keeps the one with the least error. The header is copied (same size, so the data starts
 * where it did) with the channel count, and for a looped stream the loop byte offsets, rewritten; the sample counts and
 * the loop samples do not change. Ends with the usual end frame (0x8001). A mono input is copied as is.
 * Build: gcc -O2 -o adxmono adxmono.c -lm
 */
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint32_t be32(const uint8_t *p) { return (uint32_t)p[0] << 24 | p[1] << 16 | p[2] << 8 | p[3]; }
static uint16_t be16(const uint8_t *p) { return p[0] << 8 | p[1]; }
static void put32(uint8_t *p, uint32_t v) { p[0] = v >> 24; p[1] = v >> 16; p[2] = v >> 8; p[3] = v; }
static void put16(uint8_t *p, uint16_t v) { p[0] = v >> 8; p[1] = v; }
static int clamp16(int v) { return v > 32767 ? 32767 : v < -32768 ? -32768 : v; }

static void coefs(int cutoff, int rate, int *c1, int *c2) {
    double z = cos(2.0 * M_PI * cutoff / rate), a = M_SQRT2 - z, b = M_SQRT2 - 1.0;
    double c = (a - sqrt((a + b) * (a - b))) / b;
    *c1 = (int)(c * 8192); *c2 = (int)(c * c * -4096);
}

/* encodes 32 samples; h1/h2 are updated with the decoded values; returns squared error */
static double enc_try(const int *x, int scale, int c1, int c2, int *h1, int *h2, uint8_t *out) {
    int a = *h1, b = *h2; double err = 0;
    for (int i = 0; i < 32; i++) {
        int pred = (c1 * a + c2 * b) >> 12;
        int d = x[i] - pred;
        int n = (int)lrint((double)d / scale);
        if (n > 7) n = 7;
        if (n < -8) n = -8;
        int y = clamp16(n * scale + pred);
        err += (double)(y - x[i]) * (y - x[i]);
        b = a; a = y;
        if (out) {
            if (i & 1) out[2 + i / 2] |= n & 15; else out[2 + i / 2] = (n & 15) << 4;
        }
    }
    if (out) { *h1 = a; *h2 = b; }
    return err;
}

static void enc_frame(const int *x, int c1, int c2, int *h1, int *h2, uint8_t *out) {
    int a = *h1, b = *h2, mx = 0;
    for (int i = 0; i < 32; i++) {          /* open-loop residual estimate */
        int pred = (c1 * a + c2 * b) >> 12, d = abs(x[i] - pred);
        if (d > mx) mx = d;
        b = a; a = x[i];
    }
    int base = mx / 7 + 1, best = base; double be = 1e300;
    static const double f[] = {0.75, 0.85, 1.0, 1.15, 1.3, 1.6, 2.0};
    for (unsigned k = 0; k < sizeof f / sizeof *f; k++) {
        int s = (int)(base * f[k]); if (s < 1) s = 1; if (s > 0x1000) s = 0x1000;
        int t1 = *h1, t2 = *h2;
        double e = enc_try(x, s, c1, c2, &t1, &t2, NULL);
        if (e < be) { be = e; best = s; }
    }
    memset(out, 0, 18);
    put16(out, best - 1);
    enc_try(x, best, c1, c2, h1, h2, out);
}

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "uso: adxmono IN.ADX OUT.ADX [--half-rate]\n"); return 2; }
    int half = argc > 3 && !strcmp(argv[3], "--half-rate");
    FILE *f = fopen(argv[1], "rb"); if (!f) { perror(argv[1]); return 1; }
    fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    uint8_t *b = malloc(n); if (fread(b, 1, n, f) != (size_t)n) return 1; fclose(f);
    if (b[0] != 0x80 || b[1] != 0 || b[4] != 3 || b[5] != 18 || b[6] != 4) { fprintf(stderr, "%s: no es ADX tipo 3\n", argv[1]); return 1; }
    int off = be16(b + 2) + 4, ch = b[7], rate = be32(b + 8), cutoff = be16(b + 16), ver = b[18];
    uint32_t total = be32(b + 12);
    FILE *o = fopen(argv[2], "wb"); if (!o) { perror(argv[2]); return 1; }
    if (ch == 1 && !half) { fwrite(b, 1, n, o); fclose(o); return 0; }
    if (ch != 1 && ch != 2) { fprintf(stderr, "%d canales\n", ch); return 1; }
    int c1, c2; coefs(cutoff, rate, &c1, &c2);
    /* decode */
    uint32_t frames = (total + 31) / 32;
    if ((long)off + (long)frames * 18 * ch > n) frames = (n - off) / (18 * ch);
    int *pcm = malloc(sizeof(int) * (size_t)frames * 32 + 64);
    int h[2][2] = {{0, 0}, {0, 0}};
    for (uint32_t fr = 0; fr < frames; fr++) {
        int acc[32] = {0};
        for (int c = 0; c < ch; c++) {
            const uint8_t *p = b + off + ((size_t)fr * ch + c) * 18;
            int scale = (int16_t)be16(p);
            if (scale < 0) { frames = fr; goto decoded; }        /* end frame */
            scale += 1;
            for (int i = 0; i < 32; i++) {
                int nib = (i & 1) ? (p[2 + i / 2] & 15) : (p[2 + i / 2] >> 4);
                if (nib & 8) nib -= 16;
                int y = clamp16(nib * scale + ((c1 * h[c][0] + c2 * h[c][1]) >> 12));
                h[c][1] = h[c][0]; h[c][0] = y; acc[i] += y;
            }
        }
        for (int i = 0; i < 32; i++) pcm[fr * 32 + i] = ch == 2 ? (acc[i] >= 0 ? (acc[i] + 1) / 2 : (acc[i] - 1) / 2) : acc[i];
    }
decoded:;
    uint32_t ns = frames * 32 < total ? frames * 32 : total;
    int orate = rate;
    if (half) {                               /* 2:1 with a small low-pass ([1 2 1] / 4) */
        uint32_t m = ns / 2;
        for (uint32_t i = 0; i < m; i++) {
            int a = pcm[2 * i > 0 ? 2 * i - 1 : 0], c = pcm[2 * i], d = pcm[2 * i + 1 < ns ? 2 * i + 1 : 2 * i];
            pcm[i] = (a + 2 * c + d) / 4;
        }
        ns = m; orate = rate / 2; total = (total + 1) / 2;
        coefs(cutoff, orate, &c1, &c2);
    }
    uint32_t oframes = (ns + 31) / 32;
    for (uint32_t i = ns; i < oframes * 32; i++) pcm[i] = 0;
    uint8_t *hd = malloc(off); memcpy(hd, b, off);
    hd[7] = 1; put32(hd + 8, orate); put32(hd + 12, total);
    if ((ver == 3 && off >= 0x2c && be32(hd + 0x18)) || (ver == 4 && off >= 0x38 && be32(hd + 0x24))) {
        int lo = ver == 3 ? 0x18 : 0x24;      /* loop: flag, start sample, start byte, end sample, end byte */
        for (int k = 0; k < 2; k++) {
            uint8_t *ps = hd + lo + 4 + 8 * k, *pb = ps + 4;
            uint32_t smp = be32(ps);
            if (half) { smp /= 2; put32(ps, smp); }
            put32(pb, off + (smp / 32) * 18);
        }
    }
    fwrite(hd, 1, off, o);
    int h1 = 0, h2 = 0; uint8_t fr18[18];
    for (uint32_t fr = 0; fr < oframes; fr++) { enc_frame(pcm + fr * 32, c1, c2, &h1, &h2, fr18); fwrite(fr18, 1, 18, o); }
    uint8_t end[18] = {0x80, 0x01, 0x00, 0x0e};
    fwrite(end, 1, 18, o);
    fclose(o);
    return 0;
}
