TARGET = dstest.elf
OBJS = main.o
all: dstest.bin
include $(KOS_BASE)/Makefile.rules
$(TARGET): $(OBJS)
	kos-cc -o $(TARGET) $(OBJS)
dstest.bin: $(TARGET)
	kos-objcopy -O binary $(TARGET) dstest.bin
clean:
	-rm -f $(TARGET) $(OBJS) dstest.bin
