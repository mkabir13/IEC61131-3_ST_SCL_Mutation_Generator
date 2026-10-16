static BOOL ___BIT_OF_DWORD(
  BOOL EN, 
  BOOL *__ENO, 
  DWORD IN, 
  INT N);
static BOOL ___SIGN_R(
  BOOL EN, 
  BOOL *__ENO, 
  REAL IN);
static INT ___FLOOR(
  BOOL EN, 
  BOOL *__ENO, 
  REAL X);
static DINT ___FLOOR2(
  BOOL EN, 
  BOOL *__ENO, 
  REAL X);
static REAL ___MODR(
  BOOL EN, 
  BOOL *__ENO, 
  REAL IN, 
  REAL DIVI);
static BYTE ___REVERSE(
  BOOL EN, 
  BOOL *__ENO, 
  BYTE IN);
static DWORD ___REFLECT(
  BOOL EN, 
  BOOL *__ENO, 
  DWORD DI, 
  INT L);
static BYTE ___BIT_LOAD_B(
  BOOL EN, 
  BOOL *__ENO, 
  BYTE IN, 
  BOOL VAL, 
  INT POS);
static INT ____BYTE_TO_INT(
  BOOL EN, 
  BOOL *__ENO, 
  BYTE IN);
static UDINT ___T_PLC_MS(
  BOOL EN, 
  BOOL *__ENO, 
  BOOL DEBUG);
static UDINT ___T_PLC_US(
  BOOL EN, 
  BOOL *__ENO, 
  BOOL DEBUG);
static void FT_DERIV_init__(FT_DERIV_data__ *data__, BOOL retain);
static void FT_DERIV_body__(FT_DERIV_data__ *data__);
static void FT_PIWL_init__(FT_PIWL_data__ *data__, BOOL retain);
static void FT_PIWL_body__(FT_PIWL_data__ *data__);
static void INTEGRATE_init__(INTEGRATE_data__ *data__, BOOL retain);
static void INTEGRATE_body__(INTEGRATE_data__ *data__);
static void GEN_SIN_init__(GEN_SIN_data__ *data__, BOOL retain);
static void GEN_SIN_body__(GEN_SIN_data__ *data__);
static void TESTRUNNERPROGRAM_init__(TESTRUNNERPROGRAM_data__ *data__, BOOL retain);
static void TESTRUNNERPROGRAM_body__(TESTRUNNERPROGRAM_data__ *data__);

static BOOL ___BIT_OF_DWORD(
  BOOL EN, 
  BOOL *__ENO, 
  DWORD IN, 
  INT N)
{
  BOOL ENO = __BOOL_LITERAL(TRUE);
  BOOL BIT_OF_DWORD = __BOOL_LITERAL(FALSE);

  // Control execution
  if (!EN) {
    if (__ENO != NULL) {
      *__ENO = __BOOL_LITERAL(FALSE);
    }
    return BIT_OF_DWORD;
  }
#line 8 "../Tests/TestCode.st"
  BIT_OF_DWORD = ((___SHR__DWORD__DWORD__INT(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (DWORD)IN,
    (INT)N) & __DWORD_LITERAL(0x1)) > __DWORD_LITERAL(0));

  goto __end;

__end:
  if (__ENO != NULL) {
    *__ENO = ENO;
  }
  return BIT_OF_DWORD;
}


static BOOL ___SIGN_R(
  BOOL EN, 
  BOOL *__ENO, 
  REAL IN)
{
  BOOL ENO = __BOOL_LITERAL(TRUE);
  BOOL SIGN_R = __BOOL_LITERAL(FALSE);

  // Control execution
  if (!EN) {
    if (__ENO != NULL) {
      *__ENO = __BOOL_LITERAL(FALSE);
    }
    return SIGN_R;
  }
#line 17 "../Tests/TestCode.st"
  SIGN_R = (IN < __REAL_LITERAL(0.0));

  goto __end;

__end:
  if (__ENO != NULL) {
    *__ENO = ENO;
  }
  return SIGN_R;
}


