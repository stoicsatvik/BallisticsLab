#include <assert.h>
#include <math.h>
#include <stdio.h>

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

    NumericalTrajectoryResult numerical;
    TrajectorySample samples[4096];
    assert(bl_simulate_vacuum(10.0, 45.0, 0.001, samples, 4096, &numerical) == 0);
    assert(nearly_equal(numerical.flight_time_s, forty_five.flight_time_s, 1e-9));
    assert(nearly_equal(numerical.range_m, forty_five.range_m, 1e-8));
    assert(nearly_equal(numerical.max_height_m, forty_five.max_height_m, 0.01));
    assert(numerical.steps > 1000);
    assert(nearly_equal(samples[0].time_s, 0.0, 1e-12));
    assert(nearly_equal(samples[numerical.steps].y_m, 0.0, 1e-12));

    NumericalTrajectoryResult invalid;
    assert(bl_simulate_vacuum(10.0, 45.0, 0.0, NULL, 0, &invalid) == -1);

    puts("physics tests passed");
    return 0;
}
