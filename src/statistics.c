#include "statistics.h"

#include <math.h>
#include <stdlib.h>

static int compare_double(const void *a, const void *b) {
    const double x = *(const double *)a;
    const double y = *(const double *)b;
    return (x > y) - (x < y);
}

static double percentile_sorted(const double *values, size_t count, double p) {
    const double position = p * (double)(count - 1);
    const size_t lo = (size_t)floor(position);
    const size_t hi = (size_t)ceil(position);
    const double fraction = position - (double)lo;
    return values[lo] + fraction * (values[hi] - values[lo]);
}

int stats_summary(const double *values, size_t count, StatsSummary *out) {
    if (!values || !out || count < 2) return -1;

    double mean = 0.0;
    double m2 = 0.0;
    double *sorted = malloc(count * sizeof(*sorted));
    if (!sorted) return -1;

    for (size_t i = 0; i < count; ++i) {
        if (!isfinite(values[i])) {
            free(sorted);
            return -1;
        }
        sorted[i] = values[i];
        const double delta = values[i] - mean;
        mean += delta / (double)(i + 1);
        m2 += delta * (values[i] - mean);
    }

    qsort(sorted, count, sizeof(*sorted), compare_double);
    out->mean = mean;
    out->sample_variance = m2 / (double)(count - 1);
    out->sample_stddev = sqrt(out->sample_variance);
    out->p05 = percentile_sorted(sorted, count, 0.05);
    out->p50 = percentile_sorted(sorted, count, 0.50);
    out->p95 = percentile_sorted(sorted, count, 0.95);
    free(sorted);
    return 0;
}

void stats_rng_seed(StatsRng *rng, uint64_t seed) {
    if (rng) rng->state = seed ? seed : UINT64_C(0x9e3779b97f4a7c15);
}

static uint64_t next_u64(StatsRng *rng) {
    uint64_t x = rng->state;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    rng->state = x;
    return x * UINT64_C(2685821657736338717);
}

double stats_rng_uniform01(StatsRng *rng) {
    if (!rng) return NAN;
    return (double)(next_u64(rng) >> 11) * (1.0 / 9007199254740992.0);
}

double stats_rng_normal(StatsRng *rng, double mean, double stddev) {
    if (!rng || !isfinite(mean) || !isfinite(stddev) || stddev < 0.0) return NAN;
    if (stddev == 0.0) return mean;
    double u1 = stats_rng_uniform01(rng);
    const double u2 = stats_rng_uniform01(rng);
    if (u1 <= 0.0) u1 = 0x1p-53;
    const double z = sqrt(-2.0 * log(u1)) * cos(6.28318530717958647692 * u2);
    return mean + stddev * z;
}
