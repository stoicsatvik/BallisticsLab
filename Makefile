CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -pedantic -O2
LDLIBS ?= -lm
TARGET := ballisticslab
TEST_TARGET := test_physics
SRC := src/main.c src/physics.c
TEST_SRC := tests/test_physics.c src/physics.c

.PHONY: all clean run test

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) $(LDLIBS) -o $(TARGET)

$(TEST_TARGET): $(TEST_SRC)
	$(CC) $(CFLAGS) $(TEST_SRC) $(LDLIBS) -o $(TEST_TARGET)

run: $(TARGET)
	./$(TARGET)

test: $(TEST_TARGET)
	./$(TEST_TARGET)

clean:
	rm -f $(TARGET) $(TEST_TARGET)
