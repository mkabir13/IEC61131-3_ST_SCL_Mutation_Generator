/*
 * iec_lib_math.c -- defines the 12 iec_lib_* math functions that
 * matiec/lib/C/iec_std_lib.h declares (for use by generated code
 * implementing LN, LOG, EXP, SIN, COS, TAN, ASIN, ACOS, ATAN, SQRT, MOD,
 * EXPT/POW) but never actually defines anywhere in the bundled
 * reference harness. Found the same way as the common_ticktime__ and
 * __CURRENT_TIME bugs earlier in this project: a real ST program that
 * used one of these (via SHR/bit operations pulling in the numeric
 * function family) failed to LINK with "undefined reference to
 * iec_lib_fmod" etc. -- not a compile error, so it wasn't caught by
 * MATIEC's own syntax/type checking, only by gcc's linker.
 *
 * These are plain wrappers around the C standard library's <math.h> --
 * nothing custom, just what was missing. Link this file alongside
 * Config*.c/Res*.c/plc.c/main.c whenever a program might use any IEC
 * numeric function beyond the basic arithmetic operators.
 */

#include <math.h>

double iec_lib_acos(double x)  { return acos(x); }
double iec_lib_asin(double x)  { return asin(x); }
double iec_lib_atan(double x)  { return atan(x); }
double iec_lib_cos(double x)   { return cos(x); }
double iec_lib_exp(double x)   { return exp(x); }
double iec_lib_fmod(double x, double y) { return fmod(x, y); }
double iec_lib_log(double x)   { return log(x); }
double iec_lib_log10(double x) { return log10(x); }
double iec_lib_pow(double x, double y)  { return pow(x, y); }
double iec_lib_sin(double x)   { return sin(x); }
double iec_lib_sqrt(double x)  { return sqrt(x); }
double iec_lib_tan(double x)   { return tan(x); }
