/* E391: ULP-neighbour stress of a generic constant-acceleration event solver.
 * Synthetic classroom states only. No targeting, drag, weapon parameters,
 * optimization, or physical measurement.
 */
#include <assert.h>
#include <math.h>
#include <stdio.h>

#include "../src/physics.h"

static double scaled_error(double got, double expected) {
    return fabs(got - expected) / fmax(1.0, fabs(expected));
}

int main(void) {
    const double speeds[] = {1.0, 10.0, 100.0};
    const double angles[] = {15.0, 45.0, 75.0};
    const double ratios[] = {0.5, 1.0, 2.0};
    size_t cases = 0, accepted = 0, rejected = 0;
    double max_t_error = 0.0, max_x_error = 0.0, max_h_error = 0.0;

    for (size_t i = 0; i < 3; ++i) {
        for (size_t j = 0; j < 3; ++j) {
            const TrajectoryResult exact =
                bl_vacuum_trajectory(speeds[i], angles[j]);
            assert(isfinite(exact.flight_time_s) &&
                   exact.flight_time_s > 0.0);
            for (size_t k = 0; k < 3; ++k) {
                const double nominal = exact.flight_time_s * ratios[k];
                const double steps[] = {
                    nextafter(nominal, 0.0),
                    nominal,
                    nextafter(nominal, INFINITY)
                };
                for (size_t m = 0; m < 3; ++m) {
                    NumericalTrajectory result = {0};
                    const int status = bl_simulate_vacuum(
                        speeds[i], angles[j], steps[m], &result);
                    if (status != 0) {
                        fprintf(stderr,
                                "E391_FAIL speed=%.17g angle=%.17g ratio=%.17g "
                                "ULP_index=%zu status=%d\n",
                                speeds[i], angles[j], ratios[k], m, status);
                    }
                    ++cases;
                    if (status != 0) {
                        /* A sub-ULP event may be unrepresentable at the
                           current timestamp; fail-closed is permitted. */
                        assert(result.count == 0 && result.samples == NULL);
                        ++rejected;
                        continue;
                    }
                    ++accepted;
                    assert(result.count >= 2 && result.samples != NULL);
                    const double t_error = scaled_error(
                        result.impact_time_s, exact.flight_time_s);
                    const double x_error = scaled_error(
                        result.impact_x_m, exact.range_m);
                    const double h_error = scaled_error(
                        result.max_height_m, exact.max_height_m);
                    if (t_error > max_t_error) max_t_error = t_error;
                    if (x_error > max_x_error) max_x_error = x_error;
                    if (h_error > max_h_error) max_h_error = h_error;
                    assert(t_error < 1e-8 && x_error < 1e-8 &&
                           h_error < 1e-8);
                    for (size_t n = 1; n < result.count; ++n) {
                        assert(result.samples[n].time_s >
                               result.samples[n-1].time_s);
                        assert(isfinite(result.samples[n].time_s));
                        assert(isfinite(result.samples[n].y_m));
                    }
                    const TrajectorySample last =
                        result.samples[result.count-1];
                    assert(last.y_m == 0.0);
                    assert(last.time_s == result.impact_time_s);
                    assert(last.x_m == result.impact_x_m);
                    bl_free_trajectory(&result);
                }
            }
        }
    }
    assert(cases == 81);
    printf("E391_CASES %zu\n", cases);
    printf("E391_ACCEPTED %zu\n", accepted);
    printf("E391_REJECTED %zu\n", rejected);
    assert(accepted + rejected == cases);
    printf("E391_MAX_SCALED_TIME_ERROR %.17g\n", max_t_error);
    printf("E391_MAX_SCALED_X_ERROR %.17g\n", max_x_error);
    printf("E391_MAX_SCALED_APEX_ERROR %.17g\n", max_h_error);
    return 0;
}
