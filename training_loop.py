#!/usr/bin/env python3

import json
import time
from pathlib import Path
from typing import List, Dict, Tuple
from enhanced_evaluation import ask_ollama_stream, load_kernel_standards, generate_test_prompts
from scoring_analytics_engine import ScoringEngine


class FeedbackGenerator:
    def __init__(self):
        self.scoring_engine = ScoringEngine()
    
    def generate_detailed_feedback(self, code: str, evaluation_result, iteration: int) -> str:
        feedback = f"ITERATION {iteration} - CODE REVIEW FEEDBACK\n\nOVERALL SCORE: {evaluation_result.overall_score:.2f}/1.00\n\nCRITICAL ISSUES TO FIX:\n\n"
        
        if not evaluation_result.compilation.success:
            feedback += "COMPILATION FAILED:\nYour code does not compile. This is the highest priority issue.\n\nCommon kernel driver compilation issues:\n- Wrong function signatures in file_operations\n- Missing or incorrect #include statements\n- Using undefined functions or variables\n- API misuse (mixing different kernel subsystems)\n- Syntax errors or typos\n\n"
        
        if evaluation_result.static_analysis.sparse_issues > 0:
            feedback += f"STATIC ANALYSIS ISSUES ({evaluation_result.static_analysis.sparse_issues} Sparse issues):\n- Check for type mismatches\n- Verify pointer usage\n- Fix endianness issues\n- Address context violations (atomic vs non-atomic)\n\n"
        
        if evaluation_result.static_analysis.checkpatch_violations > 10:
            feedback += f"CODING STYLE VIOLATIONS ({evaluation_result.static_analysis.checkpatch_violations} violations):\n- Use proper Linux kernel coding style\n- Place opening braces correctly (functions: next line, others: same line)\n- Follow 80-column limit\n- Add SPDX license header: // SPDX-License-Identifier: GPL-2.0\n- Don't initialize static variables to NULL\n\n"
        
        if evaluation_result.static_analysis.api_compliance_score < 0.5:
            feedback += "API USAGE ERRORS:\n- Ensure all kmalloc() calls are paired with kfree()\n- Don't call kfree() on statically allocated buffers\n- Match all register_chrdev() with unregister_chrdev()\n- Match all class_create() with class_destroy()\n- Use correct function signatures for file_operations\n\n"
        
        security_score = (evaluation_result.security.buffer_safety_score + evaluation_result.security.input_validation_score) / 2
        if security_score < 0.8:
            feedback += "SECURITY CONCERNS:\n- Validate user input sizes before copying\n- Use copy_from_user() and copy_to_user() correctly\n- Check buffer boundaries\n- Handle edge cases in read/write operations\n\n"
        
        if evaluation_result.functionality.basic_operations_score < 1.0:
            feedback += "FUNCTIONALITY ISSUES:\n- Implement proper open/release functions for character devices\n- Don't mix seq_file APIs with character device APIs\n- Use simple return 0 for open, not single_open()\n- Implement proper file position handling\n\n"
        
        if evaluation_result.functionality.error_handling_score < 0.5:
            feedback += "ERROR HANDLING:\n- Check return values of all kernel API calls\n- Use proper error codes (-ENOMEM, -EFAULT, -EINVAL)\n- Implement proper cleanup in error paths\n- Don't return uninitialized variables\n\n"
        
        feedback += self._analyze_specific_issues(code)
        
        feedback += "\nFOCUS AREAS FOR NEXT ITERATION:\n1. Fix compilation errors first\n2. Use correct file_operations function signatures\n3. Follow kernel coding style guidelines\n4. Implement proper error handling\n5. Use appropriate kernel APIs for character devices\n\nREMEMBER:\n- Character devices use simple file operations, not seq_file\n- Static buffers don't need kfree()\n- Always check API return values\n- Follow Linux kernel coding style exactly"
        
        return feedback
    
    def _analyze_specific_issues(self, code: str) -> str:
        issues = []
        
        if "single_open" in code:
            issues.append("- Remove single_open() - use simple return 0 for character device open()")
        
        if "single_release" in code:
            issues.append("- Remove single_release - use simple return 0 for character device release()")
        
        if "kfree(buffer)" in code and "static char buffer" in code:
            issues.append("- Don't call kfree() on static buffers - only on kmalloc'd memory")
        
        if "class_unregister" in code:
            issues.append("- class_unregister() doesn't exist - use only class_destroy()")
        
        if "return result;" in code and "result" not in code.split("return result;")[0].split("\n")[-1]:
            issues.append("- Don't return uninitialized variables - check your return statements")
        
        if issues:
            return f"\nSPECIFIC ISSUES FOUND IN YOUR CODE:\n" + "\n".join(issues) + "\n"
        
        return ""


