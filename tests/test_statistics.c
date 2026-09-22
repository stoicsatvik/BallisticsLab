#include "../src/statistics.h"

#include <assert.h>
#include <math.h>
#include <stddef.h>

static int close_enough(double a, double b, double tolerance) {
    return fabs(a - b) <= tolerance;
}

int main(void) {
    const double values[] = {1.0, 2.0, 3.0, 4.0, 5.0};
    StatsSummary summary;
    assert(stats_summary(values, 5, &summary) == 0);
    assert(close_enough(summary.mean, 3.0, 1e-12));
    assert(close_enough(summary.sample_variance, 2.5, 1e-12));
    assert(close_enough(summary.sample_stddev, sqrt(2.5), 1e-12));
    assert(close_enough(summary.p50, 3.0, 1e-12));
    assert(close_enough(summary.p05, 1.2, 1e-12));
    assert(close_enough(summary.p95, 4.8, 1e-12));

    const double invalid[] = {1.0, NAN};
    assert(stats_summary(invalid, 2, &summary) != 0);
    assert(stats_summary(values, 1, &summary) != 0);
    assert(stats_summary(NULL, 5, &summary) != 0);

    StatsRng a, b;
    stats_rng_seed(&a, 42);
    stats_rng_seed(&b, 42);
    for (size_t i = 0; i < 32; ++i) {
        assert(stats_rng_uniform01(&a) == stats_rng_uniform01(&b));
    }

    stats_rng_seed(&a, 7);
    stats_rng_seed(&b, 7);
    for (size_t i = 0; i < 32; ++i) {
        assert(stats_rng_normal(&a, 10.0, 2.0) == stats_rng_normal(&b, 10.0, 2.0));
    }
    assert(isnan(stats_rng_normal(NULL, 0.0, 1.0)));
    assert(isnan(stats_rng_normal(&a, 0.0, -1.0)));
    assert(stats_rng_normal(&a, 5.0, 0.0) == 5.0);
    return 0;
}
