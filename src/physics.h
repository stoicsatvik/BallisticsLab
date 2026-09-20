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
    TrajectorySample *samples;
    size_t count;
    double impact_time_s;
    double impact_x_m;
    double max_height_m;
} NumericalTrajectory;

double bl_deg_to_rad(double degrees);
double bl_momentum(double mass_kg, double speed_mps);
double bl_kinetic_energy(double mass_kg, double speed_mps);
TrajectoryResult bl_vacuum_trajectory(double speed_mps, double angle_deg);

/*
 * Generic educational vacuum integrator. Uses velocity-Verlet kinematics for
 * constant gravitational acceleration and linearly interpolates the final
 * ground crossing. Returns 0 on success and -1 for invalid input/allocation
 * failure. Caller owns result->samples and must call bl_free_trajectory().
 */
int bl_simulate_vacuum(double speed_mps, double angle_deg, double dt_s,
                       NumericalTrajectory *result);
void bl_free_trajectory(NumericalTrajectory *result);
int bl_write_trajectory_csv(const char *path, const NumericalTrajectory *result);

#endif
