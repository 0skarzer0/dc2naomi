/* nse_compat.h: forced (-include) into every NesterDC SE / libdreamscript file for the current KallistiOS.
   - stricmp/strnicmp of KOS 1.3's libc are strcasecmp/strncasecmp now.
   - TMU2 belongs to KallistiOS now (timer_ms_*), TMU1 to timer_spin_sleep: SE's frame timer (TMU2 at 50/60 Hz)
     runs from the vertical blank instead (nse_timer.c). */
#ifndef NSE_COMPAT_H
#define NSE_COMPAT_H
#include <strings.h>
#define stricmp strcasecmp
#define strnicmp strncasecmp
#ifdef __cplusplus
extern "C" {
#endif
void nse_timer_prime(int hz);
void nse_timer_set_handler(void (*fn)(void));
void nse_timer_start(void);
void nse_timer_stop(void);
#ifdef __cplusplus
}
#endif
#endif
