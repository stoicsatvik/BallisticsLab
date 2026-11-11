#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "../src/integrator.h"
#include "../src/physics.h"

static int nearly_equal(double a, double b, double tolerance) {
    return fabs(a - b) <= tolerance;
}

static double max_height(const TrajectorySample *samples, size_t count) {
    double result = 0.0;
    for (size_t i = 0; i < count; ++i) {
        if (samples[i].y_m > result) {
            result = samples[i].y_m;
        }
    }
    return result;
}

static double range_error(double dt_s) {
    TrajectorySample samples[10000];
    size_t count = 0;
    const TrajectoryResult analytic = bl_vacuum_trajectory(20.0, 45.0);
    assert(bl_simulate_vacuum(20.0, 45.0, dt_s, samples, 10000, &count) == BL_SIM_OK);
    assert(count >= 2);
    return fabs(samples[count - 1].x_m - analytic.range_m);
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

    TrajectorySample samples[10000];
    size_t count = 0;
    const TrajectoryResult analytic = bl_vacuum_trajectory(20.0, 45.0);
    assert(bl_simulate_vacuum(20.0, 45.0, 0.001, samples, 10000, &count) == BL_SIM_OK);
    assert(count > 2);
    assert(samples[0].time_s == 0.0 && samples[0].x_m == 0.0 && samples[0].y_m == 0.0);
    assert(samples[count - 1].y_m == 0.0);
    assert(fabs(samples[count - 1].time_s - analytic.flight_time_s) < 0.002);
    assert(fabs(samples[count - 1].x_m - analytic.range_m) < 0.03);
    assert(fabs(max_height(samples, count) - analytic.max_height_m) < 0.08);

    const double coarse_error = range_error(0.08);
    const double medium_error = range_error(0.04);
    const double fine_error = range_error(0.02);
    assert(coarse_error > medium_error);
    assert(medium_error > fine_error);

    TrajectorySample degenerate[4];
    size_t degenerate_count = 0;
    assert(bl_simulate_vacuum(0.0, 45.0, 0.1, degenerate, 4, &degenerate_count) == BL_SIM_OK);
    assert(degenerate_count == 1);
    assert(bl_simulate_vacuum(10.0, 0.0, 0.1, degenerate, 4, &degenerate_count) == BL_SIM_OK);
    assert(degenerate_count == 1);

    assert(bl_simulate_vacuum(-1.0, 45.0, 0.1, degenerate, 4, &degenerate_count) == BL_SIM_INVALID_ARGUMENT);
    assert(bl_simulate_vacuum(10.0, 91.0, 0.1, degenerate, 4, &degenerate_count) == BL_SIM_INVALID_ARGUMENT);
    assert(bl_simulate_vacuum(10.0, 45.0, 0.0, degenerate, 4, &degenerate_count) == BL_SIM_INVALID_ARGUMENT);
    assert(bl_simulate_vacuum(10.0, 45.0, NAN, degenerate, 4, &degenerate_count) == BL_SIM_INVALID_ARGUMENT);
    assert(bl_simulate_vacuum(10.0, 45.0, 0.001, degenerate, 4, &degenerate_count) == BL_SIM_INSUFFICIENT_CAPACITY);
    assert(degenerate_count == 0);

    FILE *csv = tmpfile();
    assert(csv != NULL);
    assert(bl_write_trajectory_csv(csv, samples, count) == 1);
    rewind(csv);
    char header[128];
    assert(fgets(header, sizeof(header), csv) != NULL);
    assert(strcmp(header, "time_s,x_m,y_m,vx_mps,vy_mps\n") == 0);
    fclose(csv);
    assert(bl_write_trajectory_csv(NULL, samples, count) == 0);
    assert(bl_write_trajectory_csv(stdout, NULL, 0) == 0);

    puts("physics and integrator tests passed");
    return 0;
}