static INT ___FLOOR(
  BOOL EN, 
  BOOL *__ENO, 
  REAL X)
{
  BOOL ENO = __BOOL_LITERAL(TRUE);
  INT FLOOR = 0;

  // Control execution
  if (!EN) {
    if (__ENO != NULL) {
      *__ENO = __BOOL_LITERAL(FALSE);
    }
    return FLOOR;
  }
#line 26 "../Tests/TestCode.st"
  FLOOR = ___REAL_TO_INT(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (REAL)X);
#line 27 "../Tests/TestCode.st"
  if ((___INT_TO_REAL(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (INT)FLOOR) > X)) {
#line 28 "../Tests/TestCode.st"
    FLOOR = (FLOOR - __INT_LITERAL(1));
  };

  goto __end;

__end:
  if (__ENO != NULL) {
    *__ENO = ENO;
  }
  return FLOOR;
}


static DINT ___FLOOR2(
  BOOL EN, 
  BOOL *__ENO, 
  REAL X)
{
  BOOL ENO = __BOOL_LITERAL(TRUE);
  DINT FLOOR2 = 0;

  // Control execution
  if (!EN) {
    if (__ENO != NULL) {
      *__ENO = __BOOL_LITERAL(FALSE);
    }
    return FLOOR2;
  }
#line 38 "../Tests/TestCode.st"
  FLOOR2 = ___REAL_TO_DINT(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (REAL)X);
#line 39 "../Tests/TestCode.st"
  if ((___DINT_TO_REAL(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (DINT)FLOOR2) > X)) {
#line 40 "../Tests/TestCode.st"
    FLOOR2 = (FLOOR2 - __DINT_LITERAL(1));
  };

  goto __end;

__end:
  if (__ENO != NULL) {
    *__ENO = ENO;
  }
  return FLOOR2;
}


static REAL ___MODR(
  BOOL EN, 
  BOOL *__ENO, 
  REAL IN, 
  REAL DIVI)
{
  BOOL ENO = __BOOL_LITERAL(TRUE);
  REAL MODR = 0;

  // Control execution
  if (!EN) {
    if (__ENO != NULL) {
      *__ENO = __BOOL_LITERAL(FALSE);
    }
    return MODR;
  }
#line 51 "../Tests/TestCode.st"
  if ((DIVI == __REAL_LITERAL(0.0))) {
#line 52 "../Tests/TestCode.st"
    MODR = __REAL_LITERAL(0.0);
  } else {
#line 54 "../Tests/TestCode.st"
    MODR = (IN - (___DINT_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (DINT)___FLOOR2(
        (BOOL)__BOOL_LITERAL(TRUE),
        NULL,
        (REAL)(IN / DIVI))) * DIVI));
  };

  goto __end;

__end:
  if (__ENO != NULL) {
    *__ENO = ENO;
  }
  return MODR;
}


static BYTE ___REVERSE(
  BOOL EN, 
  BOOL *__ENO, 
  BYTE IN)
{
  BOOL ENO = __BOOL_LITERAL(TRUE);
  BYTE REVERSE = 0;

  // Control execution
  if (!EN) {
    if (__ENO != NULL) {
      *__ENO = __BOOL_LITERAL(FALSE);
    }
    return REVERSE;
  }
#line 65 "../Tests/TestCode.st"
  REVERSE = (((((___SHL__BYTE__BYTE__SINT(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (BYTE)IN,
    (SINT)__SINT_LITERAL(7)) | ___SHR__BYTE__BYTE__SINT(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (BYTE)IN,
    (SINT)__SINT_LITERAL(7))) | (___ROR__BYTE__BYTE__SINT(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (BYTE)IN,
    (SINT)__SINT_LITERAL(3)) & __BYTE_LITERAL(0x44))) | (___ROL__BYTE__BYTE__SINT(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (BYTE)IN,
    (SINT)__SINT_LITERAL(3)) & __BYTE_LITERAL(0x22))) | (___SHL__BYTE__BYTE__SINT(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (BYTE)IN,
    (SINT)__SINT_LITERAL(1)) & __BYTE_LITERAL(0x10))) | (___SHR__BYTE__BYTE__SINT(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (BYTE)IN,
    (SINT)__SINT_LITERAL(1)) & __BYTE_LITERAL(0x08)));

  goto __end;

__end:
  if (__ENO != NULL) {
    *__ENO = ENO;
  }
  return REVERSE;
}