class IterativeTrainingLoop:
    def __init__(self, model: str = "qwen2.5:latest", test_type: str = "simple_char_driver"):
        self.model = model
        self.test_type = test_type
        self.feedback_generator = FeedbackGenerator()
        self.kernel_standards = load_kernel_standards()
        self.test_prompts = generate_test_prompts()
        self.test_config = next((t for t in self.test_prompts if t["name"] == test_type), self.test_prompts[0])
        
        Path("results").mkdir(exist_ok=True)
    
    def run_training_loop(self, num_iterations: int = 5) -> List[Dict]:
        results = []
        current_feedback = ""
        
        for iteration in range(1, num_iterations + 1):
            code = self._generate_code_with_feedback(iteration, current_feedback)
            
            code_file = f"results/iteration_{iteration}_{self.test_type}.c"
            with open(code_file, "w") as f:
                f.write(code)
            
            evaluation_result = self.feedback_generator.scoring_engine.evaluate_driver_code(code_file)
            
            result_file = f"results/iteration_{iteration}_results.json"
            self.feedback_generator.scoring_engine.export_results(evaluation_result, result_file)
            
            if iteration < num_iterations:
                current_feedback = self.feedback_generator.generate_detailed_feedback(
                    code, evaluation_result, iteration
                )
                
                feedback_file = f"results/iteration_{iteration}_feedback.txt"
                with open(feedback_file, "w") as f:
                    f.write(current_feedback)
            
            iteration_result = {
                "iteration": iteration,
                "overall_score": evaluation_result.overall_score,
                "compilation_success": evaluation_result.compilation.success,
                "static_analysis_score": evaluation_result.weighted_scores.get('static_analysis', 0),
                "security_score": evaluation_result.weighted_scores.get('security', 0),
                "code_quality_score": evaluation_result.weighted_scores.get('code_quality', 0),
                "functionality_score": evaluation_result.weighted_scores.get('functionality', 0),
                "code_file": code_file,
                "result_file": result_file
            }
            
            results.append(iteration_result)
            self._print_iteration_summary(iteration_result)
            time.sleep(1)
        
        self._generate_final_report(results)
        return results
    
    def _generate_code_with_feedback(self, iteration: int, feedback: str) -> str:
        if iteration == 1:
            prompt = self.test_config["prompt"]
        else:
            prompt = f"""{self.test_config["prompt"]}

PREVIOUS ITERATION FEEDBACK:
{feedback}

Please fix ALL the issues mentioned in the feedback above.
Pay special attention to:
1. Compilation errors
2. Correct API usage for character devices
3. Proper error handling
4. Linux kernel coding style

Return only the corrected C code, no explanations."""
        
        return ask_ollama_stream(prompt, self.model, self.kernel_standards)
    
    def _print_iteration_summary(self, result: Dict):
        compile_status = "PASS" if result['compilation_success'] else "FAIL"
        print(f"Iteration {result['iteration']}: Score {result['overall_score']:.3f}, Compile {compile_status}")
    
    def _generate_final_report(self, results: List[Dict]):
        print(f"\n{'Iter':<4} {'Score':<6} {'Compile':<8} {'Static':<8} {'Security':<8} {'Quality':<8} {'Function':<8}")
        print("-" * 60)
        
        for result in results:
            compile_status = "PASS" if result['compilation_success'] else "FAIL"
            print(f"{result['iteration']:<4} "
                  f"{result['overall_score']:<6.3f} "
                  f"{compile_status:<8} "
                  f"{result['static_analysis_score']:<8.3f} "
                  f"{result['security_score']:<8.3f} "
                  f"{result['code_quality_score']:<8.3f} "
                  f"{result['functionality_score']:<8.3f}")
        
        first_score = results[0]['overall_score']
        last_score = results[-1]['overall_score']
        improvement = last_score - first_score
        
        print(f"\nInitial Score: {first_score:.3f}")
        print(f"Final Score: {last_score:.3f}")
        print(f"Improvement: {improvement:+.3f}")
        
        compilation_progress = [r['compilation_success'] for r in results]
        first_compile = next((i for i, success in enumerate(compilation_progress) if success), None)
        if first_compile is not None:
            print(f"First successful compilation: Iteration {first_compile + 1}")
        else:
            print("No successful compilations achieved")
        
        best_iteration = max(results, key=lambda x: x['overall_score'])
        print(f"Best iteration: {best_iteration['iteration']} (Score: {best_iteration['overall_score']:.3f})")
        
        summary = {
            "model": self.model,
            "test_type": self.test_type,
            "iterations": results,
            "improvement": improvement,
            "first_successful_compilation": first_compile,
            "best_iteration": best_iteration['iteration']
        }
        
        with open("results/training_summary.json", "w") as f:
            json.dump(summary, f, indent=2)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Iterative Training Loop for AI Code Generation")
    parser.add_argument("--model", default="qwen2.5:latest", help="Model to train")
    parser.add_argument("--test", default="simple_char_driver", 
                       choices=["simple_char_driver", "gpio_platform_driver", "proc_interface_driver"],
                       help="Test type")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations")
    
    args = parser.parse_args()
    
    trainer = IterativeTrainingLoop(args.model, args.test)
    trainer.run_training_loop(args.iterations)


if __name__ == "__main__":
    main()