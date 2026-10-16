FUNCTION_BLOCK "FB_CalculateOutput"
{ S7_Optimized_Access := 'FALSE' }
VERSION : 1.0

VAR_INPUT
    i : Int;
END_VAR

VAR_OUTPUT
    o : Int;
END_VAR

BEGIN

    // Default output for all invalid/out-of-range inputs
    #o := -1;

    // Valid input/output mappings
    IF #i = 0 THEN
        #o := 0;

    ELSIF (#i >= 1) AND (#i <= 5) THEN
        #o := #i * #i;

    ELSIF (#i >= 6) AND (#i <= 10) THEN
        #o := #i - (#i * 2); (* MUTATED: ARITH_OP_REPLACE *)
    END_IF;

END_FUNCTION_BLOCK
