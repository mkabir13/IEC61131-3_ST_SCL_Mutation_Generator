#!/bin/bash
set -e
set -o pipefail

echo "===== STEP 0: SAFE LOG ROTATION ====="

ITER=${ITER:-0}

mkdir -p ../log/iter_$ITER
mkdir -p ../Output/result

rotate_log () {
    FILE=$1
    if [ -f "$FILE" ]; then
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        mv "$FILE" "${FILE}.${TIMESTAMP}.bak"
        echo "🔁 Rotated log: $FILE → ${FILE}.${TIMESTAMP}.bak"
    fi
}

# ==========================================================
# STEP 1: Cleaning old build and coverage files
# ==========================================================
echo "===== STEP 1: Cleaning old build and coverage files ====="

rm -rf ../Output/POUS.* \
        ../Output/LOCATED_VARIABLES.h \
        ../Output/VARIABLES.csv \
        ../Output/Res0.c \
        ../Output/Config0.* \
        ../Output/*.html \
        ../Output/*.css \
        ../Output/*.gcov \
        ../Output/*.o \
        ../Output/*.gcno \
        ../Output/*.gcda \
        ../Output/softplc \
        ../Output/out \
        ../Output/coverage* \
        ../Output/TestConfig* \
        ../Output/*.png \
        ../Output/Test* \
        ../Output/*.csv \
        ../Output/*.txt 2>/dev/null

# ==========================================================
# STEP 2: Move to MATIEC
# ==========================================================
echo "===== STEP 2: Moving to MATIEC directory ====="

cd ../matiec/ || { echo "❌ Failed to enter MATIEC directory"; exit 1; }

# ==========================================================
# STEP 3: Compile ST code (MATIEC)
# ==========================================================
echo "===== STEP 3: Compiling ST code with MATIEC ====="

set +e   # temporarily disable exit-on-error
./iec2c -Ol -I lib ../Tests/TestCode.st > compile_output.txt 2> compile_error.txt
compile_status=$?
set -e   # re-enable it
# rotate + move logs
# move compile error
if [ -f "./compile_error.txt" ]; then
    mv "./compile_error.txt" "../log/iter_$ITER/compile_error.txt"
fi

# move compile output
if [ -f "./compile_output.txt" ]; then
    mv "./compile_output.txt" "../log/iter_$ITER/compile_output.txt"
fi

#rotate_log ../log/compile_error.txt


if [ $compile_status -ne 0 ]; then
    echo "❌ MATIEC compilation failed."
    echo "Check ../log/iter_$ITER/"
    exit 1
fi

echo "✅ MATIEC compilation successful."

# ==========================================================
# STEP 4: Move generated C files
# ==========================================================
echo "===== STEP 4: Moving generated files to Output ====="

mv *.h ../Output/ 2>/dev/null
mv *.c ../Output/ 2>/dev/null
mv *.csv ../Output/ 2>/dev/null

# ==========================================================
# STEP 5: Go to Output
# ==========================================================
cd ../Output || { echo "❌ Failed to enter Output directory"; exit 1; }

# ==========================================================
# STEP 6: GCC compilation with coverage
# ==========================================================
echo "===== STEP 6: Compiling C code with GCC + GCOV ====="

gcc -I ../matiec/lib/C -fprofile-arcs -ftest-coverage \
Config0.c Res0.c plc.c main.c -o softplc -lm \
> gcc_output.txt 2> gcc_error.txt

gcc_status=$?

# rotate + move gcc logs
rotate_log ../log/gcc_error.txt
mv gcc_output.txt ../Output/result/ 2>/dev/null
mv gcc_error.txt ../log/ 2>/dev/null

if [ $gcc_status -ne 0 ]; then
    echo "❌ GCC compilation failed."
    echo "Check ../log/gcc_error.txt"
    exit 1
fi

echo "✅ GCC compilation successful."

# ==========================================================
# STEP 7: Run PLC program (CAPTURE LOGS)
# ==========================================================
echo "===== STEP 7: Running program ====="

timeout 5s stdbuf -oL ./softplc \
> ../log/runtime_output.txt \
2> ../log/runtime_error.txt || true

# ==========================================================
# STEP 8: Generate GCOV report
# ==========================================================
echo "===== STEP 8: Generating coverage report ====="

gcov softplc-Res0.gcno > gcov_output.txt 2> gcov_error.txt || true

# rotate + move gcov logs
rotate_log ../log/gcov_output.txt
rotate_log ../log/gcov_error.txt

mv gcov_output.txt ../log/ 2>/dev/null
mv gcov_error.txt ../log/ 2>/dev/null

echo "✅ Coverage generation completed."
