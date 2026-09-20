#include <assert.h>
#include <math.h>
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

    assert(bl_simulate_vacuum(10.0, 45.0, 0.0, &numerical) == -1);
    assert(bl_simulate_vacuum(10.0, 0.0, 0.01, &numerical) == -1);
    assert(bl_simulate_vacuum(-1.0, 45.0, 0.01, &numerical) == -1);

    puts("physics tests passed");
    return 0;
}
