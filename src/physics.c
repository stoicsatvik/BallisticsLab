#include "physics.h"

#include <math.h>

static const double BL_G = 9.80665;
static const double BL_PI = 3.14159265358979323846;

double bl_deg_to_rad(double degrees) {
    return degrees * BL_PI / 180.0;
}

double bl_momentum(double mass_kg, double speed_mps) {
    return mass_kg * speed_mps;
}

double bl_kinetic_energy(double mass_kg, double speed_mps) {
    return 0.5 * mass_kg * speed_mps * speed_mps;
}

TrajectoryResult bl_vacuum_trajectory(double speed_mps, double angle_deg) {
    const double theta = bl_deg_to_rad(angle_deg);
    const double vx = speed_mps * cos(theta);
    const double vy = speed_mps * sin(theta);

    TrajectoryResult result = {
        .horizontal_velocity_mps = vx,
        .vertical_velocity_mps = vy,
        .flight_time_s = (2.0 * vy) / BL_G,
        .range_m = vx * ((2.0 * vy) / BL_G),
        .max_height_m = (vy * vy) / (2.0 * BL_G),
    };

    return result;
}

size_t bl_vacuum_integrate(double speed_mps, double angle_deg, double dt_s,
                           TrajectorySample *samples, size_t capacity) {
    if (samples == NULL || capacity == 0 || dt_s <= 0.0 || speed_mps < 0.0) {
        return 0;
    }

    const double theta = bl_deg_to_rad(angle_deg);
    const double vx = speed_mps * cos(theta);
    const double vy0 = speed_mps * sin(theta);
    if (vy0 <= 0.0) {
        samples[0] = (TrajectorySample){0.0, 0.0, 0.0, vx, vy0};
        return 1;
    }

    const double flight_time = (2.0 * vy0) / BL_G;
    size_t count = 0;
    double t = 0.0;

    while (count < capacity) {
        if (t > flight_time) {
            t = flight_time;
        }
        samples[count++] = (TrajectorySample){
            .time_s = t,
            .x_m = vx * t,
            .y_m = vy0 * t - 0.5 * BL_G * t * t,
            .vx_mps = vx,
            .vy_mps = vy0 - BL_G * t,
        };
        if (t >= flight_time) {
            break;
        }
        t += dt_s;
    }

    return count;
}
