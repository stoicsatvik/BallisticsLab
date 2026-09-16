#ifndef BALLISTICSLAB_PHYSICS_H
#define BALLISTICSLAB_PHYSICS_H

#include <stddef.h>

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

typedef struct {
    double flight_time_s;
    double range_m;
    double max_height_m;
    size_t steps;
} NumericalTrajectoryResult;

double bl_deg_to_rad(double degrees);
double bl_momentum(double mass_kg, double speed_mps);
double bl_kinetic_energy(double mass_kg, double speed_mps);
TrajectoryResult bl_vacuum_trajectory(double speed_mps, double angle_deg);
int bl_simulate_vacuum(double speed_mps, double angle_deg, double dt_s,
                       TrajectorySample *samples, size_t capacity,
                       NumericalTrajectoryResult *result);

#endif
