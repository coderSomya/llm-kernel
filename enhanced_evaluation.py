#!/usr/bin/env python3

import requests
import json
import os
import urllib.request
from pathlib import Path
from scoring_analytics_engine import ScoringEngine


def ask_ollama_stream(query, model="qwen2.5:latest", system_prompt=None):
    url = "http://localhost:11434/api/chat"
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": query})
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": True
    }
    
    buffer = []
    try:
        with requests.post(url, json=payload, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    data = line.decode("utf-8")
                    chunk = json.loads(data)
                    content = chunk.get("message", {}).get("content")
                    if content:
                        buffer.append(content)
        return "".join(buffer)
    except requests.RequestException as e:
        return f"Error communicating with Ollama: {e}"


def ensure_dependencies():
    """Download required tools if not present"""
    checkpatch_url = "https://raw.githubusercontent.com/torvalds/linux/master/scripts/checkpatch.pl"
    spelling_url = "https://raw.githubusercontent.com/torvalds/linux/master/scripts/spelling.txt"
    
    if not Path("checkpatch.pl").exists():
        print("Downloading checkpatch.pl...")
        urllib.request.urlretrieve(checkpatch_url, "checkpatch.pl")
        os.chmod("checkpatch.pl", 0o755)
    
    if not Path("spelling.txt").exists():
        print("Downloading spelling.txt...")
        urllib.request.urlretrieve(spelling_url, "spelling.txt")


def load_kernel_standards():
    """Load kernel coding standards or create default"""
    standards_file = "kernel_standards.txt"
    
    if Path(standards_file).exists():
        with open(standards_file, "r") as f:
            return f.read()
    else:
        default_standards = """
You are an expert Linux kernel developer. Follow these guidelines:

1. CODING STYLE:
   - Use 8-space tabs for indentation
   - Keep lines under 80 characters when possible
   - Use Linux kernel naming conventions
   - Place opening braces on the same line for functions

2. INCLUDES AND HEADERS:
   - Always include necessary kernel headers
   - #include <linux/module.h> for module support
   - #include <linux/kernel.h> for kernel functions
   - #include <linux/fs.h> for file operations
   - #include <linux/uaccess.h> for user space access

3. ERROR HANDLING:
   - Use proper kernel error codes (-ENOMEM, -EINVAL, etc.)
   - Always check return values
   - Clean up resources on error paths
   - Use goto for error handling when appropriate

4. MEMORY MANAGEMENT:
   - Use kmalloc/kfree for kernel memory allocation
   - Always check for allocation failures
   - Free all allocated memory in cleanup paths
   - Use GFP_KERNEL for normal allocations

5. MODULE STRUCTURE:
   - Include MODULE_LICENSE("GPL")
   - Add MODULE_AUTHOR and MODULE_DESCRIPTION
   - Implement proper init and exit functions
   - Use module_init() and module_exit() macros

6. DEVICE OPERATIONS:
   - Implement proper file_operations structure
   - Handle concurrent access appropriately
   - Validate user input parameters
   - Return appropriate values from operations
"""
        with open(standards_file, "w") as f:
            f.write(default_standards)
        return default_standards


def generate_test_prompts():
    """Generate various test prompts for driver evaluation"""
    return [
        {
            "name": "simple_char_driver",
            "prompt": """
Create a simple character device driver that supports basic read/write operations with a
1KB internal buffer. Include proper module initialization and cleanup functions.
Return only the code, no other text. No backticks. Just the executable C code.
Follow the Linux kernel coding style strictly.
Use the latest Linux kernel version APIs.
""",
            "expected_features": ["file_operations", "read", "write", "module_init", "module_exit"]
        },
        {
            "name": "gpio_platform_driver", 
            "prompt": """
Implement a platform device driver for a simple GPIO controller with basic
set/get operations. Include device tree binding and proper platform driver structure.
Return only the code, no other text. No backticks. Just the executable C code.
Follow the Linux kernel coding style strictly.
""",
            "expected_features": ["platform_driver", "probe", "remove", "gpio_chip"]
        },
        {
            "name": "proc_interface_driver",
            "prompt": """
Create a character device driver that also provides a /proc interface for
configuration. Include both device file operations and proc file operations.
Return only the code, no other text. No backticks. Just the executable C code.
Follow the Linux kernel coding style strictly.
""",
            "expected_features": ["proc_create", "file_operations", "seq_file"]
        }
    ]


def run_enhanced_evaluation(model="qwen2.5:latest", test_name="simple_char_driver"):
    """Run enhanced evaluation with detailed scoring"""
    
    ensure_dependencies()
    kernel_standards = load_kernel_standards()
    test_prompts = generate_test_prompts()
    
    # Find the test prompt
    test_prompt = next((t for t in test_prompts if t["name"] == test_name), test_prompts[0])
    
    print(f"Generating code for: {test_prompt['name']}")
    print(f"Using model: {model}")
    print("-" * 60)
    
    # Generate code
    result = ask_ollama_stream(test_prompt["prompt"], model, kernel_standards)
    
    # Save generated code
    output_file = f"generated_{test_prompt['name']}.c"
    with open(output_file, "w") as f:
        f.write(result)
    
    print(f"Code saved to: {output_file}")
    
    # Run enhanced evaluation
    scoring_engine = ScoringEngine()
    evaluation_result = scoring_engine.evaluate_driver_code(output_file)
    
    # Print detailed results
    print("\n" + "="*60)
    print("ENHANCED EVALUATION RESULTS")
    print("="*60)
    
    print(f"Overall Score: {evaluation_result.overall_score:.2f}/1.00")
    print()
    
    # Compilation Results
    comp = evaluation_result.compilation
    print("COMPILATION:")
    print(f"  Success: {'✓' if comp.success else '✗'}")
    print(f"  Build Time: {comp.build_time:.2f}s")
    print(f"  Errors: {comp.error_count}")
    print(f"  Warnings: {comp.warning_count}")
    if comp.binary_size:
        print(f"  Binary Size: {comp.binary_size} bytes")
    print()
    
    # Static Analysis Results
    static = evaluation_result.static_analysis
    print("STATIC ANALYSIS:")
    print(f"  Sparse Issues: {static.sparse_issues}")
    print(f"  Checkpatch Violations: {static.checkpatch_violations}")
    print(f"  Cppcheck Issues: {static.cppcheck_issues}")
    print(f"  API Compliance: {static.api_compliance_score:.2f}")
    print()
    
    # Security Results
    security = evaluation_result.security
    print("SECURITY:")
    print(f"  Buffer Safety: {security.buffer_safety_score:.2f}")
    print(f"  Memory Leak Risk: {security.memory_leak_risk:.2f}")
    print(f"  Race Condition Risk: {security.race_condition_risk:.2f}")
    print(f"  Input Validation: {security.input_validation_score:.2f}")
    print()
    
    # Code Quality Results
    quality = evaluation_result.code_quality
    print("CODE QUALITY:")
    print(f"  Style Compliance: {quality.style_compliance:.2f}")
    print(f"  Cyclomatic Complexity: {quality.cyclomatic_complexity:.2f}")
    print(f"  Avg Function Length: {quality.function_length_avg:.1f} lines")
    print(f"  Comment Ratio: {quality.comment_ratio:.2f}")
    print(f"  Maintainability Index: {quality.maintainability_index:.2f}")
    print()
    
    # Functionality Results
    func = evaluation_result.functionality
    print("FUNCTIONALITY:")
    print(f"  Basic Operations: {func.basic_operations_score:.2f}")
    print(f"  Error Handling: {func.error_handling_score:.2f}")
    print(f"  Edge Cases: {func.edge_case_handling:.2f}")
    print(f"  API Correctness: {func.api_correctness:.2f}")
    print()
    
    # Weighted Scores
    print("WEIGHTED SCORES:")
    for category, score in evaluation_result.weighted_scores.items():
        print(f"  {category.title()}: {score:.3f}")
    print()
    
    # Feature Analysis
    print("FEATURE ANALYSIS:")
    code = result.lower()
    for feature in test_prompt["expected_features"]:
        found = feature.lower() in code
        print(f"  {feature}: {'✓' if found else '✗'}")
    
    # Save detailed results
    results_file = f"detailed_results_{test_prompt['name']}.json"
    scoring_engine.export_results(evaluation_result, results_file)
    print(f"\nDetailed results saved to: {results_file}")
    
    return evaluation_result


def compare_models(models=["qwen2.5:latest"], test_name="simple_char_driver"):
    """Compare multiple models on the same test"""
    
    print("MULTI-MODEL COMPARISON")
    print("="*60)
    
    results = []
    
    for model in models:
        print(f"\nEvaluating model: {model}")
        try:
            result = run_enhanced_evaluation(model, test_name)
            results.append((model, result))
        except Exception as e:
            print(f"Error evaluating {model}: {e}")
    
    if len(results) < 2:
        print("Need at least 2 successful evaluations for comparison")
        return
    
    # Generate comparison
    scoring_engine = ScoringEngine()
    comparison = scoring_engine.compare_models(results)
    
    print("\n" + "="*60)
    print("MODEL COMPARISON RESULTS")
    print("="*60)
    
    print("OVERALL RANKINGS:")
    for i, ranking in enumerate(comparison['model_rankings'], 1):
        print(f"{i}. {ranking['model']}")
        print(f"   Overall Score: {ranking['overall_score']:.3f}")
        print(f"   Compilation: {'✓' if ranking['compilation_success'] else '✗'}")
        print(f"   Security: {ranking['security_score']:.3f}")
        print()
    
    print("CATEGORY WINNERS:")
    for category, winner in comparison['category_winners'].items():
        print(f"  {category.title()}: {winner}")
    
    # Save comparison results
    with open(f"model_comparison_{test_name}.json", "w") as f:
        json.dump(comparison, f, indent=2)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Linux Driver Code Evaluation")
    parser.add_argument("--model", default="qwen2.5:latest", help="Ollama model to use")
    parser.add_argument("--test", choices=["simple_char_driver", "gpio_platform_driver", "proc_interface_driver"],
                       default="simple_char_driver", help="Test type to run")
    parser.add_argument("--compare", nargs="+", help="Compare multiple models")
    
    args = parser.parse_args()
    
    if args.compare:
        compare_models(args.compare, args.test)
    else:
        run_enhanced_evaluation(args.model, args.test)


if __name__ == "__main__":
    main()