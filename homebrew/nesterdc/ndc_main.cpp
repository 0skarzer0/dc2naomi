// NesterDC for NAOMI (KallistiOS NAOMI_HOST): minimal frontend.
// Core: Nester (GPL2), NesterDC port by tekezo (pqrs-org). Frontend: this file.
#define NDC_USE_KOS_TYPES
#include <kos.h>
#include <string.h>
#include <stdio.h>
#include "nes.h"
#include "sound_mgr.h"
#include "font8x16.h"

KOS_INIT_FLAGS(INIT_DEFAULT);

// The ROMs are files on the (emulated) disc: /cd/ROMS/<id>.NES, and /cd/ROMS.TXT is the index (the folders of the
// user's collection are kept): one entry per line, "d|f <TAB> id <TAB> parent id (-1 = root) <TAB> name".
#define MAX_ENTS 2048
struct Ent { char type; int id; int parent; char name[56]; };
static Ent ents[MAX_ENTS];
static int nents = 0;
static char load_error[64] = "";

static void load_rom_list() {
  FILE *f = fopen("/cd/ROMS.TXT", "rb");
  if (!f) { snprintf(load_error, sizeof(load_error), "NO SE LEE /cd/ROMS.TXT"); return; }
  static char buf[MAX_ENTS * 64];
  size_t n = fread(buf, 1, sizeof(buf) - 1, f);
  fclose(f);
  buf[n] = 0;
  char *s = buf;
  while (*s && nents < MAX_ENTS) {
    char *e = s; while (*e && *e != '\n' && *e != '\r') e++;
    char save = *e; *e = 0;
    Ent *en = &ents[nents];
    char t; int id, parent; char name[56];
    if (sscanf(s, "%c\t%d\t%d\t%55[^\n\r]", &t, &id, &parent, name) == 4) {
      en->type = t; en->id = id; en->parent = parent;
      strncpy(en->name, name, sizeof(en->name) - 1); en->name[sizeof(en->name) - 1] = 0;
      nents++;
    }
    if (!save) break;
    s = e + 1;
    while (*s == '\n' || *s == '\r') s++;
  }
  if (!nents) snprintf(load_error, sizeof(load_error), "ROMS.TXT VACIO");
}

// ---------------------------------------------------------------- sound
// The APU fills a 4096-byte half whenever get_currently_playing_half() changes. snd_stream pulls big chunks from a
// callback, so the halves go into a FIFO that the callback drains; poll() flips the "half" when the FIFO is low.
#define SAMPLE_RATE 44100
#define SAMPLE_BITS 16
#define HALF_BYTES 0x1000
#define FIFO_BYTES 0x10000

class ndc_sound_mgr : public sound_mgr {
public:
  uint8 buffer[HALF_BYTES] __attribute__((aligned(32)));
  uint8 fifo[FIFO_BYTES] __attribute__((aligned(32)));
  uint8 out[0x8000] __attribute__((aligned(32)));
  volatile uint32 wr, rd;
  bool locked;
  int half;
  snd_stream_hnd_t hnd;

