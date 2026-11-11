#include "integrator.h"

#include <math.h>
#include <stdint.h>

#include "physics.h"

static const double BL_G = 9.80665;

static int finite_positive(double value) {
    return isfinite(value) && value > 0.0;
}

BLSimulationStatus bl_simulate_vacuum(
    double speed_mps,
    double angle_deg,
    double dt_s,
    TrajectorySample *samples,
    size_t capacity,
    size_t *sample_count
) {
    if (sample_count == NULL) {
        return BL_SIM_INVALID_ARGUMENT;
    }
    *sample_count = 0;

    if (!isfinite(speed_mps) || speed_mps < 0.0 ||
        !isfinite(angle_deg) || angle_deg < 0.0 || angle_deg > 90.0 ||
        !finite_positive(dt_s) || samples == NULL || capacity == 0) {
        return BL_SIM_INVALID_ARGUMENT;
    }

    const TrajectoryResult analytic = bl_vacuum_trajectory(speed_mps, angle_deg);
    const double theta = bl_deg_to_rad(angle_deg);
    const double vx0 = speed_mps * cos(theta);
    const double vy0 = speed_mps * sin(theta);

    size_t required_capacity = 1;
    if (vy0 > 0.0) {
        const double step_ratio = analytic.flight_time_s / dt_s;
        /*
         * On 64-bit platforms, converting SIZE_MAX - 4 to double can round
         * upward to 2^64. Reject equality too, before an out-of-range
         * floating-point-to-size_t conversion can occur.
         */
        if (!isfinite(step_ratio) || step_ratio >= (double)(SIZE_MAX - 4)) {
            return BL_SIM_INSUFFICIENT_CAPACITY;
        }
        required_capacity = (size_t)ceil(step_ratio) + 4;
    }
    if (capacity < required_capacity) {
        return BL_SIM_INSUFFICIENT_CAPACITY;
    }

    TrajectorySample current = {
        .time_s = 0.0,
        .x_m = 0.0,
        .y_m = 0.0,
        .vx_mps = vx0,
        .vy_mps = vy0,
    };
    samples[0] = current;
    *sample_count = 1;

    if (vy0 <= 0.0) {
        return BL_SIM_OK;
    }

    for (size_t step = 0; step < required_capacity - 1; ++step) {
        TrajectorySample next = {
            .time_s = current.time_s + dt_s,
            .x_m = current.x_m + current.vx_mps * dt_s,
            .y_m = current.y_m + current.vy_mps * dt_s,
            .vx_mps = current.vx_mps,
            .vy_mps = current.vy_mps - BL_G * dt_s,
        };

        if (next.y_m <= 0.0) {
            const double denominator = current.y_m - next.y_m;
            const double fraction = denominator > 0.0 ? current.y_m / denominator : 0.0;
            TrajectorySample landing = {
                .time_s = current.time_s + fraction * dt_s,
                .x_m = current.x_m + fraction * (next.x_m - current.x_m),
                .y_m = 0.0,
                .vx_mps = current.vx_mps,
                .vy_mps = current.vy_mps + fraction * (next.vy_mps - current.vy_mps),
            };
            samples[*sample_count] = landing;
            *sample_count += 1;
            return BL_SIM_OK;
        }

        samples[*sample_count] = next;
        *sample_count += 1;
        current = next;
    }

    *sample_count = 0;
    return BL_SIM_INSUFFICIENT_CAPACITY;
}

int bl_write_trajectory_csv(FILE *stream, const TrajectorySample *samples, size_t sample_count) {
    if (stream == NULL || samples == NULL || sample_count == 0) {
        return 0;
    }

    if (fprintf(stream, "time_s,x_m,y_m,vx_mps,vy_mps\n") < 0) {
        return 0;
    }

    for (size_t i = 0; i < sample_count; ++i) {
        if (fprintf(
                stream,
                "%.9g,%.9g,%.9g,%.9g,%.9g\n",
                samples[i].time_s,
                samples[i].x_m,
                samples[i].y_m,
                samples[i].vx_mps,
                samples[i].vy_mps
            ) < 0) {
            return 0;
        }
    }

    return ferror(stream) == 0;
}
