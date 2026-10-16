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
static void LAMBERT_W_init__(LAMBERT_W_data__ *data__, BOOL retain);
static void LAMBERT_W_body__(LAMBERT_W_data__ *data__);
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
#line 8 "/tmp/tmp13e60xwd/submission.st"
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
#line 17 "/tmp/tmp13e60xwd/submission.st"
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
#line 26 "/tmp/tmp13e60xwd/submission.st"
  FLOOR = ___REAL_TO_INT(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (REAL)X);
#line 27 "/tmp/tmp13e60xwd/submission.st"
  if ((___INT_TO_REAL(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (INT)FLOOR) > X)) {
#line 28 "/tmp/tmp13e60xwd/submission.st"
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
#line 38 "/tmp/tmp13e60xwd/submission.st"
  FLOOR2 = ___REAL_TO_DINT(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (REAL)X);
#line 39 "/tmp/tmp13e60xwd/submission.st"
  if ((___DINT_TO_REAL(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (DINT)FLOOR2) > X)) {
#line 40 "/tmp/tmp13e60xwd/submission.st"
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
#line 51 "/tmp/tmp13e60xwd/submission.st"
  if ((DIVI == __REAL_LITERAL(0.0))) {
#line 52 "/tmp/tmp13e60xwd/submission.st"
    MODR = __REAL_LITERAL(0.0);
  } else {
#line 54 "/tmp/tmp13e60xwd/submission.st"
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
#line 65 "/tmp/tmp13e60xwd/submission.st"
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
#line 82 "/tmp/tmp13e60xwd/submission.st"
  _D = DI;
#line 83 "/tmp/tmp13e60xwd/submission.st"
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
#line 84 "/tmp/tmp13e60xwd/submission.st"
        REFLECT = (___SHL__DWORD__DWORD__SINT(
          (BOOL)__BOOL_LITERAL(TRUE),
          NULL,
          (DWORD)REFLECT,
          (SINT)__SINT_LITERAL(1)) | ___BOOL_TO_DWORD(
          (BOOL)__BOOL_LITERAL(TRUE),
          NULL,
          (BOOL)((_D & __DWORD_LITERAL(0x01)) > __DWORD_LITERAL(0))));
#line 85 "/tmp/tmp13e60xwd/submission.st"
        _D = ___SHR__DWORD__DWORD__SINT(
          (BOOL)__BOOL_LITERAL(TRUE),
          NULL,
          (DWORD)_D,
          (SINT)__SINT_LITERAL(1));
      }else break;
    }
  } /* END_FOR */;