static DWORD ___REFLECT(
  BOOL EN, 
  BOOL *__ENO, 
  DWORD DI, 
  INT L)
{
  BOOL ENO = __BOOL_LITERAL(TRUE);
  INT I = 0;
  DWORD _D = 0;
  DWORD REFLECT = 0;

  // Control execution
  if (!EN) {
    if (__ENO != NULL) {
      *__ENO = __BOOL_LITERAL(FALSE);
    }
    return REFLECT;
  }
#line 82 "../Tests/TestCode.st"
  _D = DI;
#line 83 "../Tests/TestCode.st"
  /* FOR ... */
  I = __INT_LITERAL(1);
  {
    int __do_increment = 0;
    while(1) {
      if(__do_increment){
        /* BY ... (of FOR loop) */
        I = (I + __INT_LITERAL(1));
      } else __do_increment = 1;
      if(I <= L      ){
#line 84 "../Tests/TestCode.st"
        REFLECT = (___SHL__DWORD__DWORD__SINT(
          (BOOL)__BOOL_LITERAL(TRUE),
          NULL,
          (DWORD)REFLECT,
          (SINT)__SINT_LITERAL(1)) | ___BOOL_TO_DWORD(
          (BOOL)__BOOL_LITERAL(TRUE),
          NULL,
          (BOOL)((_D & __DWORD_LITERAL(0x01)) > __DWORD_LITERAL(0))));
#line 85 "../Tests/TestCode.st"
        _D = ___SHR__DWORD__DWORD__SINT(
          (BOOL)__BOOL_LITERAL(TRUE),
          NULL,
          (DWORD)_D,
          (SINT)__SINT_LITERAL(1));
      }else break;
    }
  } /* END_FOR */;
#line 87 "../Tests/TestCode.st"
  REFLECT = (REFLECT | ___SHL__DWORD__DWORD__INT(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (DWORD)_D,
    (INT)L));

  goto __end;

__end:
  if (__ENO != NULL) {
    *__ENO = ENO;
  }
  return REFLECT;
}


static BYTE ___BIT_LOAD_B(
  BOOL EN, 
  BOOL *__ENO, 
  BYTE IN, 
  BOOL VAL, 
  INT POS)
{
  BOOL ENO = __BOOL_LITERAL(TRUE);
  BYTE BIT_LOAD_B = 0;

  // Control execution
  if (!EN) {
    if (__ENO != NULL) {
      *__ENO = __BOOL_LITERAL(FALSE);
    }
    return BIT_LOAD_B;
  }
#line 101 "../Tests/TestCode.st"
  if (VAL) {
#line 102 "../Tests/TestCode.st"
    BIT_LOAD_B = (IN | ___SHL__BYTE__BYTE__INT(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BYTE)__BYTE_LITERAL(1),
      (INT)POS));
  } else {
#line 104 "../Tests/TestCode.st"
    BIT_LOAD_B = (IN & ~(___SHL__BYTE__BYTE__INT(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BYTE)__BYTE_LITERAL(1),
      (INT)POS)));
  };

  goto __end;

__end:
  if (__ENO != NULL) {
    *__ENO = ENO;
  }
  return BIT_LOAD_B;
}


