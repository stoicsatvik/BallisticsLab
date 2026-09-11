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

int bl_simulate_vacuum(double speed_mps,
                       double angle_deg,
                       double dt_s,
                       TrajectorySample *samples,
                       size_t capacity,
                       size_t *sample_count) {
    if (!samples || !sample_count || capacity < 2 || !isfinite(speed_mps) ||
        !isfinite(angle_deg) || !isfinite(dt_s) || speed_mps <= 0.0 ||
        dt_s <= 0.0 || angle_deg <= 0.0 || angle_deg >= 90.0) {
        return 1;
    }

    const double theta = bl_deg_to_rad(angle_deg);
    double t = 0.0;
    double x = 0.0;
    double y = 0.0;
    double vx = speed_mps * cos(theta);
    double vy = speed_mps * sin(theta);
    size_t count = 0;

    samples[count++] = (TrajectorySample){t, x, y, vx, vy};

    for (;;) {
        if (count >= capacity) {
            return 2;
        }

        const double previous_t = t;
        const double previous_x = x;
        const double previous_y = y;
        const double previous_vy = vy;

        t += dt_s;
        x += vx * dt_s;
        y += vy * dt_s - 0.5 * BL_G * dt_s * dt_s;
        vy -= BL_G * dt_s;

        if (y <= 0.0) {
            const double denominator = previous_y - y;
            const double fraction = denominator > 0.0 ? previous_y / denominator : 0.0;
            const double landing_t = previous_t + fraction * dt_s;
            const double landing_x = previous_x + fraction * (x - previous_x);
            const double landing_vy = previous_vy - BL_G * fraction * dt_s;
            samples[count++] = (TrajectorySample){landing_t, landing_x, 0.0, vx, landing_vy};
            break;
        }

        samples[count++] = (TrajectorySample){t, x, y, vx, vy};
    }

    *sample_count = count;
    return 0;
}

int bl_write_trajectory_csv(FILE *stream,
                            const TrajectorySample *samples,
                            size_t sample_count) {
    if (!stream || !samples || sample_count == 0) {
        return 1;
    }

    if (fputs("time_s,x_m,y_m,vx_mps,vy_mps\n", stream) == EOF) {
        return 2;
    }

    for (size_t i = 0; i < sample_count; ++i) {
        const TrajectorySample *sample = &samples[i];
        if (fprintf(stream,
                    "%.9f,%.9f,%.9f,%.9f,%.9f\n",
                    sample->time_s,
                    sample->x_m,
                    sample->y_m,
                    sample->vx_mps,
                    sample->vy_mps) < 0) {
            return 2;
        }
    }

    return 0;
}
