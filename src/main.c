#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "integrator.h"
#include "physics.h"

#define BL_MAX_TRACE_SAMPLES 1000000U

static int parse_positive_double(const char *text, double *value) {
    char *end = NULL;
    const double parsed = strtod(text, &end);
    if (end == text || *end != '\0' || !isfinite(parsed) || parsed <= 0.0) {
        return 0;
    }
    *value = parsed;
    return 1;
}

int main(int argc, char **argv) {
    const char *csv_path = NULL;
    double dt_s = 0.0;

    if (argc == 4 && strcmp(argv[1], "--csv") == 0) {
        csv_path = argv[2];
        if (csv_path[0] == '\0' || !parse_positive_double(argv[3], &dt_s)) {
            fputs("Usage: ./ballisticslab [--csv PATH DT_SECONDS]\n", stderr);
            return 1;
        }
    } else if (argc != 1) {
        fputs("Usage: ./ballisticslab [--csv PATH DT_SECONDS]\n", stderr);
        return 1;
    }

    double speed_mps;
    double angle_deg;
    double mass_kg;

    puts("BallisticsLab v0.2 — generic educational projectile model");
    puts("Assumptions: vacuum, flat ground, constant gravity, no drag.\n");

    printf("Initial speed (m/s): ");
    if (scanf("%lf", &speed_mps) != 1 || !isfinite(speed_mps) || speed_mps < 0.0) {
        fputs("Invalid speed.\n", stderr);
        return 1;
    }

    printf("Launch angle (degrees, 0-90): ");
    if (scanf("%lf", &angle_deg) != 1 || !isfinite(angle_deg) || angle_deg < 0.0 || angle_deg > 90.0) {
        fputs("Invalid angle.\n", stderr);
        return 1;
    }

    printf("Mass (kg, for momentum/energy only): ");
    if (scanf("%lf", &mass_kg) != 1 || !isfinite(mass_kg) || mass_kg <= 0.0) {
        fputs("Invalid mass.\n", stderr);
        return 1;
    }

    const TrajectoryResult result = bl_vacuum_trajectory(speed_mps, angle_deg);

    puts("\nAnalytical vacuum reference");
    puts("---------------------------");
    printf("Horizontal velocity: %.3f m/s\n", result.horizontal_velocity_mps);
    printf("Vertical velocity:   %.3f m/s\n", result.vertical_velocity_mps);
    printf("Flight time:         %.3f s\n", result.flight_time_s);
    printf("Range:               %.3f m\n", result.range_m);
    printf("Maximum height:      %.3f m\n", result.max_height_m);
    printf("Momentum:            %.3f kg·m/s\n", bl_momentum(mass_kg, speed_mps));
    printf("Kinetic energy:      %.3f J\n", bl_kinetic_energy(mass_kg, speed_mps));

    if (csv_path != NULL) {
        const double capacity_value = ceil(result.flight_time_s / dt_s) + 4.0;
        if (!isfinite(capacity_value) || capacity_value > (double)BL_MAX_TRACE_SAMPLES) {
            fputs("Requested time step exceeds the trace sample limit.\n", stderr);
            return 1;
        }
        const size_t capacity = capacity_value < 1.0 ? 1U : (size_t)capacity_value;
        TrajectorySample *samples = calloc(capacity, sizeof(*samples));
        if (samples == NULL) {
            fputs("Could not allocate trajectory samples.\n", stderr);
            return 1;
        }

        size_t sample_count = 0;
        const BLSimulationStatus status = bl_simulate_vacuum(
            speed_mps, angle_deg, dt_s, samples, capacity, &sample_count
        );
        if (status != BL_SIM_OK) {
            free(samples);
            fputs("Numerical simulation failed; no CSV written.\n", stderr);
            return 1;
        }

        FILE *csv = fopen(csv_path, "w");
        if (csv == NULL) {
            free(samples);
            perror("Could not open CSV path");
            return 1;
        }
        const int write_ok = bl_write_trajectory_csv(csv, samples, sample_count);
        const int close_ok = fclose(csv) == 0;
        free(samples);
        if (!write_ok || !close_ok) {
            fputs("CSV write failed.\n", stderr);
            return 1;
        }
        printf("\nWrote %zu trajectory samples to %s (dt = %.6g s).\n", sample_count, csv_path, dt_s);
    }

    puts("\nClassroom model only: no drag, no wind, no terrain, no firing-solution or targeting use.");
    return 0;
}
