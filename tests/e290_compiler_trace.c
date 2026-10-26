/* E290: generic classroom constant-acceleration numerical portability.
 * No real-world targets, firing solutions, drag optimization or weapon inputs.
 * Each deterministic state is emitted for cross-toolchain comparison.
 */
#include <float.h>
#include <math.h>
#include <stdio.h>
#include "../src/physics.h"

static int emit(int case_id, double speed, double angle, double dt) {
    NumericalTrajectory result = {0};
    const int status = bl_simulate_vacuum(speed, angle, dt, &result);
    printf("C %d %d %zu %.17g %.17g %.17g\n",
           case_id, status, result.count,
           result.impact_time_s, result.impact_x_m, result.max_height_m);
    if (status == 0) {
        for (size_t i = 0; i < result.count; ++i) {
            const TrajectorySample s = result.samples[i];
            printf("S %d %zu %.17g %.17g %.17g %.17g %.17g\n",
                   case_id, i, s.time_s, s.x_m, s.y_m, s.vx_mps, s.vy_mps);
        }
    }
    bl_free_trajectory(&result);
    return status;
}

int main(void) {
    const double speeds[] = {1.0, 3.0, 10.0, 30.0, 100.0};
    const double angles[] = {10.0, 25.0, 45.0, 65.0, 80.0};
    const double steps[] = {0.01, 0.05, 0.2, 1.0, 5.0, 10.0};
    int id = 0;
    for (size_t i = 0; i < 5; ++i) {
        for (size_t j = 0; j < 5; ++j) {
            for (size_t k = 0; k < 6; ++k) {
                if (emit(id++, speeds[i], angles[j], steps[k]) != 0)
                    return 2;
            }
        }
    }
    /* The nine boundary controls are diagnostic, not a physics model. */
    emit(id++, 0.0, 45.0, 0.1);
    emit(id++, -1.0, 45.0, 0.1);
    emit(id++, 1.0, 0.0, 0.1);
    emit(id++, 1.0, 90.0, 0.1);
    emit(id++, NAN, 45.0, 0.1);
    emit(id++, 1.0, 45.0, INFINITY);
    emit(id++, 1.0, 45.0, 1e-300);
    emit(id++, 1e308, 45.0, 1e-3);
    emit(id++, 1.0, 45.0, DBL_MAX);
    return id == 159 ? 0 : 3;
}