  bool initialize() {
    wr = rd = 0; locked = false; half = 0;
    memset(fifo, 0, sizeof(fifo)); memset(buffer, 0, sizeof(buffer));
    snd_stream_init();
    hnd = snd_stream_alloc(cb, 16 << 10);
    snd_stream_set_userdata(hnd, this);
    snd_stream_start(hnd, SAMPLE_RATE, 0);
    return true;
  }
  static void *cb(snd_stream_hnd_t h, int req_bytes, int *got) {
    ndc_sound_mgr *s = (ndc_sound_mgr *)snd_stream_get_userdata(h);
    int bytes = req_bytes < (int)sizeof(s->out) ? req_bytes : (int)sizeof(s->out);
    uint32 avail = s->wr - s->rd;
    int n = avail < (uint32)bytes ? (int)avail : bytes;
    for (int i = 0; i < n; i++) s->out[i] = s->fifo[(s->rd + i) % FIFO_BYTES];
    s->rd += n;
    if (n < bytes) memset(s->out + n, 0, bytes - n);     // underrun: silence
    *got = bytes;
    return s->out;
  }
  void poll() {
    snd_stream_poll(hnd);
    if (wr - rd < 3 * HALF_BYTES) half ^= 1;              // ask the APU for one more block
  }
  void reset() {}
  void freeze() {}
  void thaw() {}
  void clear_buffer() { rd = wr; }
  boolean lock(sound_buf_pos which, void **buf, uint32 *len) {
    if (locked) return FALSE;
    locked = true;
    *buf = buffer; *len = sizeof(buffer);
    return TRUE;
  }
  void unlock() {
    if (!locked) return;
    locked = false;
    if (wr - rd + HALF_BYTES <= FIFO_BYTES) {
      for (int i = 0; i < HALF_BYTES; i++) fifo[(wr + i) % FIFO_BYTES] = buffer[i];
      wr += HALF_BYTES;
    }
  }
  int get_sample_rate() { return SAMPLE_RATE; }
  int get_sample_bits() { return SAMPLE_BITS; }
  sound_buf_pos get_currently_playing_half() { return half ? SOUND_BUF_HIGH : SOUND_BUF_LOW; }
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

// draws the staging texture (u1 x v1 of it) over the whole screen
static void draw_stage(float u1, float v1) {
  pvr_txr_load(stage, txr, sizeof(stage));
  pvr_wait_ready();
  pvr_scene_begin();
  pvr_list_begin(PVR_LIST_OP_POLY);
  pvr_prim(&hdr, sizeof(hdr));
  pvr_vertex_t v;
  v.argb = 0xffffffff; v.oargb = 0; v.z = 1.0f;
  v.flags = PVR_CMD_VERTEX;     v.x = 0;   v.y = 0;   v.u = 0;  v.v = 0;  pvr_prim(&v, sizeof(v));
  v.x = 640; v.y = 0;   v.u = u1; v.v = 0;  pvr_prim(&v, sizeof(v));
  v.x = 0;   v.y = 480; v.u = 0;  v.v = v1; pvr_prim(&v, sizeof(v));
  v.flags = PVR_CMD_VERTEX_EOL; v.x = 640; v.y = 480; v.u = u1; v.v = v1; pvr_prim(&v, sizeof(v));
  pvr_list_finish();
  pvr_scene_finish();
}

static void video_draw() {
  for (int y = 0; y < 240; y++) memcpy(stage + y * 512, nes_screen + y * 320 + 8, 256 * 2);
  draw_stage(256.0f / 512.0f, 240.0f / 256.0f);
}

// ---------------------------------------------------------------- input
// Pads "nes" of dc2naomi (resident.c, DIMM_PAD_NES): START = START only when RELEASED and nothing else was used
// while it was held; wheel = d-pad left/right (at the ends) + analog X, gas = A, brake = B, lever = d-pad up/down;
// with START held: gas = X, brake = Y, lever forward = L trigger, back = R trigger; START + wheel to the right =
// START and RIGHT together, held (the ROM menu).
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
    pad->nes_A      = (p.b & CONT_A) != 0;
    pad->nes_B      = (p.b & CONT_B) != 0;
    pad->nes_SELECT = (p.b & (CONT_X | CONT_Y)) != 0;
    pad->nes_START  = (p.b & CONT_START) != 0;
    pad->nes_UP     = (p.b & CONT_DPAD_UP) != 0;
    pad->nes_DOWN   = (p.b & CONT_DPAD_DOWN) != 0;
    pad->nes_LEFT   = ((p.b & CONT_DPAD_LEFT) != 0) || p.jx < -48;
    pad->nes_RIGHT  = ((p.b & CONT_DPAD_RIGHT) != 0) || p.jx > 48;
  }
}

// ---------------------------------------------------------------- ROM menu
static void put_text(int col, int row, const char *s, uint16 fg) {
  for (; *s && col < 64; s++, col++) {
    int c = (unsigned char)*s; if (c < 32 || c > 126) c = '?';
    const unsigned char *g = font8x16[c - 32];
    for (int y = 0; y < 16; y++)
      for (int x = 0; x < 8; x++)
        stage[(row * 16 + y) * 512 + col * 8 + x] = (g[y] & (0x80 >> x)) ? fg : 0;
  }
}

static int curdir = -1, cursor = 0;

static int find_ent(int id) { for (int i = 0; i < nents; i++) if (ents[i].id == id) return i; return -1; }

