FUNCTION_BLOCK TON_Example

VAR
    StartButton : BOOL;
    Motor       : BOOL;
    StartTimer  : TON;
END_VAR

StartTimer(
    IN := StartButton,
    PT := T#5s
);

StartButton := StartTimer.Q; (* MUTATED: VAR_REPLACE *)

END_FUNCTION_BLOCK