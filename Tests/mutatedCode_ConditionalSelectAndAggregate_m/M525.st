FUNCTION_BLOCK "FB_ConditionalSelectAndAggregate"
{ S7_Optimized_Access := 'TRUE' } (* MUTATED: BOOL_CONST_REPLACE *)
VERSION : 1.0

VAR_INPUT
    old_z : Int;
END_VAR

VAR_OUTPUT
    newz : Int;
END_VAR

VAR
    ax : Int := 42;
    ay : Int := 333;
END_VAR

BEGIN

    IF #ax > #old_z THEN
        #newz := #ay;
    ELSE
        #newz := #old_z;
    END_IF;

    #newz := #newz + #ax + #ay;

END_FUNCTION_BLOCK
