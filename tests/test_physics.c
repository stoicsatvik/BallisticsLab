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

    TrajectorySample coarse[512];
    TrajectorySample fine[4096];
    size_t coarse_count = 0;
    size_t fine_count = 0;

    assert(bl_simulate_vacuum(10.0, 45.0, 0.01, coarse, 512, &coarse_count) == 0);
    assert(bl_simulate_vacuum(10.0, 45.0, 0.001, fine, 4096, &fine_count) == 0);
    assert(coarse_count > 2);
    assert(fine_count > coarse_count);

    const TrajectorySample coarse_landing = coarse[coarse_count - 1];
    const TrajectorySample fine_landing = fine[fine_count - 1];
    assert(nearly_equal(coarse_landing.y_m, 0.0, 1e-12));
    assert(nearly_equal(fine_landing.y_m, 0.0, 1e-12));
    assert(nearly_equal(coarse_landing.time_s, forty_five.flight_time_s, 1e-4));
    assert(nearly_equal(coarse_landing.x_m, forty_five.range_m, 1e-3));
    assert(nearly_equal(fine_landing.time_s, forty_five.flight_time_s, 1e-6));
    assert(nearly_equal(fine_landing.x_m, forty_five.range_m, 1e-5));

    assert(bl_simulate_vacuum(10.0, 45.0, 0.0, coarse, 512, &coarse_count) != 0);
    assert(bl_simulate_vacuum(10.0, 45.0, 0.01, coarse, 1, &coarse_count) != 0);

    FILE *csv = tmpfile();
    assert(csv != NULL);
    assert(bl_write_trajectory_csv(csv, coarse, coarse_count) == 0);
    rewind(csv);
    char header[128];
    assert(fgets(header, sizeof(header), csv) != NULL);
    assert(strcmp(header, "time_s,x_m,y_m,vx_mps,vy_mps\n") == 0);
    fclose(csv);

    puts("physics tests passed");
    return 0;
}
