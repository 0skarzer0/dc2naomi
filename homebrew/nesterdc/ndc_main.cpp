// NesterDC for NAOMI (KallistiOS NAOMI_HOST): minimal frontend.
// Core: Nester (GPL2), NesterDC port by tekezo (pqrs-org). Frontend: this file (BSD).
#define NDC_USE_KOS_TYPES
#include <kos.h>
#include <string.h>
#include <stdio.h>
#include "nes.h"
#include "sound_mgr.h"

KOS_INIT_FLAGS(INIT_DEFAULT);

extern "C" {
extern const unsigned char rom_start[];
extern const unsigned char rom_end[];
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
static void poll_input(NES *emu) {
  for (int n = 0; n < 4; n++) {
    NES_pad *pad = emu->get_pad(n);
    maple_device_t *dev = maple_enum_type(n, MAPLE_FUNC_CONTROLLER);
    uint32 b = 0; int jx = 0;
    if (dev) {
      cont_state_t *st = (cont_state_t *)maple_dev_status(dev);
      if (st) { b = st->buttons; jx = st->joyx; }
    }
    pad->nes_A      = (b & (CONT_A)) != 0;
    pad->nes_B      = (b & (CONT_X | CONT_B)) != 0;
    pad->nes_SELECT = (b & (CONT_Y | CONT_Z)) != 0;
    pad->nes_START  = (b & CONT_START) != 0;
    pad->nes_UP     = (b & CONT_DPAD_UP) != 0;
    pad->nes_DOWN   = (b & CONT_DPAD_DOWN) != 0;
    pad->nes_LEFT   = ((b & CONT_DPAD_LEFT) != 0) || jx < -48;
    pad->nes_RIGHT  = ((b & CONT_DPAD_RIGHT) != 0) || jx > 48;
  }
}

int main(int argc, char **argv) {
  video_init();
  fs_ramdisk_attach("game.nes", (void *)rom_start, rom_end - rom_start);

  ndc_sound_mgr *snd = new ndc_sound_mgr();
  snd->initialize();
  NES *emu = new NES(snd);
  strcpy(emu->disksys_rom_filename, "/ram/disksys.rom");
  if (!emu->initialize("/ram/game.nes")) {
    printf("NesterDC: cannot load ROM\n");
    for (;;) { video_draw(); }
  }
  for (;;) {
    poll_input(emu);
    emu->emulate_frame(nes_screen);
    snd->poll();
    video_draw();
  }
  return 0;
}

// symbols the old frontend used (gun device)
extern "C++" uint16 get_nesscreen_pixel_color(int x, int y) { return nes_screen[y * 320 + x + 8]; }