static INT ____BYTE_TO_INT(
  BOOL EN, 
  BOOL *__ENO, 
  BYTE IN)
{
  BOOL ENO = __BOOL_LITERAL(TRUE);
  INT _BYTE_TO_INT = 0;

  // Control execution
  if (!EN) {
    if (__ENO != NULL) {
      *__ENO = __BOOL_LITERAL(FALSE);
    }
    return _BYTE_TO_INT;
  }
#line 115 "../Tests/TestCode.st"
  _BYTE_TO_INT = ___USINT_TO_INT(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (USINT)___BYTE_TO_USINT(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BYTE)IN));

  goto __end;

__end:
  if (__ENO != NULL) {
    *__ENO = ENO;
  }
  return _BYTE_TO_INT;
}


static UDINT ___T_PLC_MS(
  BOOL EN, 
  BOOL *__ENO, 
  BOOL DEBUG)
{
  BOOL ENO = __BOOL_LITERAL(TRUE);
  UDINT TX = 0;
  INT N = __INT_LITERAL(0);
  UDINT OFFSET = __UDINT_LITERAL(0);
  DWORD TEMP = __DWORD_LITERAL(1);
  UDINT T_PLC_MS = 0;

  // Control execution
  if (!EN) {
    if (__ENO != NULL) {
      *__ENO = __BOOL_LITERAL(FALSE);
    }
    return T_PLC_MS;
  }
#line 133 "../Tests/TestCode.st"
  TX = __UDINT_LITERAL(0);
#line 134 "../Tests/TestCode.st"
  #define GetFbVar(var,...) __GET_VAR(data__->var,__VA_ARGS__)
  #define SetFbVar(var,val,...) __SET_VAR(data__->,var,__VA_ARGS__,val)
extern unsigned long __tick;
  extern unsigned long long common_ticktime__;
  unsigned long long ticktime_ms = (common_ticktime__)/1000000;
  UDINT plc_time = (UDINT)(ticktime_ms * (unsigned long long)__tick);
  TX = plc_time
  #undef GetFbVar
  #undef SetFbVar
;
#line 139 "../Tests/TestCode.st"
  T_PLC_MS = TX;
#line 140 "../Tests/TestCode.st"
  if (DEBUG) {
#line 141 "../Tests/TestCode.st"
    T_PLC_MS = ((___DWORD_TO_UDINT(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (DWORD)(___SHL__DWORD__DWORD__INT(
        (BOOL)__BOOL_LITERAL(TRUE),
        NULL,
        (DWORD)___UDINT_TO_DWORD(
          (BOOL)__BOOL_LITERAL(TRUE),
          NULL,
          (UDINT)T_PLC_MS),
        (INT)N) | ___SHL__DWORD__DWORD__INT(
        (BOOL)__BOOL_LITERAL(TRUE),
        NULL,
        (DWORD)TEMP,
        (INT)N))) - __UDINT_LITERAL(1)) + OFFSET);
  };
#line 145 "../Tests/TestCode.st"
  if (DEBUG) {
#line 146 "../Tests/TestCode.st"
    T_PLC_MS = ((___DWORD_TO_UDINT(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (DWORD)(___SHL__DWORD__DWORD__INT(
        (BOOL)__BOOL_LITERAL(TRUE),
        NULL,
        (DWORD)___UDINT_TO_DWORD(
          (BOOL)__BOOL_LITERAL(TRUE),
          NULL,
          (UDINT)T_PLC_MS),
        (INT)N) | ___SHL__DWORD__DWORD__INT(
        (BOOL)__BOOL_LITERAL(TRUE),
        NULL,
        (DWORD)TEMP,
        (INT)N))) - __UDINT_LITERAL(1)) + OFFSET);
  };

  goto __end;

__end:
  if (__ENO != NULL) {
    *__ENO = ENO;
  }
  return T_PLC_MS;
}


