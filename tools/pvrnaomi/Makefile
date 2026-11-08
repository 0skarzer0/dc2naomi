TARGET = pvrtest.elf
OBJS = main.o
all: pvrtest_nb.bin pvrtest_np.bin
include $(KOS_BASE)/Makefile.rules
$(TARGET): $(OBJS)
	kos-cc -o $(TARGET) $(OBJS)
pvrtest_nb.bin: $(TARGET)
	$(KOS_BASE)/utils/naomibintool/naomibintool build $@ -t "PVRTEST NB" -d "0SKARZER0" -e $(TARGET)
pvrtest_np.bin: $(TARGET)
	kos-objcopy -O binary $(TARGET) $@
