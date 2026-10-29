CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -pedantic -O2
LDLIBS ?= -lm
TARGET := ballisticslab
TEST_TARGET := test_physics
STATS_TEST_TARGET := test_statistics
INVARIANT_TEST_TARGET := test_integrator_invariants
E391_TEST_TARGET := test_e391_ulp_boundary
SRC := src/main.c src/physics.c
TEST_SRC := tests/test_physics.c src/physics.c
STATS_TEST_SRC := tests/test_statistics.c src/statistics.c
INVARIANT_TEST_SRC := tests/test_integrator_invariants.c src/physics.c
E391_TEST_SRC := tests/test_e391_ulp_boundary.c src/physics.c

.PHONY: all clean run test

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) $(LDLIBS) -o $(TARGET)

$(TEST_TARGET): $(TEST_SRC)
	$(CC) $(CFLAGS) $(TEST_SRC) $(LDLIBS) -o $(TEST_TARGET)

$(STATS_TEST_TARGET): $(STATS_TEST_SRC)
	$(CC) $(CFLAGS) $(STATS_TEST_SRC) $(LDLIBS) -o $(STATS_TEST_TARGET)

$(INVARIANT_TEST_TARGET): $(INVARIANT_TEST_SRC)
	$(CC) $(CFLAGS) $(INVARIANT_TEST_SRC) $(LDLIBS) -o $(INVARIANT_TEST_TARGET)

$(E391_TEST_TARGET): $(E391_TEST_SRC)
	$(CC) $(CFLAGS) $(E391_TEST_SRC) $(LDLIBS) -o $(E391_TEST_TARGET)

run: $(TARGET)
	./$(TARGET)

test: $(TEST_TARGET) $(STATS_TEST_TARGET) $(INVARIANT_TEST_TARGET) $(E391_TEST_TARGET)
	./$(TEST_TARGET)
	./$(STATS_TEST_TARGET)
	./$(INVARIANT_TEST_TARGET)
	./$(E391_TEST_TARGET)

clean:
	rm -f $(TARGET) $(TEST_TARGET) $(STATS_TEST_TARGET) $(INVARIANT_TEST_TARGET) $(E391_TEST_TARGET)
