#ifndef BALLISTICSLAB_INTEGRATOR_H
#define BALLISTICSLAB_INTEGRATOR_H

#include <stddef.h>
#include <stdio.h>

typedef struct {
    double time_s;
    double x_m;
    double y_m;
    double vx_mps;
    double vy_mps;
} TrajectorySample;

typedef enum {
    BL_SIM_OK = 0,
    BL_SIM_INVALID_ARGUMENT = 1,
    BL_SIM_INSUFFICIENT_CAPACITY = 2
} BLSimulationStatus;

/* Explicit-Euler vacuum trajectory with linear interpolation at ground contact. */
BLSimulationStatus bl_simulate_vacuum(
    double speed_mps,
    double angle_deg,
    double dt_s,
    TrajectorySample *samples,
    size_t capacity,
    size_t *sample_count
);

/* Writes a header and one row per sample. Returns 1 on success, 0 on failure. */
int bl_write_trajectory_csv(FILE *stream, const TrajectorySample *samples, size_t sample_count);

#endif
