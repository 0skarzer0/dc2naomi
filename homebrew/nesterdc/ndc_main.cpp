// NesterDC for NAOMI (KallistiOS NAOMI_HOST): minimal frontend.
// Core: Nester (GPL2), NesterDC port by tekezo (pqrs-org). Frontend: this file (BSD).
#define NDC_USE_KOS_TYPES
#include <kos.h>
#include <string.h>
#include <stdio.h>
#include "nes.h"
#include "sound_mgr.h"

KOS_INIT_FLAGS(INIT_DEFAULT);

struct rom_ent { const char *name; const unsigned char *start; const unsigned char *end; };
extern "C" {
extern const struct rom_ent rom_table[];
extern const int rom_count;
}

#define SAMPLE_RATE 44100
#define SAMPLE_BITS 16
#define SOUND_BUF_LEN 0x2000   // 2 halves of 0x1000 bytes (mono, 16 bit)

// ---------------------------------------------------------------- sound
class ndc_sound_mgr : public sound_mgr {
public:
  uint8 buffer[SOUND_BUF_LEN / 2] __attribute__((aligned(32)));
  uint8 ring[SOUND_BUF_LEN] __attribute__((aligned(32)));
  uint8 out[SOUND_BUF_LEN] __attribute__((aligned(32)));
  volatile uint32 consumed;
  bool locked;
  int curhalf;
  snd_stream_hnd_t hnd;

  bool initialize() {
    consumed = 0; locked = false; curhalf = 0;
    memset(ring, 0, sizeof(ring)); memset(buffer, 0, sizeof(buffer));
    snd_stream_init();
    hnd = snd_stream_alloc(cb, SND_STREAM_BUFFER_MAX);
    snd_stream_set_userdata(hnd, this);
    snd_stream_start(hnd, SAMPLE_RATE, 0);
    return true;
  }
  static void *cb(snd_stream_hnd_t h, int smp_req, int *smp_recv) {
    ndc_sound_mgr *s = (ndc_sound_mgr *)snd_stream_get_userdata(h);
    int bytes = smp_req * 2;
    if (bytes > (int)sizeof(s->out)) bytes = sizeof(s->out);
    for (int i = 0; i < bytes; i++) s->out[i] = s->ring[(s->consumed + i) % SOUND_BUF_LEN];
    s->consumed += bytes;
    *smp_recv = bytes / 2;
    return s->out;
  }
  void poll() { snd_stream_poll(hnd); }
  void reset() {}
  void freeze() {}
  void thaw() {}
  void clear_buffer() { memset(ring, 0, sizeof(ring)); }
  boolean lock(sound_buf_pos which, void **buf, uint32 *len) {
    if (locked) return FALSE;
    locked = true; curhalf = (which == SOUND_BUF_HIGH);
    *buf = buffer; *len = sizeof(buffer);
    return TRUE;
  }
  void unlock() {
    if (!locked) return;
    locked = false;
    memcpy(ring + sizeof(buffer) * curhalf, buffer, sizeof(buffer));
  }
  int get_sample_rate() { return SAMPLE_RATE; }
  int get_sample_bits() { return SAMPLE_BITS; }
  sound_buf_pos get_currently_playing_half() {
    return ((consumed % SOUND_BUF_LEN) >= SOUND_BUF_LEN / 2) ? SOUND_BUF_HIGH : SOUND_BUF_LOW;
  }
  boolean IsNull() { return FALSE; }
};

// ---------------------------------------------------------------- video
static uint16 nes_screen[320 * 240] __attribute__((aligned(32)));
static uint16 stage[512 * 256] __attribute__((aligned(32)));
static pvr_ptr_t txr;
static pvr_poly_hdr_t hdr;

static void video_init() {
  vid_set_mode(DM_640x480_VGA, PM_RGB565);
  pvr_init_defaults();
  txr = pvr_mem_malloc(512 * 256 * 2);
  pvr_poly_cxt_t cxt;
  pvr_poly_cxt_txr(&cxt, PVR_LIST_OP_POLY, PVR_TXRFMT_RGB565 | PVR_TXRFMT_NONTWIDDLED, 512, 256, txr, PVR_FILTER_BILINEAR);
  pvr_poly_compile(&hdr, &cxt);
}

static void video_draw() {
  for (int y = 0; y < 240; y++) memcpy(stage + y * 512, nes_screen + y * 320 + 8, 256 * 2);
  pvr_txr_load(stage, txr, sizeof(stage));
  pvr_wait_ready();
  pvr_scene_begin();
  pvr_list_begin(PVR_LIST_OP_POLY);
  pvr_prim(&hdr, sizeof(hdr));
  pvr_vertex_t v;
  v.argb = 0xffffffff; v.oargb = 0; v.z = 1.0f;
  float u1 = 256.0f / 512.0f, v1 = 240.0f / 256.0f;
  v.flags = PVR_CMD_VERTEX;     v.x = 0;   v.y = 0;   v.u = 0;  v.v = 0;  pvr_prim(&v, sizeof(v));
  v.x = 640; v.y = 0;   v.u = u1; v.v = 0;  pvr_prim(&v, sizeof(v));
  v.x = 0;   v.y = 480; v.u = 0;  v.v = v1; pvr_prim(&v, sizeof(v));
  v.flags = PVR_CMD_VERTEX_EOL; v.x = 640; v.y = 480; v.u = u1; v.v = v1; pvr_prim(&v, sizeof(v));
  pvr_list_finish();
  pvr_scene_finish();
}

