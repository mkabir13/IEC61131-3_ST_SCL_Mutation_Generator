#ifndef __POUS_H
#define __POUS_H

#include "accessor.h"
#include "iec_std_lib.h"

// FUNCTION_BLOCK FT_DERIV
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(REAL,IN)
  __DECLARE_VAR(REAL,K)
  __DECLARE_VAR(BOOL,RUN)
  __DECLARE_VAR(REAL,OUT)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(REAL,OLD)
  __DECLARE_VAR(UDINT,TX)
  __DECLARE_VAR(UDINT,LAST)
  __DECLARE_VAR(BOOL,INIT)
  __DECLARE_VAR(REAL,TC)

} FT_DERIV_data__;

// FUNCTION_BLOCK FT_PIWL
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(REAL,IN)
  __DECLARE_VAR(REAL,KP)
  __DECLARE_VAR(REAL,KI)
  __DECLARE_VAR(REAL,LIM_L)
  __DECLARE_VAR(REAL,LIM_H)
  __DECLARE_VAR(BOOL,RST)
  __DECLARE_VAR(REAL,Y)
  __DECLARE_VAR(BOOL,LIM)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(BOOL,INIT)
  __DECLARE_VAR(UDINT,TX)
  __DECLARE_VAR(REAL,TC)
  __DECLARE_VAR(UDINT,T_LAST)
  __DECLARE_VAR(REAL,IN_LAST)
  __DECLARE_VAR(REAL,I)
  __DECLARE_VAR(REAL,P)

} FT_PIWL_data__;

// FUNCTION_BLOCK INTEGRATE
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,_E)
  __DECLARE_VAR(REAL,X)
  __DECLARE_VAR(REAL,K)
  __DECLARE_VAR(REAL,Y)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(REAL,X_LAST)
  __DECLARE_VAR(BOOL,INIT)
  __DECLARE_VAR(UDINT,LAST)
  __DECLARE_VAR(UDINT,TX)

} INTEGRATE_data__;

// FUNCTION_BLOCK LAMBERT_W
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(REAL,X)
  __DECLARE_VAR(REAL,OUT)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(REAL,W)
  __DECLARE_VAR(INT,I)
  __DECLARE_VAR(REAL,WE)
  __DECLARE_VAR(REAL,W1E)
  __DECLARE_VAR(REAL,EWX)
  __DECLARE_VAR(DWORD,LAST)

} LAMBERT_W_data__;

// PROGRAM TESTRUNNERPROGRAM
// Data part
typedef struct {
  // PROGRAM Interface - IN, OUT, IN_OUT variables

  // PROGRAM private variables - TEMP, private and located variables
  __DECLARE_LOCATED(BOOL,TESTRESULT)
  __DECLARE_LOCATED(INT,TOTALTESTS)
  __DECLARE_LOCATED(INT,PASSEDTESTS)

} TESTRUNNERPROGRAM_data__;

#endif //__POUS_H