// returns the id of the chosen ROM
static int rom_menu() {
  uint32 prev = 0xffffffff;        // what is pressed when the menu opens does not count
  int hold = 0;
  for (;;) {
    // visible entries: ".." (-2), then the folders, then the ROMs, of the current folder
    static int vis[MAX_ENTS + 1]; int nvis = 0;
    if (curdir != -1) vis[nvis++] = -2;
    for (int i = 0; i < nents; i++) if (ents[i].parent == curdir && ents[i].type == 'd') vis[nvis++] = i;
    for (int i = 0; i < nents; i++) if (ents[i].parent == curdir && ents[i].type == 'f') vis[nvis++] = i;
    if (cursor >= nvis) cursor = nvis - 1;
    if (cursor < 0) cursor = 0;

    Pad p = read_pad(0);
    uint32 pressed = p.b & ~prev;
    prev = p.b;
    int step = 0;
    if (pressed & CONT_DPAD_UP) { step = -1; hold = 0; }
    else if (pressed & CONT_DPAD_DOWN) { step = 1; hold = 0; }
    else if (p.b & (CONT_DPAD_UP | CONT_DPAD_DOWN)) {            // auto-repeat when held
      if (++hold > 20 && hold % 4 == 0) step = (p.b & CONT_DPAD_UP) ? -1 : 1;
    } else hold = 0;
    cursor += step;
    if (cursor < 0) cursor = 0;
    if (cursor > nvis - 1) cursor = nvis - 1;
    if (pressed & CONT_DPAD_LEFT) { cursor = cursor > 10 ? cursor - 10 : 0; }
    if (pressed & CONT_DPAD_RIGHT) { cursor = cursor + 10 < nvis ? cursor + 10 : nvis - 1; }
    if ((pressed & (CONT_A | CONT_START)) && nvis) {
      int v = vis[cursor];
      if (v == -2) {                                               // up one folder
        int d = find_ent(curdir);
        curdir = d >= 0 ? ents[d].parent : -1;
        cursor = 0;
        if (d >= 0) {   // leave the cursor on the folder we came from
          int n2 = 0;
          if (curdir != -1) n2++;
          for (int i = 0; i < nents; i++) if (ents[i].parent == curdir && ents[i].type == 'd') { if (i == d) { cursor = n2; break; } n2++; }
        }
        continue;
      }
      if (ents[v].type == 'd') { curdir = ents[v].id; cursor = 0; continue; }
      return ents[v].id;
    }

    memset(stage, 0, sizeof(stage));
    char path[64] = "";
    { int d = find_ent(curdir); if (d >= 0) snprintf(path, sizeof(path), "/%s", ents[d].name); }
    char title[80]; snprintf(title, sizeof(title), "NESTERDC %s", path);
    put_text(0, 0, title, 0xffe0);
    int first = cursor - 5; if (first + 11 > nvis) first = nvis - 11; if (first < 0) first = 0;
    for (int i = 0; i < 11 && first + i < nvis; i++) {
      int v = vis[first + i];
      char line[80];
      if (v == -2) snprintf(line, sizeof(line), "%c ..", (first + i == cursor) ? '>' : ' ');
      else if (ents[v].type == 'd') snprintf(line, sizeof(line), "%c [%s]", (first + i == cursor) ? '>' : ' ', ents[v].name);
      else snprintf(line, sizeof(line), "%c %s", (first + i == cursor) ? '>' : ' ', ents[v].name);
      put_text(0, 2 + i, line, (first + i == cursor) ? 0xffff : 0x8c71);
    }
    snprintf(title, sizeof(title), "%d/%d", cursor + 1, nvis);
    put_text(0, 14, title, 0x07e0);
    put_text(10, 14, "PALANCA=MOVER VOLANTE=PAGINA ACELERADOR=OK", 0x07e0);
    put_text(0, 15, "EN JUEGO: START + VOLANTE DERECHA = VOLVER AL MENU", 0x07e0);
    draw_stage(1.0f, 1.0f);
  }
}

int main(int argc, char **argv) {
  video_init();
  load_rom_list();
  ndc_sound_mgr *snd = new ndc_sound_mgr();
  snd->initialize();

  for (;;) {
    if (!nents) {
      memset(stage, 0, sizeof(stage)); put_text(0, 0, "NESTERDC", 0xffe0); put_text(0, 2, load_error, 0xf800);
      draw_stage(1.0f, 1.0f); continue;
    }
    int id = rom_menu();
    char path[32]; snprintf(path, sizeof(path), "/cd/ROMS/%03d.NES", id);
    NES *emu = new NES(snd);
    strcpy(emu->disksys_rom_filename, "/cd/DISKSYS.ROM");
    snd->clear_buffer();
    if (!emu->initialize(path)) { delete emu; continue; }
    uint64 combo_since = 0;
    for (;;) {
      Pad p = read_pad(0);
      // START + wheel to the right (held 0.3 s) = back to the ROM menu
      if ((p.b & CONT_START) && (p.b & CONT_DPAD_RIGHT)) {
        uint64 now = timer_ms_gettime64();
        if (!combo_since) combo_since = now;
        if (now - combo_since >= 300) break;
      } else combo_since = 0;
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