static UDINT ___T_PLC_US(
  BOOL EN, 
  BOOL *__ENO, 
  BOOL DEBUG)
{
  BOOL ENO = __BOOL_LITERAL(TRUE);
  UDINT TX = 0;
  INT N = __INT_LITERAL(0);
  UDINT OFFSET = __UDINT_LITERAL(0);
  DWORD TEMP = __DWORD_LITERAL(1);
  UDINT T_PLC_US = 0;

  // Control execution
  if (!EN) {
    if (__ENO != NULL) {
      *__ENO = __BOOL_LITERAL(FALSE);
    }
    return T_PLC_US;
  }
#line 178 "../Tests/TestCode.st"
  T_PLC_US = (TX * __UDINT_LITERAL(1000));
#line 179 "../Tests/TestCode.st"
  if (DEBUG) {
#line 180 "../Tests/TestCode.st"
    T_PLC_US = ((___DWORD_TO_UDINT(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (DWORD)(___SHL__DWORD__DWORD__INT(
        (BOOL)__BOOL_LITERAL(TRUE),
        NULL,
        (DWORD)___UDINT_TO_DWORD(
          (BOOL)__BOOL_LITERAL(TRUE),
          NULL,
          (UDINT)T_PLC_US),
        (INT)N) | ___SHL__DWORD__DWORD__INT(
        (BOOL)__BOOL_LITERAL(TRUE),
        NULL,
        (DWORD)TEMP,
        (INT)N))) - __UDINT_LITERAL(1)) + OFFSET);
  };

  goto __end;

__end:
  if (__ENO != NULL) {
    *__ENO = ENO;
  }
  return T_PLC_US;
}


static void FT_DERIV_init__(FT_DERIV_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->IN,0,retain)
  __INIT_VAR(data__->K,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->RUN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->OUT,0,retain)
  __INIT_VAR(data__->OLD,0,retain)
  __INIT_VAR(data__->TX,0,retain)
  __INIT_VAR(data__->LAST,0,retain)
  __INIT_VAR(data__->INIT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->TC,0,retain)
}

// Code part
static void FT_DERIV_body__(FT_DERIV_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

#line 217 "../Tests/TestCode.st"
  __SET_VAR(data__->,TX,,___T_PLC_US(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (BOOL)__BOOL_LITERAL(FALSE)));
#line 218 "../Tests/TestCode.st"
  __SET_VAR(data__->,TC,,___UDINT_TO_REAL(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UDINT)(__GET_VAR(data__->TX,) - __GET_VAR(data__->LAST,))));
#line 221 "../Tests/TestCode.st"
  if (!(__GET_VAR(data__->INIT,))) {
#line 222 "../Tests/TestCode.st"
    __SET_VAR(data__->,INIT,,__BOOL_LITERAL(TRUE));
#line 223 "../Tests/TestCode.st"
    __SET_VAR(data__->,OLD,,__GET_VAR(data__->IN,));
  } else if ((__GET_VAR(data__->RUN,) && (__GET_VAR(data__->TC,) > __REAL_LITERAL(0.0)))) {
#line 225 "../Tests/TestCode.st"
    __SET_VAR(data__->,OUT,,((((__GET_VAR(data__->IN,) - __GET_VAR(data__->OLD,)) / __GET_VAR(data__->TC,)) * __REAL_LITERAL(1000000.0)) * __GET_VAR(data__->K,)));
#line 226 "../Tests/TestCode.st"
    __SET_VAR(data__->,OLD,,__GET_VAR(data__->IN,));
  } else {
#line 228 "../Tests/TestCode.st"
    __SET_VAR(data__->,OUT,,__REAL_LITERAL(0.0));
  };
#line 231 "../Tests/TestCode.st"
  __SET_VAR(data__->,LAST,,__GET_VAR(data__->TX,));

  goto __end;

__end:
  return;
} // FT_DERIV_body__() 





static void FT_PIWL_init__(FT_PIWL_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->IN,0,retain)
  __INIT_VAR(data__->KP,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->KI,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->LIM_L,__REAL_LITERAL(-1.0E38),retain)
  __INIT_VAR(data__->LIM_H,__REAL_LITERAL(1.0E38),retain)
  __INIT_VAR(data__->RST,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->Y,0,retain)
  __INIT_VAR(data__->LIM,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->INIT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->TX,0,retain)
  __INIT_VAR(data__->TC,0,retain)
  __INIT_VAR(data__->T_LAST,0,retain)
  __INIT_VAR(data__->IN_LAST,0,retain)
  __INIT_VAR(data__->I,0,retain)
  __INIT_VAR(data__->P,0,retain)
}

