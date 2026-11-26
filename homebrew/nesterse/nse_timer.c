/* nse_timer.c: SE's TMU2 frame timer on the vertical blank (60 Hz on the NAOMI). hz below 60 skips blanks
   (50 -> 5 calls every 6 blanks), above 60 calls the handler several times in one blank. */
#include <kos.h>
#include <dc/vblank.h>
#include "nse_compat.h"

static void (*nse_fn)(void);
static volatile int nse_hz = 60, nse_acc, nse_hnd = -1;

static void nse_vbl(uint32 code, void *data) {
    (void)code; (void)data;
    if (!nse_fn) return;
    nse_acc += nse_hz;
    while (nse_acc >= 60) { nse_acc -= 60; nse_fn(); }
}

void nse_timer_prime(int hz) { nse_hz = hz > 0 ? hz : 60; nse_acc = 0; }
void nse_timer_set_handler(void (*fn)(void)) { nse_fn = fn; }
void nse_timer_start(void) { if (nse_hnd < 0) nse_hnd = vblank_handler_add(nse_vbl, NULL); }
void nse_timer_stop(void) {
    if (nse_hnd >= 0) { vblank_handler_remove(nse_hnd); nse_hnd = -1; }
}
