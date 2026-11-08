TARGET = pvrtest.elf
OBJS = main.o
all: pvrtest.bin
include $(KOS_BASE)/Makefile.rules
$(TARGET): $(OBJS)
	kos-cc -o $(TARGET) $(OBJS)
pvrtest.bin: $(TARGET)
	kos-objcopy -O binary $(TARGET) pvrtest.bin
clean:
	-rm -f $(TARGET) $(OBJS) pvrtest.bin
