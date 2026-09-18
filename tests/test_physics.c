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

    TrajectorySample samples[128];
    assert(bl_vacuum_integrate(10.0, 45.0, 0.05, NULL, 128) == 0);
    assert(bl_vacuum_integrate(10.0, 45.0, 0.0, samples, 128) == 0);

    const size_t count = bl_vacuum_integrate(10.0, 45.0, 0.05, samples, 128);
    assert(count > 2);
    assert(nearly_equal(samples[0].time_s, 0.0, 1e-12));
    assert(nearly_equal(samples[0].x_m, 0.0, 1e-12));
    assert(nearly_equal(samples[0].y_m, 0.0, 1e-12));

    const TrajectorySample last = samples[count - 1];
    assert(nearly_equal(last.time_s, forty_five.flight_time_s, 1e-12));
    assert(nearly_equal(last.x_m, forty_five.range_m, 1e-10));
    assert(fabs(last.y_m) < 1e-10);

    for (size_t i = 1; i < count; ++i) {
        assert(samples[i].time_s > samples[i - 1].time_s);
        assert(samples[i].x_m >= samples[i - 1].x_m);
    }

    TrajectorySample flat_samples[2];
    assert(bl_vacuum_integrate(10.0, 0.0, 0.1, flat_samples, 2) == 1);
    assert(nearly_equal(flat_samples[0].y_m, 0.0, 1e-12));

    puts("physics tests passed");
    return 0;
}
