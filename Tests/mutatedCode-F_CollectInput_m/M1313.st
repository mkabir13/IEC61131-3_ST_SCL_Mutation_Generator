FUNCTION_BLOCK "F_CollectInput"
{ S7_Optimized_Access := 'FALSE' }
VERSION : 1.0

VAR_INPUT
    TICK : Bool := FALSE;
    IN1 : Bool := FALSE;
    IN2 : Bool := FALSE;
    IN3 : Bool := FALSE;
    IN4 : Bool := FALSE;
    IN5 : Bool := FALSE;
    RESET : Bool := FALSE;
END_VAR

VAR_OUTPUT
    Finished : Bool;
END_VAR

VAR_IN_OUT
    Data : Array[1..20] of Bool;
END_VAR

VAR
    j : USInt := 1;        // Next free index in Data (1..21)
    tock : Bool := FALSE;  // Previous TICK state (edge detection)
END_VAR

VAR_TEMP
    k : Int;
END_VAR

BEGIN

    IF #RESET THEN
        // Reset: restart indexing and clear the previous collection
        #j := 1;
        #tock := FALSE;
        FOR #k := 1 TO 20 DO
            #Data[#k] := FALSE;
        END_FOR;
    ELSE
        // Collect on the rising edge of TICK, 5 inputs per tick
        IF #TICK AND NOT #tock THEN
            IF #j <= 16 THEN
                #Data[#j] := #IN1;
                #Data[#j + 1] := #IN2;
                #Data[#j + 2] := #IN3;
                #Data[#j + 3] := #IN4;
                #Data[#j + 4] := #IN5;
                #j := #j + 5;
            END_IF;
        END_IF;
        #tock := #TICK;
    END_IF;

    // Array fully populated after 20 inputs (4 ticks)
    #Finished := #j > 20;

    //#ASSERT j >= 1 AND j <= 21
    //#ASSERT Finished = (j > 20)
    //#ASSERT NOT RESET OR (j = 1 AND tock = FALSE)

END_FUNCTION_BLOCK

FUNCTION_BLOCK "MAIN"
{ S7_Optimized_Access := 'FALSE' }
VERSION : 1.0

VAR
    Data : Array[1..20] of Bool;
    Ready : Bool;
    CollectInput : "F_CollectInput";
    TICK : Bool;
    IN1 : Bool;
    IN2 : Bool;
    IN3 : Bool;
    IN4 : Bool;
    IN5 : Bool;
    OutReady : Bool := FALSE;
    FeedNext : Bool := FALSE;
    Out : Bool;
END_VAR

BEGIN

    // IEC "PROGRAM MAIN" implemented as an SCL function block.
    // 1) Collect the inputs; FeedNext (set in the previous scan once the
    //    output was produced) resets the collector for the next round.
    #CollectInput(TICK := #TICK,
                  IN1 := #IN1,
                  IN2 := #IN2,
                  IN3 := #IN3,
                  IN4 := #IN4,
                  IN5 := #IN5,
                  RESET := #FeedNext,
                  Data := #Data);

    // 2) Ready when the collector reports that Data is complete
    #Ready := #CollectInput.Finished;

    // 3) Output: for each address combination of Data[1], Data[2],
    //    Data[3], Data[7] the selected data bit must be TRUE
    #Out := (NOT (NOT #Data[7] AND NOT #Data[3] AND NOT #Data[2] AND NOT #Data[1]) OR #Data[5])
        AND (NOT (#Data[7] AND NOT #Data[3] AND NOT #Data[2] AND NOT #Data[1]) OR #Data[6])
        AND (NOT (NOT #Data[7] AND #Data[3] AND NOT #Data[2] AND NOT #Data[1]) OR #Data[12])
        AND (NOT (#Data[7] AND #Data[3] AND NOT #Data[2] AND NOT #Data[1]) OR #Data[8])
        AND (NOT (NOT #Data[7] AND NOT #Data[3] AND #Data[2] AND NOT #Data[1]) OR #Data[4])
        AND (NOT (#Data[7] AND NOT #Data[3] AND #Data[2] AND NOT #Data[1]) OR #Data[9])
        AND (NOT (NOT #Data[7] AND #Data[3] AND #Data[2] AND NOT #Data[1]) OR #Data[10])
        AND (NOT (#Data[7] AND #Data[3] AND #Data[2] AND NOT #Data[1]) OR #Data[16])
        AND (NOT (NOT #Data[7] AND NOT #Data[3] AND NOT #Data[2] AND #Data[1]) OR #Data[12]) (* MUTATED: CONST_VALUE_REPLACE *)
        AND (NOT (#Data[7] AND NOT #Data[3] AND NOT #Data[2] AND #Data[1]) OR #Data[14])
        AND (NOT (NOT #Data[7] AND #Data[3] AND NOT #Data[2] AND #Data[1]) OR #Data[17])
        AND (NOT (#Data[7] AND #Data[3] AND NOT #Data[2] AND #Data[1]) OR #Data[18])
        AND (NOT (NOT #Data[7] AND NOT #Data[3] AND #Data[2] AND #Data[1]) OR #Data[13])
        AND (NOT (#Data[7] AND NOT #Data[3] AND #Data[2] AND #Data[1]) OR #Data[20])
        AND (NOT (NOT #Data[7] AND #Data[3] AND #Data[2] AND #Data[1]) OR #Data[15])
        AND (NOT (#Data[7] AND #Data[3] AND #Data[2] AND #Data[1]) OR #Data[19]);

    // 4) Output readiness
    #OutReady := #Ready AND #Out;

    // 5) Request a reset of the collector once the output was produced
    #FeedNext := #Ready;

    //#ASSERT OutReady = (Ready AND Out)

END_FUNCTION_BLOCK