// Code part
static void FT_PIWL_body__(FT_PIWL_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

#line 261 "../Tests/TestCode.st"
  if ((!(__GET_VAR(data__->INIT,)) || __GET_VAR(data__->RST,))) {
#line 262 "../Tests/TestCode.st"
    __SET_VAR(data__->,INIT,,__BOOL_LITERAL(TRUE));
#line 263 "../Tests/TestCode.st"
    __SET_VAR(data__->,IN_LAST,,__GET_VAR(data__->IN,));
#line 264 "../Tests/TestCode.st"
    __SET_VAR(data__->,T_LAST,,___T_PLC_US(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__BOOL_LITERAL(FALSE)));
#line 265 "../Tests/TestCode.st"
    __SET_VAR(data__->,I,,__REAL_LITERAL(0.0));
#line 266 "../Tests/TestCode.st"
    __SET_VAR(data__->,TC,,__REAL_LITERAL(0.0));
  } else {
#line 269 "../Tests/TestCode.st"
    __SET_VAR(data__->,TX,,___T_PLC_US(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__BOOL_LITERAL(FALSE)));
#line 270 "../Tests/TestCode.st"
    __SET_VAR(data__->,TC,,___UDINT_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (UDINT)(__GET_VAR(data__->TX,) - __GET_VAR(data__->T_LAST,))));
#line 271 "../Tests/TestCode.st"
    __SET_VAR(data__->,T_LAST,,__GET_VAR(data__->TX,));
#line 274 "../Tests/TestCode.st"
    __SET_VAR(data__->,P,,(__GET_VAR(data__->KP,) * __GET_VAR(data__->IN,)));
#line 277 "../Tests/TestCode.st"
    __SET_VAR(data__->,I,,(((((__GET_VAR(data__->IN,) + __GET_VAR(data__->IN_LAST,)) * __REAL_LITERAL(5.0E-7)) * __GET_VAR(data__->KI,)) * __GET_VAR(data__->TC,)) + __GET_VAR(data__->I,)));
#line 278 "../Tests/TestCode.st"
    __SET_VAR(data__->,IN_LAST,,__GET_VAR(data__->IN,));
#line 281 "../Tests/TestCode.st"
    __SET_VAR(data__->,Y,,(__GET_VAR(data__->P,) + __GET_VAR(data__->I,)));
#line 284 "../Tests/TestCode.st"
    if ((__GET_VAR(data__->Y,) >= __GET_VAR(data__->LIM_H,))) {
#line 285 "../Tests/TestCode.st"
      __SET_VAR(data__->,Y,,__GET_VAR(data__->LIM_H,));
#line 286 "../Tests/TestCode.st"
      if ((__GET_VAR(data__->KI,) != __REAL_LITERAL(0.0))) {
#line 287 "../Tests/TestCode.st"
        __SET_VAR(data__->,I,,(__GET_VAR(data__->LIM_H,) - __GET_VAR(data__->P,)));
      } else {
#line 289 "../Tests/TestCode.st"
        __SET_VAR(data__->,I,,__REAL_LITERAL(0.0));
      };
#line 291 "../Tests/TestCode.st"
      __SET_VAR(data__->,LIM,,__BOOL_LITERAL(TRUE));
    } else if ((__GET_VAR(data__->Y,) <= __GET_VAR(data__->LIM_L,))) {
#line 293 "../Tests/TestCode.st"
      __SET_VAR(data__->,Y,,__GET_VAR(data__->LIM_L,));
#line 294 "../Tests/TestCode.st"
      if ((__GET_VAR(data__->KI,) != __REAL_LITERAL(0.0))) {
#line 295 "../Tests/TestCode.st"
        __SET_VAR(data__->,I,,(__GET_VAR(data__->LIM_L,) - __GET_VAR(data__->P,)));
      } else {
#line 297 "../Tests/TestCode.st"
        __SET_VAR(data__->,I,,__REAL_LITERAL(0.0));
      };
#line 299 "../Tests/TestCode.st"
      __SET_VAR(data__->,LIM,,__BOOL_LITERAL(TRUE));
    } else {
#line 301 "../Tests/TestCode.st"
      __SET_VAR(data__->,LIM,,__BOOL_LITERAL(FALSE));
    };
  };

  goto __end;

