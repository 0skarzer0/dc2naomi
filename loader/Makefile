# Needs the KallistiOS environment with KOS_SUBARCH=naomi.
TARGET = loader.elf
OBJS = loader.o resident_bin.o
TITLE ?= DC2NAOMI
NAOMIBINTOOL ?= $(KOS_BASE)/utils/naomibintool/naomibintool

all: loader.bin

include $(KOS_BASE)/Makefile.rules

resident_bin.o: resident_bin.S ../resident/resident.bin
	kos-cc -c -o $@ resident_bin.S

$(TARGET): $(OBJS)
	kos-cc -o $(TARGET) $(OBJS)

loader.bin: $(TARGET)
	$(NAOMIBINTOOL) build $@ -t "$(TITLE)" -d "0SKARZER0" -e $(TARGET)

clean:
	-rm -f $(OBJS) $(TARGET) loader.bin
