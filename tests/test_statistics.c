#include "../src/statistics.h"

#include <assert.h>
#include <math.h>
#include <stddef.h>

static int close_enough(double a, double b, double tolerance) {
    return fabs(a - b) <= tolerance;
}

static double affine_transform(double sample, void *context) {
    const double scale = *(const double *)context;
    return scale * sample + 1.0;
}

static double invalid_transform(double sample, void *context) {
    (void)sample;
    (void)context;
    return NAN;
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

    const double scale = 2.0;
    StatsSummary mc_a, mc_b, mc_large;
    assert(stats_monte_carlo_normal(1234, 4096, 10.0, 2.0, affine_transform, (void *)&scale, &mc_a) == 0);
    assert(stats_monte_carlo_normal(1234, 4096, 10.0, 2.0, affine_transform, (void *)&scale, &mc_b) == 0);
    assert(mc_a.mean == mc_b.mean);
    assert(mc_a.sample_stddev == mc_b.sample_stddev);
    assert(mc_a.p05 == mc_b.p05 && mc_a.p50 == mc_b.p50 && mc_a.p95 == mc_b.p95);
    assert(close_enough(mc_a.mean, 21.0, 0.15));
    assert(close_enough(mc_a.sample_stddev, 4.0, 0.15));

    assert(stats_monte_carlo_normal(1234, 65536, 10.0, 2.0, affine_transform, (void *)&scale, &mc_large) == 0);
    assert(fabs(mc_large.mean - 21.0) < fabs(mc_a.mean - 21.0));
    assert(fabs(mc_large.sample_stddev - 4.0) < fabs(mc_a.sample_stddev - 4.0));

    assert(stats_monte_carlo_normal(1, 1, 0.0, 1.0, affine_transform, (void *)&scale, &summary) != 0);
    assert(stats_monte_carlo_normal(1, 10, 0.0, -1.0, affine_transform, (void *)&scale, &summary) != 0);
    assert(stats_monte_carlo_normal(1, 10, 0.0, 1.0, NULL, NULL, &summary) != 0);
    assert(stats_monte_carlo_normal(1, 10, 0.0, 1.0, invalid_transform, NULL, &summary) != 0);
    return 0;
}