__end:
  return;
} // FT_PIWL_body__() 





static void INTEGRATE_init__(INTEGRATE_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->_E,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->X,0,retain)
  __INIT_VAR(data__->K,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->Y,0,retain)
  __INIT_VAR(data__->X_LAST,0,retain)
  __INIT_VAR(data__->INIT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->LAST,0,retain)
  __INIT_VAR(data__->TX,0,retain)
}

// Code part
static void INTEGRATE_body__(INTEGRATE_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

#line 326 "../Tests/TestCode.st"
  __SET_VAR(data__->,TX,,___T_PLC_MS(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (BOOL)__BOOL_LITERAL(FALSE)));
#line 328 "../Tests/TestCode.st"
  if (!(__GET_VAR(data__->INIT,))) {
#line 329 "../Tests/TestCode.st"
    __SET_VAR(data__->,INIT,,__BOOL_LITERAL(TRUE));
#line 330 "../Tests/TestCode.st"
    __SET_VAR(data__->,X_LAST,,__GET_VAR(data__->X,));
  } else if (__GET_VAR(data__->_E,)) {
#line 332 "../Tests/TestCode.st"
    __SET_VAR(data__->,Y,,(((((__GET_VAR(data__->X,) + __GET_VAR(data__->X_LAST,)) * __REAL_LITERAL(0.5E-3)) * ___UDINT_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (UDINT)(__GET_VAR(data__->TX,) - __GET_VAR(data__->LAST,)))) * __GET_VAR(data__->K,)) + __GET_VAR(data__->Y,)));
#line 333 "../Tests/TestCode.st"
    __SET_VAR(data__->,X_LAST,,__GET_VAR(data__->X,));
  };
#line 335 "../Tests/TestCode.st"
  __SET_VAR(data__->,LAST,,__GET_VAR(data__->TX,));

  goto __end;

__end:
  return;
} // INTEGRATE_body__() 





static void GEN_SIN_init__(GEN_SIN_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->PT,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->AM,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->OS,0,retain)
  __INIT_VAR(data__->DL,0,retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->OUT,0,retain)
  __INIT_VAR(data__->TX,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->LAST,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->INIT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->TEMP,0,retain)
}

// Code part
static void GEN_SIN_body__(GEN_SIN_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

#line 360 "../Tests/TestCode.st"
  __SET_VAR(data__->,TX,,_____time_sub(___UDINT_TO_TIME(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UDINT)___T_PLC_MS(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__BOOL_LITERAL(FALSE))), __GET_VAR(data__->LAST,)));
#line 362 "../Tests/TestCode.st"
  __SET_VAR(data__->,DL,,___MODR(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (REAL)__GET_VAR(data__->DL,),
    (REAL)__REAL_LITERAL(2.0)));
#line 363 "../Tests/TestCode.st"
  if ((__GET_VAR(data__->DL,) < __REAL_LITERAL(0.0))) {
#line 363 "../Tests/TestCode.st"
    __SET_VAR(data__->,DL,,(__REAL_LITERAL(1.0) - __GET_VAR(data__->DL,)));
  };
#line 366 "../Tests/TestCode.st"
  if (!(__GET_VAR(data__->INIT,))) {
#line 367 "../Tests/TestCode.st"
    __SET_VAR(data__->,INIT,,__BOOL_LITERAL(TRUE));
#line 368 "../Tests/TestCode.st"
    __SET_VAR(data__->,LAST,,__GET_VAR(data__->TX,));
#line 369 "../Tests/TestCode.st"
    __SET_VAR(data__->,TX,,__time_to_timespec(1, 0, 0, 0, 0, 0));
  };
