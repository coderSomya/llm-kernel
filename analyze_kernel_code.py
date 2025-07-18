import subprocess
import tempfile
import os
import re
import urllib.request

# Path to the generated code file
GENERATED_CODE_FILE = "generated_driver.c"


def check_compilability(code_path):
    """
    Try to compile the code using gcc. Returns (success, output).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "driver.ko")
        # Try to compile as a kernel module
        makefile_content = f"""
obj-m += driver.o
all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules
clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
"""
        # Write Makefile and code
        with open(os.path.join(tmpdir, "Makefile"), "w") as mf:
            mf.write(makefile_content)
        code_dest = os.path.join(tmpdir, "driver.c")
        with open(code_path, "r") as src, open(code_dest, "w") as dst:
            dst.write(src.read())
        # Run make
        try:
            result = subprocess.run(["make"], cwd=tmpdir, capture_output=True, text=True, timeout=30)
            success = result.returncode == 0
            return success, result.stdout + "\n" + result.stderr
        except Exception as e:
            return False, str(e)

def run_static_analysis(code_path):
    """
    Run static analysis using cppcheck (if available).
    Returns a list of issues found.
    """
    try:
        result = subprocess.run([
            "cppcheck", "--enable=all", "--std=c99", code_path
        ], capture_output=True, text=True, timeout=20)
        issues = result.stderr.strip().splitlines()
        return issues
    except Exception as e:
        return [f"Static analysis failed: {e}"]

def check_kernel_coding_style(code_path):
    """
    Check Linux kernel coding style using checkpatch.pl (local copy preferred).
    Returns a list of style warnings/errors.
    """
    checkpatch_path = "./checkpatch.pl"
    if not os.path.exists(checkpatch_path):
        return ["checkpatch.pl not found in current directory."]
    try:
        result = subprocess.run([
            "perl", checkpatch_path, "--no-tree", code_path
        ], capture_output=True, text=True, timeout=20)
        style_issues = result.stdout.strip().splitlines()
        return style_issues
    except Exception as e:
        return [f"Style analysis failed: {e}"]

def code_metrics(code_path):
    """
    Return basic code metrics: line count, comment ratio, function count, average function length.
    """
    with open(code_path, "r") as f:
        code = f.read()
    lines = code.splitlines()
    total_lines = len(lines)
    comment_lines = len([l for l in lines if l.strip().startswith('//') or l.strip().startswith('/*') or l.strip().startswith('*')])
    comment_ratio = comment_lines / total_lines if total_lines else 0
    functions = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)\s*{', code)
    function_count = len(functions)
    # Estimate average function length
    function_lengths = [len(f.splitlines()) for f in re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)\s*{[\s\S]*?\n}', code)]
    avg_func_length = sum(function_lengths) / function_count if function_count else 0
    return {
        "total_lines": total_lines,
        "comment_ratio": comment_ratio,
        "function_count": function_count,
        "avg_func_length": avg_func_length
    }

def analyze_and_grade_kernel_code(code_path=GENERATED_CODE_FILE):
    print(f"Analyzing: {code_path}\n")
    # Compilability
    compiles, compile_output = check_compilability(code_path)
    print(f"Compilability: {'PASS' if compiles else 'FAIL'}")
    if not compiles:
        print("Compiler output:")
        print(compile_output)
    print()
    # Static analysis
    static_issues = run_static_analysis(code_path)
    print(f"Static Analysis Issues: {len(static_issues)}")
    for issue in static_issues:
        print(issue)
    print()
    # Coding style
    style_issues = check_kernel_coding_style(code_path)
    print(f"Kernel Coding Style Issues: {len(style_issues)}")
    for issue in style_issues:
        print(issue)
    print()
    # Code metrics
    metrics = code_metrics(code_path)
    print("Code Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    print()
    # Grading (simple heuristic)
    grade = 100
    if not compiles:
        grade -= 40
    grade -= min(len(static_issues), 10) * 3
    grade -= min(len(style_issues), 10) * 2
    if metrics["comment_ratio"] < 0.05:
        grade -= 5
    print(f"\nFinal Grade: {max(grade, 0)}/100\n")

def ensure_checkpatch_local():
    url = "https://raw.githubusercontent.com/torvalds/linux/master/scripts/checkpatch.pl"
    local_path = "checkpatch.pl"
    if not os.path.exists(local_path):
        print("Downloading checkpatch.pl...")
        urllib.request.urlretrieve(url, local_path)
        os.chmod(local_path, 0o755)
        print("checkpatch.pl downloaded.")

if __name__ == "__main__":
    ensure_checkpatch_local()
    analyze_and_grade_kernel_code() 