#include "numerics.h"

#include <math.h>

int bl_step_uniform_gravity(BLParticleState *state, double dt_s, double gravity_mps2) {
    if (!state || !isfinite(dt_s) || dt_s <= 0.0 ||
        !isfinite(gravity_mps2) || gravity_mps2 <= 0.0 ||
        !isfinite(state->time_s) || !isfinite(state->x_m) ||
        !isfinite(state->y_m) || !isfinite(state->vx_mps) ||
        !isfinite(state->vy_mps)) {
        return 1;
    }

    /* Velocity-Verlet is exact for constant acceleration, up to roundoff. */
    const double next_x = state->x_m + state->vx_mps * dt_s;
    const double next_y = state->y_m + state->vy_mps * dt_s -
                          0.5 * gravity_mps2 * dt_s * dt_s;
    const double next_vy = state->vy_mps - gravity_mps2 * dt_s;
    const double next_time = state->time_s + dt_s;
    if (!isfinite(next_x) || !isfinite(next_y) ||
        !isfinite(next_vy) || !isfinite(next_time)) {
        return 1;
    }
    state->x_m = next_x;
    state->y_m = next_y;
    state->vy_mps = next_vy;
    state->time_s = next_time;
    return 0;
}

static int write_row(FILE *output, const BLParticleState *s) {
    return fprintf(output, "%.12g,%.12g,%.12g,%.12g,%.12g\n",
                   s->time_s, s->x_m, s->y_m, s->vx_mps, s->vy_mps) < 0;
}

int bl_write_drop_csv(FILE *output, double height_m, double gravity_mps2,
                      double dt_s, unsigned max_steps, double *impact_time_s) {
    if (!output || !impact_time_s || !isfinite(height_m) || height_m < 0.0 ||
        !isfinite(gravity_mps2) || gravity_mps2 <= 0.0 ||
        !isfinite(dt_s) || dt_s <= 0.0 || max_steps == 0) {
        return 1;
    }
    BLParticleState state = {0.0, 0.0, height_m, 0.0, 0.0};
    if (fputs("time_s,x_m,y_m,vx_mps,vy_mps\n", output) == EOF ||
        write_row(output, &state)) {
        return 2;
    }
    if (height_m == 0.0) {
        *impact_time_s = 0.0;
        return 0;
    }

    for (unsigned step = 0; step < max_steps; ++step) {
        BLParticleState previous = state;
        if (bl_step_uniform_gravity(&state, dt_s, gravity_mps2)) {
            return 1;
        }
        if (state.y_m <= 0.0) {
            /* Solve y(t)=y0+vy0*t-g*t^2/2 for the crossing in this step. */
            const double discriminant = previous.vy_mps * previous.vy_mps +
                                        2.0 * gravity_mps2 * previous.y_m;
            if (!isfinite(discriminant) || discriminant < 0.0) {
                return 1;
            }
            const double root = (sqrt(discriminant) + previous.vy_mps) /
                                gravity_mps2;
            if (!isfinite(root) || root < 0.0 || root > dt_s * (1.0 + 1e-10)) {
                return 1;
            }
            BLParticleState impact = previous;
            if (bl_step_uniform_gravity(&impact, root, gravity_mps2)) {
                return 1;
            }
            impact.y_m = 0.0;
            if (write_row(output, &impact)) {
                return 2;
            }
            *impact_time_s = impact.time_s;
            return 0;
        }
        if (write_row(output, &state)) {
            return 2;
        }
    }
    return 3;
}
