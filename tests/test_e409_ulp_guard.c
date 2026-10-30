/* E409: isolate a binary64 terminal-event resolution failure.
 * Generic classroom constant-acceleration arithmetic only; no weapon
 * parameters, targeting, optimization or empirical physical claims.
 */
#include <assert.h>
#include <float.h>
#include <math.h>
#include <stdio.h>
#include "../src/physics.h"

int main(void) {
    const double g = 9.80665;
    const double speed = 100.0;
    const double angle = 15.0;
    const TrajectoryResult analytic = bl_vacuum_trajectory(speed, angle);
    const double dt = nextafter(analytic.flight_time_s * 0.5, 0.0);
    NumericalTrajectory result = {0};
    assert(bl_simulate_vacuum(speed, angle, dt, &result) == -1);
    assert(result.samples == NULL && result.count == 0);

    /* Mirror the production operations, not a second trajectory solver.
     * Check every earlier rejection predicate before isolating the
     * strict impact_t > t predicate in the third step. */
    const double vy0 = speed * sin(bl_deg_to_rad(angle));
    const double vx = speed * cos(bl_deg_to_rad(angle));
    double t = 0.0, y = 0.0, vy = vy0, x = 0.0;
    for (int step = 0; step < 2; ++step) {
        const double nt = t + dt;
        const double nx = x + vx * dt;
        const double ny = y + vy * dt - 0.5 * g * dt * dt;
        const double nvy = vy - g * dt;
        assert(isfinite(nt) && isfinite(nx) && isfinite(ny) && isfinite(nvy));
        assert(nt > t && ny >= 0.0);
        assert(!(ny == y && nvy == vy));
        t = nt; x = nx; y = ny; vy = nvy;
    }
    const double nt = t + dt;
    const double nx = x + vx * dt;
    const double ny = y + vy * dt - 0.5 * g * dt * dt;
    const double nvy = vy - g * dt;
    assert(isfinite(nt) && isfinite(nx) && isfinite(ny) && isfinite(nvy));
    assert(nt > t && ny < 0.0 && !(ny == y && nvy == vy));

    const double root = hypot(vy, sqrt(2.0 * g) * sqrt(y));
    const double tau = vy >= 0.0 ? (vy + root) / g
                                 : (2.0 * y) / (root - vy);
    const double impact_t = t + tau;
    const double impact_x = x + vx * tau;
    const double impact_vy = vy - g * tau;
    assert(isfinite(tau) && tau > 0.0 && tau < dt);
    assert(isfinite(impact_x) && isfinite(impact_vy));
    assert(impact_t == t); /* Exact mirrored strict-time guard fails. */
    const double ulp = nextafter(t, INFINITY) - t;
    assert(tau > 0.0 && tau < ulp * 0.5);
    assert(LDBL_MANT_DIG > DBL_MANT_DIG); /* Tested Linux x86_64 ABI. */
    const long double wide_event = (long double)t + (long double)tau;
    assert(wide_event > (long double)t);
    printf("E409_GUARD impact_t<=t; tau=%.17g; ulp=%.17g; "
           "ratio=%.17g; wide_delta=%.21Lg\n",
           tau, ulp, tau / ulp, wide_event - (long double)t);
    return 0;
}
