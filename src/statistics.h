#ifndef BALLISTICSLAB_STATISTICS_H
#define BALLISTICSLAB_STATISTICS_H

#include <stddef.h>
#include <stdint.h>

typedef struct {
    double mean;
    double sample_variance;
    double sample_stddev;
    double p05;
    double p50;
    double p95;
} StatsSummary;

typedef struct {
    uint64_t state;
} StatsRng;

typedef double (*StatsMonteCarloTransform)(double sample, void *context);

int stats_summary(const double *values, size_t count, StatsSummary *out);
void stats_rng_seed(StatsRng *rng, uint64_t seed);
double stats_rng_uniform01(StatsRng *rng);
double stats_rng_normal(StatsRng *rng, double mean, double stddev);
int stats_monte_carlo_normal(
    uint64_t seed,
    size_t count,
    double input_mean,
    double input_stddev,
    StatsMonteCarloTransform transform,
    void *context,
    StatsSummary *out
);

#endif
