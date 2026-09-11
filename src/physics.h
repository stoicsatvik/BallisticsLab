#ifndef BALLISTICSLAB_PHYSICS_H
#define BALLISTICSLAB_PHYSICS_H

#include <stddef.h>
#include <stdio.h>

typedef struct {
    double horizontal_velocity_mps;
    double vertical_velocity_mps;
    double flight_time_s;
    double range_m;
    double max_height_m;
} TrajectoryResult;

typedef struct {
    double time_s;
    double x_m;
    double y_m;
    double vx_mps;
    double vy_mps;
} TrajectorySample;

double bl_deg_to_rad(double degrees);
double bl_momentum(double mass_kg, double speed_mps);
double bl_kinetic_energy(double mass_kg, double speed_mps);
TrajectoryResult bl_vacuum_trajectory(double speed_mps, double angle_deg);

/*
 * Integrate generic 2D vacuum motion using fixed time steps and constant
 * gravitational acceleration. The caller owns the sample buffer.
 * Returns 0 on success and non-zero for invalid input or insufficient space.
 */
int bl_simulate_vacuum(double speed_mps,
                       double angle_deg,
                       double dt_s,
                       TrajectorySample *samples,
                       size_t capacity,
                       size_t *sample_count);

/* Write previously generated samples as deterministic CSV. */
int bl_write_trajectory_csv(FILE *stream,
                            const TrajectorySample *samples,
                            size_t sample_count);

#endif
