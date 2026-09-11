CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -pedantic -O2
LDLIBS ?= -lm
TARGET := ballisticslab
SRC := src/main.c

.PHONY: all clean run

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) $(LDLIBS) -o $(TARGET)

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET)