#line 87 "/tmp/tmp13e60xwd/submission.st"
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
#line 101 "/tmp/tmp13e60xwd/submission.st"
  if (VAL) {
#line 102 "/tmp/tmp13e60xwd/submission.st"
    BIT_LOAD_B = (IN | ___SHL__BYTE__BYTE__INT(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BYTE)__BYTE_LITERAL(1),
      (INT)POS));
  } else {
#line 104 "/tmp/tmp13e60xwd/submission.st"
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
#line 115 "/tmp/tmp13e60xwd/submission.st"
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
#line 133 "/tmp/tmp13e60xwd/submission.st"
  TX = __UDINT_LITERAL(0);
#line 134 "/tmp/tmp13e60xwd/submission.st"
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
#line 139 "/tmp/tmp13e60xwd/submission.st"
  T_PLC_MS = TX;
#line 140 "/tmp/tmp13e60xwd/submission.st"
  if (DEBUG) {
#line 141 "/tmp/tmp13e60xwd/submission.st"
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
#line 145 "/tmp/tmp13e60xwd/submission.st"
  if (DEBUG) {
#line 146 "/tmp/tmp13e60xwd/submission.st"
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
#line 178 "/tmp/tmp13e60xwd/submission.st"
  T_PLC_US = (TX * __UDINT_LITERAL(1000));
#line 179 "/tmp/tmp13e60xwd/submission.st"
  if (DEBUG) {
#line 180 "/tmp/tmp13e60xwd/submission.st"
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

#line 217 "/tmp/tmp13e60xwd/submission.st"
  __SET_VAR(data__->,TX,,___T_PLC_US(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (BOOL)__BOOL_LITERAL(FALSE)));
#line 218 "/tmp/tmp13e60xwd/submission.st"
  __SET_VAR(data__->,TC,,___UDINT_TO_REAL(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UDINT)(__GET_VAR(data__->TX,) - __GET_VAR(data__->LAST,))));
#line 221 "/tmp/tmp13e60xwd/submission.st"
  if (!(__GET_VAR(data__->INIT,))) {
#line 222 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,INIT,,__BOOL_LITERAL(TRUE));
#line 223 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,OLD,,__GET_VAR(data__->IN,));
  } else if ((__GET_VAR(data__->RUN,) && (__GET_VAR(data__->TC,) > __REAL_LITERAL(0.0)))) {
#line 225 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,OUT,,((((__GET_VAR(data__->IN,) - __GET_VAR(data__->OLD,)) / __GET_VAR(data__->TC,)) * __REAL_LITERAL(1000000.0)) * __GET_VAR(data__->K,)));
#line 226 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,OLD,,__GET_VAR(data__->IN,));
  } else {
#line 228 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,OUT,,__REAL_LITERAL(0.0));
  };
#line 231 "/tmp/tmp13e60xwd/submission.st"
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

#line 261 "/tmp/tmp13e60xwd/submission.st"
  if ((!(__GET_VAR(data__->INIT,)) || __GET_VAR(data__->RST,))) {
#line 262 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,INIT,,__BOOL_LITERAL(TRUE));
#line 263 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,IN_LAST,,__GET_VAR(data__->IN,));
#line 264 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,T_LAST,,___T_PLC_US(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__BOOL_LITERAL(FALSE)));
#line 265 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,I,,__REAL_LITERAL(0.0));
#line 266 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,TC,,__REAL_LITERAL(0.0));
  } else {
#line 269 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,TX,,___T_PLC_US(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__BOOL_LITERAL(FALSE)));
#line 270 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,TC,,___UDINT_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (UDINT)(__GET_VAR(data__->TX,) - __GET_VAR(data__->T_LAST,))));
#line 271 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,T_LAST,,__GET_VAR(data__->TX,));
#line 274 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,P,,(__GET_VAR(data__->KP,) * __GET_VAR(data__->IN,)));
#line 277 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,I,,(((((__GET_VAR(data__->IN,) + __GET_VAR(data__->IN_LAST,)) * __REAL_LITERAL(5.0E-7)) * __GET_VAR(data__->KI,)) * __GET_VAR(data__->TC,)) + __GET_VAR(data__->I,)));
#line 278 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,IN_LAST,,__GET_VAR(data__->IN,));
#line 281 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,Y,,(__GET_VAR(data__->P,) + __GET_VAR(data__->I,)));
#line 284 "/tmp/tmp13e60xwd/submission.st"
    if ((__GET_VAR(data__->Y,) >= __GET_VAR(data__->LIM_H,))) {
#line 285 "/tmp/tmp13e60xwd/submission.st"
      __SET_VAR(data__->,Y,,__GET_VAR(data__->LIM_H,));
#line 286 "/tmp/tmp13e60xwd/submission.st"
      if ((__GET_VAR(data__->KI,) != __REAL_LITERAL(0.0))) {
#line 287 "/tmp/tmp13e60xwd/submission.st"
        __SET_VAR(data__->,I,,(__GET_VAR(data__->LIM_H,) - __GET_VAR(data__->P,)));
      } else {
#line 289 "/tmp/tmp13e60xwd/submission.st"
        __SET_VAR(data__->,I,,__REAL_LITERAL(0.0));
      };
#line 291 "/tmp/tmp13e60xwd/submission.st"
      __SET_VAR(data__->,LIM,,__BOOL_LITERAL(TRUE));
    } else if ((__GET_VAR(data__->Y,) <= __GET_VAR(data__->LIM_L,))) {
#line 293 "/tmp/tmp13e60xwd/submission.st"
      __SET_VAR(data__->,Y,,__GET_VAR(data__->LIM_L,));
#line 294 "/tmp/tmp13e60xwd/submission.st"
      if ((__GET_VAR(data__->KI,) != __REAL_LITERAL(0.0))) {
#line 295 "/tmp/tmp13e60xwd/submission.st"
        __SET_VAR(data__->,I,,(__GET_VAR(data__->LIM_L,) - __GET_VAR(data__->P,)));
      } else {
#line 297 "/tmp/tmp13e60xwd/submission.st"
        __SET_VAR(data__->,I,,__REAL_LITERAL(0.0));
      };
#line 299 "/tmp/tmp13e60xwd/submission.st"
      __SET_VAR(data__->,LIM,,__BOOL_LITERAL(TRUE));
    } else {
#line 301 "/tmp/tmp13e60xwd/submission.st"
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

#line 326 "/tmp/tmp13e60xwd/submission.st"
  __SET_VAR(data__->,TX,,___T_PLC_MS(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (BOOL)__BOOL_LITERAL(FALSE)));
#line 328 "/tmp/tmp13e60xwd/submission.st"
  if (!(__GET_VAR(data__->INIT,))) {
#line 329 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,INIT,,__BOOL_LITERAL(TRUE));
#line 330 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,X_LAST,,__GET_VAR(data__->X,));
  } else if (__GET_VAR(data__->_E,)) {
#line 332 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,Y,,(((((__GET_VAR(data__->X,) + __GET_VAR(data__->X_LAST,)) * __REAL_LITERAL(0.5E-3)) * ___UDINT_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (UDINT)(__GET_VAR(data__->TX,) - __GET_VAR(data__->LAST,)))) * __GET_VAR(data__->K,)) + __GET_VAR(data__->Y,)));
#line 333 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,X_LAST,,__GET_VAR(data__->X,));
  };
#line 335 "/tmp/tmp13e60xwd/submission.st"
  __SET_VAR(data__->,LAST,,__GET_VAR(data__->TX,));

  goto __end;

__end:
  return;
} // INTEGRATE_body__() 





static void LAMBERT_W_init__(LAMBERT_W_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->X,0,retain)
  __INIT_VAR(data__->OUT,0,retain)
  __INIT_VAR(data__->W,0,retain)
  __INIT_VAR(data__->I,0,retain)
  __INIT_VAR(data__->WE,0,retain)
  __INIT_VAR(data__->W1E,0,retain)
  __INIT_VAR(data__->EWX,0,retain)
  __INIT_VAR(data__->LAST,0,retain)
}

// Code part
static void LAMBERT_W_body__(LAMBERT_W_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

#line 358 "/tmp/tmp13e60xwd/submission.st"
  if ((__GET_VAR(data__->X,) < __REAL_LITERAL(-0.367879441171442))) {
#line 359 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,OUT,,__REAL_LITERAL(-1000.0));
#line 360 "/tmp/tmp13e60xwd/submission.st"
    goto __end;
  } else if ((__GET_VAR(data__->X,) == __REAL_LITERAL(0.0))) {
#line 363 "/tmp/tmp13e60xwd/submission.st"
    goto __end;
  } else if ((__GET_VAR(data__->X,) <= __REAL_LITERAL(500.0))) {
#line 366 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,W,,___LN__REAL__REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)(__GET_VAR(data__->X,) + __REAL_LITERAL(1.0))));
#line 367 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,W,,(((__REAL_LITERAL(0.665) * (__REAL_LITERAL(1.0) + (__REAL_LITERAL(0.0195) * __GET_VAR(data__->W,)))) * __GET_VAR(data__->W,)) + __REAL_LITERAL(0.04)));
  } else {
#line 369 "/tmp/tmp13e60xwd/submission.st"
    __SET_VAR(data__->,W,,(___LN__REAL__REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)(__GET_VAR(data__->X,) - __REAL_LITERAL(4.0))) - ((__REAL_LITERAL(1.0) - (__REAL_LITERAL(1.0) / ___LN__REAL__REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->X,)))) * ___LN__REAL__REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)___LN__REAL__REAL(
        (BOOL)__BOOL_LITERAL(TRUE),
        NULL,
        (REAL)__GET_VAR(data__->X,))))));
  };
