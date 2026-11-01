#ifndef BALLISTICSLAB_TIME2_H
#define BALLISTICSLAB_TIME2_H
/* Generic two-component binary64 timestamps; no trajectory/targeting API. */
typedef struct { double hi; double lo; } BlTime2;
int bl_time2_make(double hi, double lo, BlTime2 *out);
int bl_time2_add(BlTime2 a, BlTime2 b, BlTime2 *out);
int bl_time2_compare(BlTime2 a, BlTime2 b);
/* Fail closed if a nonzero signed delta cannot change the represented time
 * in its mathematical direction. Inputs are normalized before comparison.
 * A zero delta must leave the normalized time unchanged. On failure, *out
 * is untouched. This does not guarantee exact rational addition. */
int bl_time2_add_strict(BlTime2 a, BlTime2 delta, BlTime2 *out);
#endif
