/* The finite-input and progress guards below rely on IEEE-style NaN/Inf
 * classification. Fast-math/finite-math-only compilers may assume such
 * values never occur and optimize away isfinite() checks. Fail at build time.
 * This is a generic numerical integrity rule, not a physical validation. */
#if defined(__FAST_MATH__) || (defined(__FINITE_MATH_ONLY__) && __FINITE_MATH_ONLY__)
#error "BallisticsLab finite-input validation requires non-fast-math IEEE semantics"
#endif

#include "physics.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

static const double BL_G = 9.80665;
static const double BL_PI = 3.14159265358979323846;
/* Bound memory and CPU for pathological fixed-step inputs. */
static const size_t BL_MAX_TRAJECTORY_SAMPLES = 1000000;

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
    if (result->count >= BL_MAX_TRAJECTORY_SAMPLES) return -1;
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
    /* A zero-speed initial state has zero flight duration. Return a single
       origin sample, not two identical time-zero impact records. */
    if (speed_mps == 0.0) {
        return append_sample(result, &capacity,
                             (TrajectorySample){0.0, 0.0, 0.0, 0.0, 0.0});
    }
    const double theta = bl_deg_to_rad(angle_deg);
    const double vx = speed_mps * cos(theta);
    double vy = speed_mps * sin(theta);
    /* A tiny step can request billions of samples before the first impact.
       Reject it up front rather than allocating until the process is killed. */
    const double estimated_steps = ((2.0 * vy) / BL_G) / dt_s;
    if (!isfinite(estimated_steps) ||
        estimated_steps > (double)(BL_MAX_TRAJECTORY_SAMPLES - 2)) {
        return -1;
    }
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

        /* Fail closed if arithmetic overflows or time/vertical state stalls.
           Otherwise the loop may append identical samples indefinitely. */
        if (!isfinite(next_t) || !isfinite(next_x) ||
            !isfinite(next_y) || !isfinite(next_vy) || next_t <= t ||
            (next_y == y && next_vy == vy)) {
            bl_free_trajectory(result);
            return -1;
        }

        /* The exact apex may lie between sampled states, even when the
           ground crossing happens in a later integration interval. */
        const double apex_tau = vy / BL_G;
        if (apex_tau > 0.0 && apex_tau < dt_s) {
            const double apex_y = y + vy * apex_tau
                - 0.5 * BL_G * apex_tau * apex_tau;
            if (isfinite(apex_y) && apex_y > result->max_height_m) {
                result->max_height_m = apex_y;
            }
        }

        /* An exactly zero-height endpoint is already the final event.
           Waiting for a negative next step creates a zero-duration
           duplicate and the later root fails the strict time guard. */
        if (next_y == 0.0) {
            const TrajectorySample impact = {
                next_t, next_x, 0.0, vx, next_vy
            };
            if (append_sample(result, &capacity, impact) != 0) {
                bl_free_trajectory(result);
                return -1;
            }
            result->impact_time_s = next_t;
            result->impact_x_m = next_x;
            return 0;
        }

        if (next_y < 0.0) {
            /* Linear interpolation is wrong when a large step spans the
               entire flight: y=0 at both endpoints is not a straight line.
               Solve the constant-acceleration crossing within this step. */
            const double root = hypot(vy, sqrt(2.0 * BL_G) * sqrt(y));
            const double tau = vy >= 0.0
                ? (vy + root) / BL_G
                : (2.0 * y) / (root - vy);
            if (!isfinite(tau) || tau < 0.0 || tau > dt_s) {
                bl_free_trajectory(result);
                return -1;
            }
            const double impact_t = t + tau;
            const double impact_x = x + vx * tau;
            const double impact_vy = vy - BL_G * tau;
            if (!isfinite(impact_t) || impact_t <= t || !isfinite(impact_x) ||
                !isfinite(impact_vy)) {
                bl_free_trajectory(result);
                return -1;
            }
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
    /* E256: validate the complete batch before opening the destination.
       A later NaN/Inf must not leave a partial, apparently valid CSV. */
    for (size_t i = 0; i < result->count; ++i) {
        const TrajectorySample s = result->samples[i];
        if (!isfinite(s.time_s) || !isfinite(s.x_m) || !isfinite(s.y_m) ||
            !isfinite(s.vx_mps) || !isfinite(s.vy_mps)) {
            return -1;
        }
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
        if (fprintf(file, "%.17g,%.17g,%.17g,%.17g,%.17g\n", s.time_s, s.x_m,
                    s.y_m, s.vx_mps, s.vy_mps) < 0) {
            fclose(file);
            return -1;
        }
    }
    return fclose(file) == 0 ? 0 : -1;
}
