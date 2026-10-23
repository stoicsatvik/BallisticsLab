CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -pedantic -O2
LDLIBS ?= -lm
TARGET := ballisticslab
TEST_TARGET := test_physics
STATS_TEST_TARGET := test_statistics
SRC := src/main.c src/physics.c
TEST_SRC := tests/test_physics.c src/physics.c
STATS_TEST_SRC := tests/test_statistics.c src/statistics.c

.PHONY: all clean run test

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) $(LDLIBS) -o $(TARGET)

$(TEST_TARGET): $(TEST_SRC)
	$(CC) $(CFLAGS) $(TEST_SRC) $(LDLIBS) -o $(TEST_TARGET)

$(STATS_TEST_TARGET): $(STATS_TEST_SRC)
	$(CC) $(CFLAGS) $(STATS_TEST_SRC) $(LDLIBS) -o $(STATS_TEST_TARGET)

run: $(TARGET)
	./$(TARGET)

test: $(TEST_TARGET) $(STATS_TEST_TARGET)
	./$(TEST_TARGET)
	./$(STATS_TEST_TARGET)

clean:
	rm -f $(TARGET) $(TEST_TARGET) $(STATS_TEST_TARGET)
