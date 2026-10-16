
FUNCTION_BLOCK "FB_BreakerControlSystem"
{ S7_Optimized_Access := 'TRUE' }

VAR_INPUT
    B10_1_Trip  : BOOL;
    B10_1_Close : BOOL;

    B10_2_Trip  : BOOL;
    B10_2_Close : BOOL;

    B10_12_Trip  : BOOL;
    B10_12_Close : BOOL;

    B54_Trip  : BOOL;
    B54_Close : BOOL;

    B55_Trip  : BOOL;
    B55_Close : BOOL;

    B56_Trip  : BOOL;
    B56_Close : BOOL;

    B57_Trip  : BOOL;
    B57_Close : BOOL;
END_VAR

VAR_OUTPUT
    Point_1a : INT;
    Point_2a : INT;
    Point_3a : INT;
    Point_4a : INT;

    B10_1_Opened : BOOL;
    B10_1_Closed : BOOL;

    B10_2_Opened : BOOL;
    B10_2_Closed : BOOL;

    B10_12_Opened : BOOL;
    B10_12_Closed : BOOL;

    B54_Opened : BOOL;
    B54_Closed : BOOL;

    B55_Opened : BOOL;
    B55_Closed : BOOL;

    B56_Opened : BOOL;
    B56_Closed : BOOL;

    B57_Opened : BOOL;
    B57_Closed : BOOL;
END_VAR

BEGIN

    // --------------------------------------------------
    // Breaker B10_1 state transition
    // --------------------------------------------------
    IF B10_1_Close THEN
        B10_1_Closed := TRUE;
        B10_1_Opened := FALSE;
    ELSIF B10_1_Trip THEN
        B10_1_Closed := FALSE;
        B10_1_Opened := TRUE;
    END_IF;


    // --------------------------------------------------
    // Breaker B10_2 state transition
    // --------------------------------------------------
    IF B10_2_Close THEN
        B10_2_Closed := TRUE;
        B10_2_Opened := FALSE;
    ELSIF B10_2_Trip THEN
        B10_2_Closed := FALSE;
        B10_2_Opened := TRUE;
    END_IF;


    // --------------------------------------------------
    // Breaker B10_12 state transition
    // --------------------------------------------------
    IF B10_12_Close THEN
        B10_12_Closed := TRUE;
        B10_12_Opened := FALSE;
    ELSIF B10_12_Trip THEN
        B10_12_Closed := FALSE;
        B10_12_Opened := TRUE;
    END_IF;


    // --------------------------------------------------
    // Breaker B54 state transition
    // --------------------------------------------------
    IF B54_Close THEN
        B54_Closed := TRUE;
        B54_Opened := FALSE;
    ELSIF B54_Trip THEN
        B54_Closed := FALSE;
        B54_Opened := TRUE;
    END_IF;


    // --------------------------------------------------
    // Breaker B55 state transition
    // --------------------------------------------------
    IF B55_Close THEN
        B55_Closed := TRUE;
        B55_Opened := NOT (FALSE); (* MUTATED: ASSIGN_NEGATE *)
    ELSIF B55_Trip THEN
        B55_Closed := FALSE;
        B55_Opened := TRUE;
    END_IF;


    // --------------------------------------------------
    // Breaker B56 state transition
    // --------------------------------------------------
    IF B56_Close THEN
        B56_Closed := TRUE;
        B56_Opened := FALSE;
    ELSIF B56_Trip THEN
        B56_Closed := FALSE;
        B56_Opened := TRUE;
    END_IF;


    // --------------------------------------------------
    // Breaker B57 state transition
    // --------------------------------------------------
    IF B57_Close THEN
        B57_Closed := TRUE;
        B57_Opened := FALSE;
    ELSIF B57_Trip THEN
        B57_Closed := FALSE;
        B57_Opened := TRUE;
    END_IF;


    // --------------------------------------------------
    // Point_1a calculation
    // B54 AND ((B10_12 AND B10_1) OR B10_2)
    // --------------------------------------------------
    IF B54_Closed AND
       ((B10_12_Closed AND B10_1_Closed)
        OR B10_2_Closed) THEN

        Point_1a := 0;
    ELSE
        Point_1a := 138;
    END_IF;


    // --------------------------------------------------
    // Point_2a calculation
    // B55 AND ((B10_12 AND B10_1) OR B10_2)
    // --------------------------------------------------
    IF B55_Closed AND
       ((B10_12_Closed AND B10_1_Closed)
        OR B10_2_Closed) THEN

        Point_2a := 0;
    ELSE
        Point_2a := 138;
    END_IF;


    // --------------------------------------------------
    // Point_3a calculation
    // B56 AND ((B10_12 AND B10_2) OR B10_1)
    // --------------------------------------------------
    IF B56_Closed AND
       ((B10_12_Closed AND B10_2_Closed)
        OR B10_1_Closed) THEN

        Point_3a := 0;
    ELSE
        Point_3a := 138;
    END_IF;


    // --------------------------------------------------
    // Point_4a calculation
    // B57 AND ((B10_12 AND B10_2) OR B10_1)
    // --------------------------------------------------
    IF B57_Closed AND
       ((B10_12_Closed AND B10_2_Closed)
        OR B10_1_Closed) THEN

        Point_4a := 0;
    ELSE
        Point_4a := 138;
    END_IF;

END_FUNCTION_BLOCK