// ---------------------------------------------------------------- input
// Pads "ct" of dc2naomi (cabinet): short START = Y, START held >1 s = START, lever fwd = B, lever back = A,
// wheel = analog X (and, at the ends, d-pad left+up / right+down), pedals = triggers, JVS 0x0200 = X.
struct Pad { uint32 b; int jx, lt, rt; };
static Pad read_pad(int n) {
  Pad p = {0, 0, 0, 0};
  maple_device_t *dev = maple_enum_type(n, MAPLE_FUNC_CONTROLLER);
  if (dev) {
    cont_state_t *st = (cont_state_t *)maple_dev_status(dev);
    if (st) { p.b = st->buttons; p.jx = st->joyx; p.lt = st->ltrig; p.rt = st->rtrig; }
  }
  return p;
}

static void poll_input(NES *emu) {
  for (int n = 0; n < 4; n++) {
    NES_pad *pad = emu->get_pad(n);
    Pad p = read_pad(n);
    bool lock = (p.jx < -100 || p.jx > 100);          // wheel at its end: the cabinet also sends up/down
    pad->nes_A      = (p.b & CONT_A) != 0 || p.rt > 128;
    pad->nes_B      = (p.b & CONT_B) != 0 || p.lt > 128;
    pad->nes_SELECT = (p.b & CONT_X) != 0;
    pad->nes_START  = (p.b & CONT_Y) != 0;
    pad->nes_UP     = ((p.b & CONT_DPAD_UP) != 0) && !lock;
    pad->nes_DOWN   = ((p.b & CONT_DPAD_DOWN) != 0) && !lock;
    pad->nes_LEFT   = ((p.b & CONT_DPAD_LEFT) != 0) || p.jx < -48;
    pad->nes_RIGHT  = ((p.b & CONT_DPAD_RIGHT) != 0) || p.jx > 48;
  }
}

// ---------------------------------------------------------------- ROM menu
static void draw_stage() {
  pvr_txr_load(stage, txr, sizeof(stage));
  pvr_wait_ready();
  pvr_scene_begin();
  pvr_list_begin(PVR_LIST_OP_POLY);
  pvr_prim(&hdr, sizeof(hdr));
  pvr_vertex_t v;
  v.argb = 0xffffffff; v.oargb = 0; v.z = 1.0f;
  v.flags = PVR_CMD_VERTEX;     v.x = 0;   v.y = 0;   v.u = 0; v.v = 0; pvr_prim(&v, sizeof(v));
  v.x = 640; v.y = 0;   v.u = 1; v.v = 0; pvr_prim(&v, sizeof(v));
  v.x = 0;   v.y = 480; v.u = 0; v.v = 1; pvr_prim(&v, sizeof(v));
  v.flags = PVR_CMD_VERTEX_EOL; v.x = 640; v.y = 480; v.u = 1; v.v = 1; pvr_prim(&v, sizeof(v));
  pvr_list_finish();
  pvr_scene_finish();
}

static void put_text(int line, const char *s) { bfont_draw_str(stage + line * 24 * 512, 512, 1, s); }

// returns the chosen ROM index
static int rom_menu(int cur) {
  uint32 prev = 0xffffffff;       // ignore what is already pressed when the menu opens
  int rep = 0;
  for (;;) {
    Pad p = read_pad(0);
    uint32 pressed = p.b & ~prev;
    if (pressed & CONT_DPAD_UP) { if (cur > 0) cur--; }
    if (pressed & CONT_DPAD_DOWN) { if (cur < rom_count - 1) cur++; }
    if (p.jx < -100 && !rep) { if (cur > 0) cur--; rep = 1; }
    if (p.jx > 100 && !rep) { if (cur < rom_count - 1) cur++; rep = 1; }
    if (p.jx > -60 && p.jx < 60) rep = 0;
    if (pressed & (CONT_A | CONT_Y | CONT_START)) return cur;
    prev = p.b;

    memset(stage, 0, sizeof(stage));
    put_text(0, "NESTERDC  -  JUEGOS");
    int first = cur - 6; if (first < 0) first = 0;
    for (int i = 0; i < 8 && first + i < rom_count; i++) {
      char line[64];
      snprintf(line, sizeof(line), "%c %.38s", (first + i == cur) ? '>' : ' ', rom_table[first + i].name);
      put_text(2 + i, line);
    }
    put_text(9, "VOLANTE=ELEGIR  START=JUGAR");
    draw_stage();
  }
}

int main(int argc, char **argv) {
  video_init();
  for (int i = 0; i < rom_count; i++) {
    char fn[16]; snprintf(fn, sizeof(fn), "r%d.nes", i);
    fs_ramdisk_attach(fn, (void *)rom_table[i].start, rom_table[i].end - rom_table[i].start);
  }
  ndc_sound_mgr *snd = new ndc_sound_mgr();
  snd->initialize();

  int cur = 0;
  for (;;) {
    cur = rom_menu(cur);
    char path[24]; snprintf(path, sizeof(path), "/ram/r%d.nes", cur);
    NES *emu = new NES(snd);
    strcpy(emu->disksys_rom_filename, "/ram/disksys.rom");
    snd->clear_buffer();
    if (!emu->initialize(path)) { delete emu; continue; }
    int hold = 0;
    for (;;) {
      Pad p = read_pad(0);
      // START held (the cabinet sends START after 1 s of holding; one more second) = back to the menu
      if (p.b & CONT_START) { if (++hold >= 60) break; } else hold = 0;
      poll_input(emu);
      emu->emulate_frame(nes_screen);
      snd->poll();
      video_draw();
    }
    delete emu;
    snd->clear_buffer();
  }
  return 0;
}

// symbol the old frontend defined (used by the light-gun device)
extern "C++" uint16 get_nesscreen_pixel_color(int x, int y) { return nes_screen[y * 320 + x + 8]; }
