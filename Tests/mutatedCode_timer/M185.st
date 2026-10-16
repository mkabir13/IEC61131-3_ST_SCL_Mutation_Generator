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

Motor := StartButton; (* MUTATION: TIMER_BYPASS on StartTimer *)

END_FUNCTION_BLOCK