#line 372 "/tmp/tmp13e60xwd/submission.st"
  /* FOR ... */
  __SET_VAR(data__->,I,,__INT_LITERAL(0));
  {
    int __do_increment = 0;
    while(1) {
      if(__do_increment){
        /* BY ... (of FOR loop) */
        __SET_VAR(data__->,I,,(__GET_VAR(data__->I,) + __INT_LITERAL(1)));
      } else __do_increment = 1;
      if(__GET_VAR(data__->I,) <= __INT_LITERAL(5)      ){
#line 373 "/tmp/tmp13e60xwd/submission.st"
        __SET_VAR(data__->,EWX,,___EXP__REAL__REAL(
          (BOOL)__BOOL_LITERAL(TRUE),
          NULL,
          (REAL)__GET_VAR(data__->W,)));
#line 374 "/tmp/tmp13e60xwd/submission.st"
        __SET_VAR(data__->,WE,,((__GET_VAR(data__->W,) * __GET_VAR(data__->EWX,)) - __GET_VAR(data__->X,)));
#line 375 "/tmp/tmp13e60xwd/submission.st"
        __SET_VAR(data__->,W1E,,((__GET_VAR(data__->W,) + __REAL_LITERAL(1.0)) * __GET_VAR(data__->EWX,)));
#line 376 "/tmp/tmp13e60xwd/submission.st"
        __SET_VAR(data__->,LAST,,(___REAL_TO_DWORD(
          (BOOL)__BOOL_LITERAL(TRUE),
          NULL,
          (REAL)__GET_VAR(data__->W,)) & __DWORD_LITERAL(0xFFFFFFFC)));
#line 377 "/tmp/tmp13e60xwd/submission.st"
        __SET_VAR(data__->,W,,(__GET_VAR(data__->W,) - (__GET_VAR(data__->WE,) / (__GET_VAR(data__->W1E,) - (((__GET_VAR(data__->W,) + __REAL_LITERAL(2.0)) * __GET_VAR(data__->WE,)) / ((__REAL_LITERAL(2.0) * __GET_VAR(data__->W,)) + __REAL_LITERAL(2.0)))))));
#line 378 "/tmp/tmp13e60xwd/submission.st"
        if (((___REAL_TO_DWORD(
          (BOOL)__BOOL_LITERAL(TRUE),
          NULL,
          (REAL)__GET_VAR(data__->W,)) & __DWORD_LITERAL(0xFFFFFFFC)) == __GET_VAR(data__->LAST,))) {
#line 378 "/tmp/tmp13e60xwd/submission.st"
          break;
        };
      }else break;
    }
  } /* END_FOR */;
#line 380 "/tmp/tmp13e60xwd/submission.st"
  __SET_VAR(data__->,OUT,,__GET_VAR(data__->W,));

  goto __end;

__end:
  return;
} // LAMBERT_W_body__() 





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
#line 395 "/tmp/tmp13e60xwd/submission.st"
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





