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

int bl_simulate_vacuum(double speed_mps, double angle_deg, double dt_s,
                       TrajectorySample *samples, size_t capacity,
                       NumericalTrajectoryResult *result) {
    if (speed_mps < 0.0 || angle_deg < 0.0 || angle_deg > 90.0 || dt_s <= 0.0 ||
        result == NULL) {
        return -1;
    }

    const double theta = bl_deg_to_rad(angle_deg);
    double t = 0.0;
    double x = 0.0;
    double y = 0.0;
    const double vx = speed_mps * cos(theta);
    double vy = speed_mps * sin(theta);
    double max_height = 0.0;
    size_t steps = 0;

    if (samples != NULL && capacity > 0) {
        samples[0] = (TrajectorySample){t, x, y, vx, vy};
    }

    if (vy <= 0.0) {
        *result = (NumericalTrajectoryResult){0.0, 0.0, 0.0, 0};
        return 0;
    }

    for (;;) {
        const double next_t = t + dt_s;
        const double next_x = x + vx * dt_s;
        const double next_y = y + vy * dt_s - 0.5 * BL_G * dt_s * dt_s;
        const double next_vy = vy - BL_G * dt_s;
        steps++;

        if (next_y <= 0.0) {
            const double a = -0.5 * BL_G;
            const double b = vy;
            const double c = y;
            const double discriminant = b * b - 4.0 * a * c;
            double tau = dt_s;
            if (discriminant >= 0.0) {
                const double root = (-b - sqrt(discriminant)) / (2.0 * a);
                if (root >= 0.0 && root <= dt_s) {
                    tau = root;
                }
            }
            t += tau;
            x += vx * tau;
            y = 0.0;
            vy -= BL_G * tau;
            if (samples != NULL && steps < capacity) {
                samples[steps] = (TrajectorySample){t, x, y, vx, vy};
            }
            break;
        }

        t = next_t;
        x = next_x;
        y = next_y;
        vy = next_vy;
        if (y > max_height) {
            max_height = y;
        }
        if (samples != NULL && steps < capacity) {
            samples[steps] = (TrajectorySample){t, x, y, vx, vy};
        }
    }

    *result = (NumericalTrajectoryResult){t, x, max_height, steps};
    return (samples != NULL && steps >= capacity) ? 1 : 0;
}
