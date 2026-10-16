/*
 *  matiec - a compiler for the programming languages defined in IEC 61131-3
 *
 *  Copyright (C) 2009-2011  Mario de Sousa (msousa@fe.up.pt)
 *  Copyright (C) 2007-2011  Laurent Bessard and Edouard Tisserant
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 *
 * This code is made available on the understanding that it will not be
 * used in safety-critical situations without a full and competent review.
 *
 *
 * Simple PLC run cycle test implementation - prints every located at each cycle
 *
 * FIXED (found while building AgenTest-ST's DistinguishSearch): the
 * original bundled version declares `void run()` with NO parameters, but
 * main.c calls `run(CURRENT_TIME.tv_sec, CURRENT_TIME.tv_nsec)`. In C,
 * calling a function declared with empty `()` (old-style "unspecified
 * arguments", not `(void)`) with extra arguments compiles without error --
 * the arguments are silently discarded. The global `__CURRENT_TIME` that
 * TON/TOF/TP/etc. read to compute elapsed time was NEVER being updated,
 * so every timer-dependent FUNCTION_BLOCK never saw its preset elapse,
 * regardless of preset value or real wall-clock time. Confirmed by
 * testing a TON with PT := T#1S through T#5S: none ever fired, even after
 * 15+ real seconds. Fixed by accepting the real elapsed time and writing
 * it into __CURRENT_TIME before running the program logic each scan.
 */

#include "iec_std_lib.h"
#include <stdio.h>

#define __print_BOOL(name) printf("  %s = (BOOL) %s\n",#name, name?"TRUE":"FALSE");
#define __print_SINT(name) printf("  %s = (SINT) %d\n",#name, name);
#define __print_INT(name) printf("  %s = (INT) %d\n",#name, name);
#define __print_DINT(name) printf("  %s = (DINT) %d\n",#name, name);
#define __print_LINT(name) printf("  %s = (LINT) %d\n",#name, name);
#define __print_USINT(name) printf("  %s = (USINT) %u\n",#name, name);
#define __print_UINT(name) printf("  %s = (UINT) %u\n",#name, name);
#define __print_UDINT(name) printf("  %s = (UDINT) %u\n",#name, name);
#define __print_ULINT(name) printf("  %s = (ULINT) %lu\n",#name, name);
#define __print_REAL(name) printf("  %s = (REAL) %f\n",#name, (double)name);
#define __print_LREAL(name) printf("  %s = (LREAL) %f\n",#name, (double)name);
#define __print_TIME(name) {STRING __tmp = __time_to_string(name);__tmp.body[__tmp.len] = 0; printf("  %s = (TIME) %*s\n",#name, __tmp.len, &__tmp.body);}
#define __print_DATE(name) {STRING __tmp = __date_to_string(name);__tmp.body[__tmp.len] = 0; printf("  %s = (DATE) %*s\n",#name, __tmp.len, &__tmp.body);}
#define __print_TOD(name) {STRING __tmp = __tod_to_string(name);__tmp.body[__tmp.len] = 0; printf("  %s = (TOD) %*s\n",#name, __tmp.len, &__tmp.body);}
#define __print_DT(name) {STRING __tmp = __dt_to_string(name);__tmp.body[__tmp.len] = 0; printf("  %s = (DT) %*s\n",#name, __tmp.len, &__tmp.body);}
#define __print_STRING(name) printf("  %s = (STRING) {%d, \"%*s\"}\n",#name, name->len, name->len, &name->body);
#define __print_BYTE(name) printf("  %s = (BYTE) 0x%2.2x\n",#name, name);
#define __print_WORD(name) printf("  %s = (WORD) 0x%4.4x\n",#name, name);
#define __print_DWORD(name) printf("  %s = (DWORD) 0x%8.8x\n",#name, name);
#define __print_LWORD(name) printf("  %s = (LWORD) 0x%16.16lx\n",#name, name);
/*
 * Functions and variables provied by generated C softPLC
 **/ 
void config_run__(int tick);
void config_init__(void);

/*
 *  Functions and variables to export to generated C softPLC
 **/
 
TIME __CURRENT_TIME;

#define __LOCATED_VAR(type, name, ...) type __##name;
#include "LOCATED_VARIABLES.h"
#undef __LOCATED_VAR
#define __LOCATED_VAR(type, name, ...) type* name = &__##name;
#include "LOCATED_VARIABLES.h"
#undef __LOCATED_VAR

static int tick = 0;
static long first_sec = 0;
static int have_first = 0;

/* FIXED: now accepts the real elapsed time from main.c and actually uses
 * it to update __CURRENT_TIME (relative to the first call, so it starts
 * near zero rather than a large epoch value) -- this is what
 * TON/TOF/TP/etc. actually read to compute their elapsed time.
 */
void run(long sec, long nsec)
{
    if (!have_first) {
        first_sec = sec;
        have_first = 1;
    }
    __CURRENT_TIME.tv_sec = sec - first_sec;
    __CURRENT_TIME.tv_nsec = nsec;

    printf("Tick %d\n",tick);
    config_run__(tick++);
    printf("  Located variables : \n");
#define __LOCATED_VAR(type, name,...) __print_##type(name);
#include "LOCATED_VARIABLES.h"
#undef __LOCATED_VAR
}
