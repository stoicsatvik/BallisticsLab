#include <stdio.h>

#include "physics.h"

int main(void) {
    double speed_mps;
    double angle_deg;
    double mass_kg;

    puts("BallisticsLab v0.1 — generic projectile model");
    puts("Assumptions: vacuum, flat ground, constant gravity, no drag.\n");

    printf("Initial speed (m/s): ");
    if (scanf("%lf", &speed_mps) != 1 || speed_mps < 0.0) {
        fputs("Invalid speed.\n", stderr);
        return 1;
    }

    printf("Launch angle (degrees, 0-90): ");
    if (scanf("%lf", &angle_deg) != 1 || angle_deg < 0.0 || angle_deg > 90.0) {
        fputs("Invalid angle.\n", stderr);
        return 1;
    }

    printf("Projectile mass (kg): ");
    if (scanf("%lf", &mass_kg) != 1 || mass_kg <= 0.0) {
        fputs("Invalid mass.\n", stderr);
        return 1;
    }

    const TrajectoryResult result = bl_vacuum_trajectory(speed_mps, angle_deg);

    puts("\nResults");
    puts("-------");
    printf("Horizontal velocity: %.3f m/s\n", result.horizontal_velocity_mps);
    printf("Vertical velocity:   %.3f m/s\n", result.vertical_velocity_mps);
    printf("Flight time:         %.3f s\n", result.flight_time_s);
    printf("Range:               %.3f m\n", result.range_m);
    printf("Maximum height:      %.3f m\n", result.max_height_m);
    printf("Momentum:            %.3f kg·m/s\n", bl_momentum(mass_kg, speed_mps));
    printf("Kinetic energy:      %.3f J\n", bl_kinetic_energy(mass_kg, speed_mps));

    puts("\nThis is a classroom projectile model, not a firing-solution calculator.");
    return 0;
}
