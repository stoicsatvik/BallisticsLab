/* Generic measurement-science control, not weapon modeling.
 * A toy laboratory cart has Gaussian speed uncertainty.
 * E[0.5*m*V^2] = 0.5*m*(mean^2+variance).
 */
#include <assert.h>
#include <math.h>
#include "../src/physics.h"

static double gaussian_expected_energy(double mass, double mean, double stddev) {
    assert(isfinite(mass) && mass >= 0.0);
    assert(isfinite(mean) && isfinite(stddev) && stddev >= 0.0);
    return 0.5 * mass * (mean * mean + stddev * stddev);
}
int main(void) {
    const double mass = 1.0, mean = 1.0;
    const double sigmas[] = {0.05, 0.20, 0.50, 1.00};
    const double expected[] = {0.50125, 0.52, 0.625, 1.0};
    for (int i = 0; i < 4; i++) {
        const double e = gaussian_expected_energy(mass, mean, sigmas[i]);
        assert(fabs(e - expected[i]) < 1e-12);
        assert(e >= bl_kinetic_energy(mass, mean));
    }
    return 0;
}
