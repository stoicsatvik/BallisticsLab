#include <math.h>
#include <stdio.h>

static const double G = 9.80665;
static const double PI = 3.14159265358979323846;

static double deg_to_rad(double degrees) {
    return degrees * PI / 180.0;
}

static double kinetic_energy(double mass_kg, double speed_mps) {
    return 0.5 * mass_kg * speed_mps * speed_mps;
}

static double momentum(double mass_kg, double speed_mps) {
    return mass_kg * speed_mps;
}

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

    const double theta = deg_to_rad(angle_deg);
    const double vx = speed_mps * cos(theta);
    const double vy = speed_mps * sin(theta);

    const double flight_time = (2.0 * vy) / G;
    const double range_m = vx * flight_time;
    const double max_height_m = (vy * vy) / (2.0 * G);

    printf("\nResults\n");
    printf("-------\n");
    printf("Horizontal velocity: %.3f m/s\n", vx);
    printf("Vertical velocity:   %.3f m/s\n", vy);
    printf("Flight time:         %.3f s\n", flight_time);
    printf("Range:               %.3f m\n", range_m);
    printf("Maximum height:      %.3f m\n", max_height_m);
    printf("Momentum:            %.3f kg·m/s\n", momentum(mass_kg, speed_mps));
    printf("Kinetic energy:      %.3f J\n", kinetic_energy(mass_kg, speed_mps));

    puts("\nThis is a classroom projectile model, not a firing-solution calculator.");
    return 0;
}
