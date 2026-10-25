/* E274: deterministic, non-operational constant-acceleration invariants.
 * Compare the existing numerical engine to its exact classroom model.
 * No target, weapon, drag, range optimization, or real-world firing input.
 */
#include <assert.h>
#include <math.h>
#include <stdio.h>

#include "../src/physics.h"

static const double GRAVITY = 9.80665;

static double relative_error(double a, double b) {
    return fabs(a - b) / fmax(1.0, fabs(b));
}

int main(void) {
    const double speeds[] = {1.0, 3.0, 10.0, 30.0, 100.0};
    const double angles[] = {10.0, 25.0, 45.0, 65.0, 80.0};
    const double steps[] = {0.01, 0.05, 0.2, 1.0, 5.0, 10.0};
    size_t cases = 0, samples = 0;
    double worst_time = 0.0, worst_x = 0.0, worst_energy = 0.0;
    double worst_height = 0.0;

    for (size_t i = 0; i < sizeof(speeds)/sizeof(speeds[0]); ++i) {
        for (size_t j = 0; j < sizeof(angles)/sizeof(angles[0]); ++j) {
            for (size_t k = 0; k < sizeof(steps)/sizeof(steps[0]); ++k) {
                const double speed = speeds[i];
                const double angle = angles[j];
                const TrajectoryResult exact = bl_vacuum_trajectory(speed, angle);
                NumericalTrajectory numerical = {0};
                assert(bl_simulate_vacuum(speed, angle, steps[k], &numerical) == 0);
                assert(numerical.samples != NULL && numerical.count >= 2);
                const double t_err = relative_error(numerical.impact_time_s,
                                                    exact.flight_time_s);
                const double x_err = relative_error(numerical.impact_x_m,
                                                    exact.range_m);
                const double h_err = relative_error(numerical.max_height_m,
                                                    exact.max_height_m);
                if (t_err > worst_time) worst_time = t_err;
                if (x_err > worst_x) worst_x = x_err;
                if (h_err > worst_height) worst_height = h_err;
                assert(t_err < 1e-8 && x_err < 1e-8 && h_err < 1e-8);
                const double initial_energy = 0.5 * speed * speed;
                for (size_t n = 0; n < numerical.count; ++n) {
                    const TrajectorySample s = numerical.samples[n];
                    const double energy = 0.5 * (s.vx_mps*s.vx_mps +
                                                 s.vy_mps*s.vy_mps) +
                                          GRAVITY * s.y_m;
                    const double e_err = relative_error(energy, initial_energy);
                    if (e_err > worst_energy) worst_energy = e_err;
                    assert(e_err < 1e-8);
                    assert(isfinite(s.time_s) && isfinite(s.x_m) &&
                           isfinite(s.y_m) && isfinite(s.vx_mps) &&
                           isfinite(s.vy_mps));
                    assert(s.y_m >= -1e-9);
                    assert(relative_error(s.x_m,
                            exact.horizontal_velocity_mps*s.time_s) < 1e-8);
                    if (n > 0) assert(s.time_s > numerical.samples[n-1].time_s);
                }
                const TrajectorySample impact = numerical.samples[numerical.count-1];
                assert(impact.y_m == 0.0);
                assert(impact.time_s == numerical.impact_time_s);
                assert(impact.x_m == numerical.impact_x_m);
                ++cases;
                samples += numerical.count;
                bl_free_trajectory(&numerical);
            }
        }
    }
    assert(cases == 150);
    printf("E274_GENERIC_CASES %zu\n", cases);
    printf("E274_GENERIC_SAMPLES %zu\n", samples);
    printf("E274_MAX_RELATIVE_TIME_ERROR %.17g\n", worst_time);
    printf("E274_MAX_RELATIVE_X_ERROR %.17g\n", worst_x);
    printf("E274_MAX_RELATIVE_APEX_ERROR %.17g\n", worst_height);
    printf("E274_MAX_RELATIVE_ENERGY_DRIFT %.17g\n", worst_energy);
    return 0;
}
