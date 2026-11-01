#ifndef BALLISTICSLAB_TIME2_H
#define BALLISTICSLAB_TIME2_H
/* Generic two-component binary64 timestamps; no trajectory/targeting API. */
typedef struct { double hi; double lo; } BlTime2;
int bl_time2_make(double hi, double lo, BlTime2 *out);
int bl_time2_add(BlTime2 a, BlTime2 b, BlTime2 *out);
int bl_time2_compare(BlTime2 a, BlTime2 b);
#endif
