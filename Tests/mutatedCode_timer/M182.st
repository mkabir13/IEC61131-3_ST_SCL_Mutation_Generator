FUNCTION_BLOCK TON_Example

VAR
    StartButton : BOOL;
    Motor       : BOOL;
    StartTimer  : TON;
END_VAR

StartTimer(
    IN := Motor, (* MUTATED: VAR_REPLACE *)
    PT := T#5s
);

Motor := StartTimer.Q;

END_FUNCTION_BLOCK