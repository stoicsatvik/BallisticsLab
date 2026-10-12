#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "../src/numerics.h"

static int close_to(double a, double b, double tol) {
    return fabs(a - b) <= tol;
}

static void test_uniform_gravity_invariants(void) {
    const double g = 9.80665;
    BLParticleState s = {0.0, 1.0, 20.0, 2.0, 0.0};
    const double initial_energy = 0.5 * (s.vx_mps * s.vx_mps +
                                         s.vy_mps * s.vy_mps) + g * s.y_m;
    for (unsigned i = 0; i < 100; ++i) {
        assert(bl_step_uniform_gravity(&s, 0.01, g) == 0);
        assert(close_to(s.x_m, 1.0 + 2.0 * s.time_s, 1e-10));
        assert(close_to(s.y_m, 20.0 - 0.5 * g * s.time_s * s.time_s, 1e-10));
        assert(close_to(s.vy_mps, -g * s.time_s, 1e-10));
        const double energy = 0.5 * (s.vx_mps * s.vx_mps +
                                     s.vy_mps * s.vy_mps) + g * s.y_m;
        assert(close_to(energy, initial_energy, 1e-9));
    }
}

static void test_input_contract(void) {
    BLParticleState s = {0.0, 0.0, 10.0, 0.0, 0.0};
    BLParticleState original = s;
    assert(bl_step_uniform_gravity(NULL, 0.1, 9.8) != 0);
    assert(bl_step_uniform_gravity(&s, 0.0, 9.8) != 0);
    assert(bl_step_uniform_gravity(&s, NAN, 9.8) != 0);
    assert(bl_step_uniform_gravity(&s, 0.1, INFINITY) != 0);
    assert(memcmp(&s, &original, sizeof(s)) == 0);
}

static void test_drop_and_csv(void) {
    const double g = 9.80665;
    const double height = 12.0;
    const double expected = sqrt(2.0 * height / g);
    for (int k = 0; k < 4; ++k) {
        const double dt = 0.7 / (double)(1 << k);
        FILE *file = tmpfile();
        assert(file != NULL);
        double t = -1.0;
        assert(bl_write_drop_csv(file, height, g, dt, 200, &t) == 0);
        assert(close_to(t, expected, 1e-10));
        rewind(file);
        char header[128];
        assert(fgets(header, sizeof(header), file));
        assert(strcmp(header, "time_s,x_m,y_m,vx_mps,vy_mps\n") == 0);
        double last_t = -1.0, last_y = -1.0, parsed_t, x, y, vx, vy;
        char line[256];
        while (fgets(line, sizeof(line), file)) {
            assert(sscanf(line, "%lf,%lf,%lf,%lf,%lf", &parsed_t, &x, &y, &vx, &vy) == 5);
            assert(parsed_t >= last_t);
            last_t = parsed_t;
            last_y = y;
        }
        assert(close_to(last_t, expected, 1e-10));
        assert(close_to(last_y, 0.0, 1e-12));
        fclose(file);
    }
}

static void test_budget_and_edge_cases(void) {
    FILE *file = tmpfile();
    assert(file != NULL);
    double t = -1.0;
    assert(bl_write_drop_csv(file, 100.0, 9.8, 0.1, 1, &t) == 3);
    assert(t == -1.0);
    assert(bl_write_drop_csv(file, 0.0, 9.8, 0.1, 1, &t) == 0);
    assert(t == 0.0);
    assert(bl_write_drop_csv(file, NAN, 9.8, 0.1, 10, &t) == 1);
    assert(bl_write_drop_csv(file, 1.0, 9.8, 0.0, 10, &t) == 1);
    fclose(file);
}

int main(void) {
    test_uniform_gravity_invariants();
    test_input_contract();
    test_drop_and_csv();
    test_budget_and_edge_cases();
    puts("numerical gravity tests passed");
    return 0;
}
