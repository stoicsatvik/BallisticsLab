#ifndef BALLISTICSLAB_NUMERICS_H
#define BALLISTICSLAB_NUMERICS_H

#include <stdio.h>

typedef struct {
    double time_s;
    double x_m;
    double y_m;
    double vx_mps;
    double vy_mps;
} BLParticleState;

/* Textbook point-mass motion under uniform downward gravity. No drag or targeting. */
int bl_step_uniform_gravity(BLParticleState *state, double dt_s, double gravity_mps2);

/* Simulate a stationary ball dropped from a height, with the ground at y=0.
 * The final CSV row is the interpolated impact state. Returns 0 on success.
 * Invalid inputs, I/O errors and insufficient step budgets return nonzero. */
int bl_write_drop_csv(FILE *output, double height_m, double gravity_mps2,
                      double dt_s, unsigned max_steps, double *impact_time_s);

#endif
