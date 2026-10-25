#include <assert.h>
#include <math.h>
#include <float.h>
#include <stdio.h>
#include <string.h>

#include "../src/physics.h"

static int nearly_equal(double a, double b, double tolerance) {
    return fabs(a - b) <= tolerance;
}

int main(void) {
    assert(nearly_equal(bl_momentum(2.0, 3.0), 6.0, 1e-12));
    assert(nearly_equal(bl_kinetic_energy(2.0, 3.0), 9.0, 1e-12));

    const TrajectoryResult flat = bl_vacuum_trajectory(10.0, 0.0);
    assert(nearly_equal(flat.flight_time_s, 0.0, 1e-12));
    assert(nearly_equal(flat.range_m, 0.0, 1e-12));
    assert(nearly_equal(flat.max_height_m, 0.0, 1e-12));

    const TrajectoryResult vertical = bl_vacuum_trajectory(10.0, 90.0);
    assert(fabs(vertical.horizontal_velocity_mps) < 1e-9);
    assert(vertical.max_height_m > 5.0 && vertical.max_height_m < 5.2);

    const TrajectoryResult forty_five = bl_vacuum_trajectory(10.0, 45.0);
    assert(forty_five.range_m > 10.1 && forty_five.range_m < 10.3);

    NumericalTrajectory numerical = {0};
    assert(bl_simulate_vacuum(10.0, 45.0, 0.01, &numerical) == 0);
    assert(numerical.count > 2);
    assert(nearly_equal(numerical.impact_time_s, forty_five.flight_time_s, 1e-4));
    assert(nearly_equal(numerical.impact_x_m, forty_five.range_m, 1e-3));
    /* Sampled apex is bounded by one integration interval. */
    assert(nearly_equal(numerical.max_height_m, forty_five.max_height_m, 1e-3));
    assert(nearly_equal(numerical.samples[numerical.count - 1].y_m, 0.0, 1e-12));

    const char *csv_path = "test_trajectory.csv";
    assert(bl_write_trajectory_csv(csv_path, &numerical) == 0);
    FILE *csv = fopen(csv_path, "r");
    assert(csv != NULL);
    char header[128] = {0};
    assert(fgets(header, sizeof(header), csv) != NULL);
    assert(strcmp(header, "time_s,x_m,y_m,vx_mps,vy_mps\n") == 0);
    fclose(csv);
    remove(csv_path);
    bl_free_trajectory(&numerical);

    /* E238: CSV must preserve tiny and large finite measurement values.
       Fixed nine-decimal formatting silently turns 1e-12 into zero, so a
       serialized measurement can contradict the in-memory simulation. */
    TrajectorySample precision_samples[] = {{
        1e-12, 1e-13, 2e-13, 3.141592653589793, -1e12
    }};
    NumericalTrajectory precision = {0};
    precision.samples = precision_samples;
    precision.count = 1;
    assert(bl_write_trajectory_csv(csv_path, &precision) == 0);
    csv = fopen(csv_path, "r");
    assert(csv != NULL);
    assert(fgets(header, sizeof(header), csv) != NULL);
    char row[256] = {0};
    assert(fgets(row, sizeof(row), csv) != NULL);
    double parsed[5] = {0};
    assert(sscanf(row, "%lf,%lf,%lf,%lf,%lf", &parsed[0], &parsed[1],
                  &parsed[2], &parsed[3], &parsed[4]) == 5);
    fclose(csv);
    remove(csv_path);
    assert(parsed[0] == precision_samples[0].time_s);
    assert(parsed[1] == precision_samples[0].x_m);
    assert(parsed[2] == precision_samples[0].y_m);
    assert(parsed[3] == precision_samples[0].vx_mps);
    assert(parsed[4] == precision_samples[0].vy_mps);

    /* E256: invalid measurements must fail closed BEFORE creating a CSV.
       nan/inf strings are not finite measurements and poison downstream data. */
    const TrajectorySample invalid_samples[] = {
        {NAN, 2, 3, 4, 5}, {1, NAN, 3, 4, 5},
        {1, 2, NAN, 4, 5}, {1, 2, 3, NAN, 5},
        {1, 2, 3, 4, NAN}, {INFINITY, 2, 3, 4, 5},
        {1, INFINITY, 3, 4, 5}, {1, 2, INFINITY, 4, 5},
        {1, 2, 3, INFINITY, 5}, {1, 2, 3, 4, INFINITY},
        {-INFINITY, 2, 3, 4, 5}, {1, -INFINITY, 3, 4, 5},
        {1, 2, -INFINITY, 4, 5}, {1, 2, 3, -INFINITY, 5},
        {1, 2, 3, 4, -INFINITY},
    };
    for (size_t i = 0; i < sizeof(invalid_samples)/sizeof(invalid_samples[0]); ++i) {
        NumericalTrajectory bad = {0};
        bad.samples = (TrajectorySample *)&invalid_samples[i];
        bad.count = 1;
        remove(csv_path);
        assert(bl_write_trajectory_csv(csv_path, &bad) == -1);
        FILE *unwanted = fopen(csv_path, "r");
        assert(unwanted == NULL);
    }
    TrajectorySample mixed_samples[] = {
        {0.0, 0.0, 0.0, 0.0, 0.0},
        {1.0, 2.0, 3.0, INFINITY, 5.0}
    };
    NumericalTrajectory mixed = {0};
    mixed.samples = mixed_samples;
    mixed.count = 2;
    assert(bl_write_trajectory_csv(csv_path, &mixed) == -1);
    assert(fopen(csv_path, "r") == NULL);

    /* E198: an oversized time step crosses the entire positive arc.
       Linear endpoint interpolation returned impact_time=0 and max_height=0
       even though the exact constant-acceleration solution is positive. */
    for (size_t i = 0; i < 3; ++i) {
        const double dt = (double[]){0.5, 2.0, 10.0}[i];
        assert(bl_simulate_vacuum(10.0, 45.0, dt, &numerical) == 0);
        assert(nearly_equal(numerical.impact_time_s,
                            forty_five.flight_time_s, 1e-10));
        assert(nearly_equal(numerical.impact_x_m,
                            forty_five.range_m, 1e-9));
        assert(nearly_equal(numerical.max_height_m,
                            forty_five.max_height_m, 1e-9));
        assert(numerical.count >= 2);
        bl_free_trajectory(&numerical);
    }

    /* E217: a zero-energy initial state is a degenerate one-sample
       trajectory. It must not emit two impact samples at the same time. */
    assert(bl_simulate_vacuum(0.0, 45.0, 0.1, &numerical) == 0);
    assert(numerical.count == 1);
    assert(numerical.samples[0].time_s == 0.0);
    assert(numerical.samples[0].y_m == 0.0);
    assert(numerical.impact_time_s == 0.0);
    assert(numerical.impact_x_m == 0.0);
    assert(numerical.max_height_m == 0.0);
    bl_free_trajectory(&numerical);

    /* Positive subnormal speed with unrepresentable flight duration must
       fail rather than append an impact at the same timestamp. */
    assert(bl_simulate_vacuum(nextafter(0.0, 1.0), 45.0, 0.1, &numerical) == -1);
    assert(numerical.count == 0);

    assert(bl_simulate_vacuum(10.0, 45.0, 0.0, &numerical) == -1);
    assert(bl_simulate_vacuum(10.0, 0.0, 0.01, &numerical) == -1);
    assert(bl_simulate_vacuum(-1.0, 45.0, 0.01, &numerical) == -1);

    /* A subnormal step would require astronomically many samples; reject
       before allocating or entering the loop. */
    assert(bl_simulate_vacuum(10.0, 45.0, DBL_MIN, &numerical) == -1);
    assert(numerical.count == 0);

    /* Even an ordinary tiny step must respect the documented sample cap. */
    assert(bl_simulate_vacuum(10.0, 45.0, 1e-6, &numerical) == -1);
    assert(numerical.count == 0);

    /* Finite input can still overflow intermediate position arithmetic. */
    assert(bl_simulate_vacuum(10.0, 45.0, DBL_MAX, &numerical) == -1);
    assert(numerical.count == 0);

    puts("physics tests passed");
    return 0;
}
