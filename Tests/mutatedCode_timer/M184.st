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

Motor := NOT (StartTimer.Q); (* MUTATED: ASSIGN_NEGATE *)

END_FUNCTION_BLOCK