#line 373 "../Tests/TestCode.st"
  if (___GE_TIME(__BOOL_LITERAL(TRUE), NULL, 2, __GET_VAR(data__->TX,), __GET_VAR(data__->PT,))) {
#line 374 "../Tests/TestCode.st"
    __SET_VAR(data__->,LAST,,_____time_add(__GET_VAR(data__->LAST,), __GET_VAR(data__->PT,)));
#line 375 "../Tests/TestCode.st"
    __SET_VAR(data__->,TX,,_____time_sub(__GET_VAR(data__->TX,), __GET_VAR(data__->PT,)));
  };
#line 379 "../Tests/TestCode.st"
  if (___GT_TIME(__BOOL_LITERAL(TRUE), NULL, 2, __GET_VAR(data__->PT,), __time_to_timespec(1, 0, 0, 0, 0, 0))) {
#line 379 "../Tests/TestCode.st"
    __SET_VAR(data__->,TEMP,,___SIN__REAL__REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)((__REAL_LITERAL(6.283185307179586476) * ___TIME_TO_REAL(
        (BOOL)__BOOL_LITERAL(TRUE),
        NULL,
        (TIME)_____time_add(__GET_VAR(data__->TX,), ___MULTIME__TIME__TIME__REAL(
          (BOOL)__BOOL_LITERAL(TRUE),
          NULL,
          (TIME)__GET_VAR(data__->PT,),
          (REAL)__GET_VAR(data__->DL,))))) / ___TIME_TO_REAL(
        (BOOL)__BOOL_LITERAL(TRUE),
        NULL,
        (TIME)__GET_VAR(data__->PT,)))));
  };
#line 380 "../Tests/TestCode.st"
  __SET_VAR(data__->,OUT,,(((__GET_VAR(data__->AM,) * __REAL_LITERAL(0.5)) * __GET_VAR(data__->TEMP,)) + __GET_VAR(data__->OS,)));
#line 383 "../Tests/TestCode.st"
  __SET_VAR(data__->,Q,,!(___SIGN_R(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (REAL)__GET_VAR(data__->TEMP,))));

  goto __end;

__end:
  return;
} // GEN_SIN_body__() 





static void TESTRUNNERPROGRAM_init__(TESTRUNNERPROGRAM_data__ *data__, BOOL retain) {
  __INIT_LOCATED(BOOL,__QX0_0,data__->TESTRESULT,retain)
  __INIT_LOCATED_VALUE(data__->TESTRESULT,__BOOL_LITERAL(FALSE))
  __INIT_LOCATED(INT,__QW0,data__->TOTALTESTS,retain)
  __INIT_LOCATED_VALUE(data__->TOTALTESTS,__INT_LITERAL(0))
  __INIT_LOCATED(INT,__QW1,data__->PASSEDTESTS,retain)
  __INIT_LOCATED_VALUE(data__->PASSEDTESTS,__INT_LITERAL(0))
}

// Code part
static void TESTRUNNERPROGRAM_body__(TESTRUNNERPROGRAM_data__ *data__) {
  // Initialise TEMP variables

  __IL_DEFVAR_T __IL_DEFVAR;
(void)__IL_DEFVAR;
  __IL_DEFVAR_T __IL_DEFVAR_BACK;
(void)__IL_DEFVAR_BACK;
#line 400 "../Tests/TestCode.st"
  #define GetFbVar(var,...) __GET_VAR(data__->var,__VA_ARGS__)
  #define SetFbVar(var,val,...) __SET_VAR(data__->,var,__VA_ARGS__,val)
printf("=== T0 is called ===\n");
  #undef GetFbVar
  #undef SetFbVar
;

  goto __end;

__end:
  return;
} // TESTRUNNERPROGRAM_body__() 





