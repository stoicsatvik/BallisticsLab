#ifndef BALLISTICSLAB_PHYSICS_H
#define BALLISTICSLAB_PHYSICS_H

typedef struct {
    double horizontal_velocity_mps;
    double vertical_velocity_mps;
    double flight_time_s;
    double range_m;
    double max_height_m;
} TrajectoryResult;

double bl_deg_to_rad(double degrees);
double bl_momentum(double mass_kg, double speed_mps);
double bl_kinetic_energy(double mass_kg, double speed_mps);
TrajectoryResult bl_vacuum_trajectory(double speed_mps, double angle_deg);

#endif
