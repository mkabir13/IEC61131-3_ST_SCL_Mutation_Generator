"""
mergeSTcode.py

Creates TestCode.st by merging the ST fragments in the following
fixed serial order:

    1. Library.txt
    2. mutatecode.txt
    3. Programcontroller.txt
    4. Config.txt

Every time this script runs, TestCode.st is completely cleared and
rewritten from scratch.

The "2 mutatecode.txt" entry is dynamic:
- If original_code_override is provided, that string is inserted.
- Otherwise, the contents of 2 mutatecode.txt are read from disk.

This allows the mutation campaign and dashboard to inject either
mutated or original ST source without modifying 2 mutatecode.txt.

Run directly:

    python mergeSTcode.py

This writes:

    Tests/TestCode.st
"""

import config


# Fixed merge order required by the project.
ST_MERGE_ORDER = [
    "1 Library.txt",
    "2 mutatecode.txt",
    "3 Programcontroller.txt",
    "4 Config.txt",
]


def merge_st_files(original_code_override: str | None = None) -> str:
    """
    Build the complete TestCode.st content.

    The output is generated fresh every time in this exact order:

        1 Library.txt
        2 mutatecode.txt
        3 Programcontroller.txt
        4 Config.txt

    If original_code_override is supplied, it replaces the contents
    of 2 mutatecode.txt for this merge only.
    """

    parts = []

    for filename in ST_MERGE_ORDER:
        path = config.TESTS_DIR / filename

        # Dynamic source injection for mutation/dashboard workflow.
        if filename == "2 mutatecode.txt" and original_code_override is not None:
            content = original_code_override
        else:
            if not path.exists():
                raise FileNotFoundError(
                    f"Required ST fragment not found: {path}"
                )

            content = path.read_text(encoding="utf-8")

        # Add a clear separator between merged files.
        parts.append(
            f"(* ===== File: {filename} ===== *)\n"
            f"{content.rstrip()}\n"
        )

    # Return a completely new TestCode.st content.
    return "\n".join(parts)


def write_merged_st_file(original_code_override: str | None = None) -> str:
    """
    Completely clears TestCode.st and writes a fresh merged version.

    The file is opened with 'w' mode, which truncates the existing
    TestCode.st before writing the new content.
    """

    merged = merge_st_files(original_code_override)

    out_path = config.TESTS_DIR / "TestCode.st"

    # 'w' mode guarantees that the previous TestCode.st is removed
    # before the new merged content is written.
    with out_path.open("w", encoding="utf-8") as f:
        f.write(merged)

    return str(out_path)


if __name__ == "__main__":
    try:
        output_path = write_merged_st_file()

        print("========================================")
        print("ST Code Merge Successful")
        print("========================================")
        print(f"Output: {output_path}")
        print("")
        print("Merge order:")
        for index, filename in enumerate(ST_MERGE_ORDER, start=1):
            print(f"  {index}. {filename}")
        print("========================================")

    except Exception as e:
        print("========================================")
        print("ST Code Merge Failed")
        print("========================================")
        print(f"Error: {e}")
        print("========================================")
        raise
