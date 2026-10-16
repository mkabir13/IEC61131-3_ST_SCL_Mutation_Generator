FUNCTION_BLOCK "FB_Fibonacci_Calculator"
{ S7_Optimized_Access := 'FALSE' }
VERSION : 1.0

VAR_INPUT
    N : DInt := 5;
END_VAR

VAR_OUTPUT
    O : DInt := 1;
END_VAR

VAR
    F1 : DInt := 1;    // Fib(k-2) at the end of the calculation
    F2 : DInt := 1;    // Fib(k-1) at the end of the calculation
    CNT : DInt := 2;   // Index of the last computed term
END_VAR

BEGIN

    // Start values: Fib(1) = Fib(2) = 1
    #F1 := 1;
    #F2 := 1;
    #O := 1;

    IF #N <= 2 THEN
        // Edge case: N <= 2 returns 1
        #CNT := #N;
    ELSE
        #CNT := 2;
        WHILE #CNT < #N DO
            #CNT := #CNT + 1;

            // Saturation arithmetic: result would exceed INT range
            IF (#F1 + #F2) > 32767 THEN
                #O := 32767;
                EXIT;
            END_IF;

            #O := #F1 + #F2;

            // Shift the window only if another term is still needed,
            // so that at the end O = F1 + F2
            IF #CNT < #N THEN
                #F1 := #F2;
                #F2 := #O;
            END_IF;
        END_WHILE;
    END_IF;

    // Final saturation guard
    IF (#O > 32768) OR (#O < 0) THEN (* MUTATED: CONST_VALUE_REPLACE *)
        #O := 32767;
    END_IF;

    //#ASSERT O >= 0 AND O <= 32767
    //#ASSERT F1 <= 32767 AND F2 <= 32767
    //#ASSERT CNT <= N

END_FUNCTION_BLOCK
