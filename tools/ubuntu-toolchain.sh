#!/bin/bash
# KallistiOS (KOS_SUBARCH=naomi) with Ubuntu's sh-elf toolchain (gcc 13 + newlib 3.3), for
# environments where the KOS toolchain builder cannot download GCC from the GNU mirrors.
# Good enough for the loader (C only). The proper way is still kos-chain (utils/kos-chain).
set -e
apt-get install -y gcc-sh-elf binutils-sh-elf libnewlib-sh-elf-dev
DC=/opt/toolchains/dc
mkdir -p $DC/sh-elf/bin $DC/compat/lib
for f in /usr/bin/sh-elf-*; do ln -sf $f $DC/sh-elf/bin/; done
[ -d $DC/kos ] || git clone --depth 1 https://github.com/KallistiOS/KallistiOS $DC/kos

# helpers that newer newlib (sys/param.h) and GCC 15 provide
cat > $DC/compat/kos_gcc13.h <<'EOF'
#ifndef KOS_GCC13_COMPAT
#define KOS_GCC13_COMPAT
#ifndef __builtin_is_aligned
#define __builtin_is_aligned(x, a) ((((unsigned long)(x)) & ((unsigned long)(a) - 1)) == 0)
#endif
#ifndef __is_aligned
#define __is_aligned(x, a) __builtin_is_aligned(x, a)
#endif
#ifndef __align_up
#define __align_up(x, a) ((((x) + (a) - 1) / (a)) * (a))
#endif
#ifndef __align_down
#define __align_down(x, a) (((x) / (a)) * (a))
#endif
#endif
EOF

cd $DC/kos
cp doc/environ.sh.sample environ.sh
sed -i 's/^#export KOS_SUBARCH="naomi"/export KOS_SUBARCH="naomi"/' environ.sh
cat >> environ.sh <<'EOF'
export KOS_CFLAGS="${KOS_CFLAGS} -include /opt/toolchains/dc/compat/kos_gcc13.h"
export KOS_LDFLAGS="${KOS_LDFLAGS} -L/opt/toolchains/dc/compat/lib"
EOF
source environ.sh
make -C kernel
make -C utils/naomibintool

# Ubuntu's libc.a brings its own syscall stubs, reentrant wrappers and malloc, which KOS
# implements itself: a copy without the objects that clash with libkallisti.a
L=$(sh-elf-gcc -m4-single -ml -print-file-name=libc.a)
cp "$L" $DC/compat/lib/libc.a
cd $DC/compat/lib
sh-elf-nm --defined-only $DC/kos/lib/dreamcast/libkallisti.a 2>/dev/null | awk '$2=="T"{print $3}' | sort -u > kos.syms
objs=$(sh-elf-nm -A --defined-only libc.a 2>/dev/null | awk '{split($1,a,":"); if ($2=="T") print a[2], $3}' |
       while read o s; do grep -qx "$s" kos.syms && echo "$o"; done | sort -u)
sh-elf-ar d libc.a lib_a-syscalls.o $objs
rm kos.syms
echo "KOS ready: source $DC/kos/environ.sh"
