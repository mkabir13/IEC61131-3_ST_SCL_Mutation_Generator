FUNCTION_BLOCK "PumpControl"
{ S7_Optimized_Access := 'TRUE' }
VERSION : 0.1
VAR_INPUT
HighLevelSensor : Bool; // True if water is dangerously high
LowLevelSensor : Bool; // True if tank is empty
ManualStop : Bool;
END_VAR 
 
VAR_OUTPUT
MainPump : Bool;
BackupPump : Bool;
END_VAR 
 
BEGIN
// Main Pump Logic
IF #HighLevelSensor AND NOT #ManualStop THEN
#MainPump := TRUE;
ELIF #LowLevelSensor OR #ManualStop THEN
#MainPump := FALSE;
END_IF; 
 
// Safety Backup Pump Logic IF #HighLevelSensor AND #MainPump THEN #BackupPump := TRUE; 
// Turns on if main pump isnt enough or failed ELIF #LowLevelSensor THEN #BackupPump := FALSE; END_IF;
END_FUNCTION_BLOCK 
