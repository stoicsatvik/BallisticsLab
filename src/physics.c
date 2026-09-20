#include "physics.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

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

static int append_sample(NumericalTrajectory *result, size_t *capacity,
                         TrajectorySample sample) {
    if (result->count == *capacity) {
        size_t next_capacity = *capacity == 0 ? 64 : *capacity * 2;
        TrajectorySample *next = realloc(result->samples,
                                         next_capacity * sizeof(*next));
        if (next == NULL) {
            return -1;
        }
        result->samples = next;
        *capacity = next_capacity;
    }
    result->samples[result->count++] = sample;
    return 0;
}

int bl_simulate_vacuum(double speed_mps, double angle_deg, double dt_s,
                       NumericalTrajectory *result) {
    if (result == NULL || !isfinite(speed_mps) || !isfinite(angle_deg) ||
        !isfinite(dt_s) || speed_mps < 0.0 || angle_deg <= 0.0 ||
        angle_deg >= 90.0 || dt_s <= 0.0) {
        return -1;
    }

    *result = (NumericalTrajectory){0};
    size_t capacity = 0;
    const double theta = bl_deg_to_rad(angle_deg);
    const double vx = speed_mps * cos(theta);
    double vy = speed_mps * sin(theta);
    double t = 0.0;
    double x = 0.0;
    double y = 0.0;

    if (append_sample(result, &capacity,
                      (TrajectorySample){t, x, y, vx, vy}) != 0) {
        return -1;
    }

    while (1) {
        const double next_t = t + dt_s;
        const double next_x = x + vx * dt_s;
        const double next_y = y + vy * dt_s - 0.5 * BL_G * dt_s * dt_s;
        const double next_vy = vy - BL_G * dt_s;

        if (next_y < 0.0) {
            const double fraction = y / (y - next_y);
            const double impact_t = t + fraction * dt_s;
            const double impact_x = x + fraction * (next_x - x);
            const double impact_vy = vy - BL_G * fraction * dt_s;
            TrajectorySample impact = {impact_t, impact_x, 0.0, vx, impact_vy};
            if (append_sample(result, &capacity, impact) != 0) {
                bl_free_trajectory(result);
                return -1;
            }
            result->impact_time_s = impact_t;
            result->impact_x_m = impact_x;
            return 0;
        }

        t = next_t;
        x = next_x;
        y = next_y;
        vy = next_vy;
        if (y > result->max_height_m) {
            result->max_height_m = y;
        }
        if (append_sample(result, &capacity,
                          (TrajectorySample){t, x, y, vx, vy}) != 0) {
            bl_free_trajectory(result);
            return -1;
        }
    }
}

void bl_free_trajectory(NumericalTrajectory *result) {
    if (result == NULL) {
        return;
    }
    free(result->samples);
    *result = (NumericalTrajectory){0};
}

int bl_write_trajectory_csv(const char *path, const NumericalTrajectory *result) {
    if (path == NULL || result == NULL || result->samples == NULL ||
        result->count == 0) {
        return -1;
    }
    FILE *file = fopen(path, "w");
    if (file == NULL) {
        return -1;
    }
    if (fprintf(file, "time_s,x_m,y_m,vx_mps,vy_mps\n") < 0) {
        fclose(file);
        return -1;
    }
    for (size_t i = 0; i < result->count; ++i) {
        const TrajectorySample s = result->samples[i];
        if (fprintf(file, "%.9f,%.9f,%.9f,%.9f,%.9f\n", s.time_s, s.x_m,
                    s.y_m, s.vx_mps, s.vy_mps) < 0) {
            fclose(file);
            return -1;
        }
    }
    return fclose(file) == 0 ? 0 : -1;
}
