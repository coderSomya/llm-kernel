import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple
import argparse
from scoring_analytics_engine import ScoringEngine, EvaluationResult


class OllamaInterface:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        
    def generate_driver_code(self, prompt: str, model: str = "qwen2.5:latest", 
                           system_prompt: str = None) -> str:
        url = f"{self.base_url}/api/chat"
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
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


class PromptGenerator:
    def __init__(self):
        self.base_prompts = {
            "character_device": """
Create a simple character device driver that supports basic read/write operations with a
{buffer_size} internal buffer. Include proper module initialization and cleanup functions.
""",
            "block_device": """
Create a basic block device driver that handles read/write requests with a {block_size} block size.
Include request queue handling and proper error management.
""",
            "network_device": """
Create a simple network device driver that can transmit and receive packets.
Include basic network interface operations and statistics.
""",
            "platform_device": """
Implement a platform device driver for a memory-mapped GPIO controller with interrupt support.
Include device tree binding and power management.
""",
            "usb_device": """
Create a USB device driver for a simple bulk transfer device.
Include probe/disconnect functions and endpoint management.
"""
        }
        
        self.complexity_modifiers = {
            "basic": "Focus on core functionality only.",
            "intermediate": "Include proper error handling and edge cases.",
            "advanced": "Add performance optimizations and advanced features like DMA support."
        }
        
        self.style_requirements = """
Return only the code, no other text. No backticks. Just the executable C code.
Follow the Linux kernel coding style strictly.
Use the latest Linux kernel version APIs.
Include proper error handling and resource cleanup.
Do not include any explanations or comments outside the code.
"""

    def generate_prompt(self, driver_type: str, complexity: str = "basic", **kwargs) -> str:
        if driver_type not in self.base_prompts:
            raise ValueError(f"Unknown driver type: {driver_type}")
        
        base_prompt = self.base_prompts[driver_type].format(**kwargs)
        complexity_mod = self.complexity_modifiers.get(complexity, "")
        
        return f"{base_prompt}\n{complexity_mod}\n{self.style_requirements}"


class TestSuiteRunner:
    def __init__(self, models: List[str], output_dir: str = "evaluation_results"):
        self.models = models
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.ollama = OllamaInterface()
        self.prompt_gen = PromptGenerator()
        self.scoring_engine = ScoringEngine()
        
    def load_kernel_standards(self, standards_file: str = "kernel_standards.txt") -> str:
        try:
            with open(standards_file, "r") as f:
                return f.read()
        except FileNotFoundError:
            return self._get_default_kernel_standards()
    
    def _get_default_kernel_standards(self) -> str:
        return """
You are an expert Linux kernel developer. Follow these guidelines:
1. Use proper kernel coding style (8-space tabs, 80-column limit)
2. Include all necessary headers (#include <linux/module.h>, etc.)
3. Use proper error codes (-ENOMEM, -EINVAL, etc.)
4. Always check return values and handle errors
5. Use kernel memory allocation functions (kmalloc, kfree)
6. Follow GPL licensing requirements
7. Use proper locking mechanisms when needed
8. Handle module initialization and cleanup correctly
"""

    def run_single_evaluation(self, model: str, driver_type: str, 
                            complexity: str = "basic", test_id: str = None) -> Tuple[str, EvaluationResult]:
        if test_id is None:
            test_id = f"{model}_{driver_type}_{complexity}_{int(time.time())}"
        
        print(f"Evaluating {model} on {driver_type} driver ({complexity})...")
        
        kernel_standards = self.load_kernel_standards()
        prompt = self.prompt_gen.generate_prompt(
            driver_type, complexity, 
            buffer_size="1KB", block_size="512 bytes"
        )
        
        generated_code = self.ollama.generate_driver_code(prompt, model, kernel_standards)
        
        code_file = self.output_dir / f"{test_id}_generated.c"
        with open(code_file, "w") as f:
            f.write(generated_code)
        
        result = self.scoring_engine.evaluate_driver_code(str(code_file))
        
        result_file = self.output_dir / f"{test_id}_results.json"
        self.scoring_engine.export_results(result, str(result_file))
        
        print(f"  Overall Score: {result.overall_score:.2f}")
        print(f"  Compilation: {'PASS' if result.compilation.success else 'FAIL'}")
        print(f"  Security Score: {(result.security.buffer_safety_score + result.security.input_validation_score) / 2:.2f}")
        
        return test_id, result

    def run_comprehensive_evaluation(self) -> Dict[str, List[Tuple[str, EvaluationResult]]]:
        driver_types = ["character_device", "block_device", "network_device"]
        complexity_levels = ["basic", "intermediate"]
        
        all_results = {}
        
        for model in self.models:
            model_results = []
            print(f"\n=== Evaluating Model: {model} ===")
            
            for driver_type in driver_types:
                for complexity in complexity_levels:
                    try:
                        test_id, result = self.run_single_evaluation(
                            model, driver_type, complexity
                        )
                        model_results.append((test_id, result))
                        time.sleep(1)
                    except Exception as e:
                        print(f"Error evaluating {model} on {driver_type}: {e}")
                        
            all_results[model] = model_results
        
        return all_results

    def generate_comparison_report(self, all_results: Dict[str, List[Tuple[str, EvaluationResult]]]) -> Dict:
        model_summaries = []
        
        for model, results in all_results.items():
            if not results:
                continue
                
            scores = [r[1].overall_score for r in results]
            compilation_success = [r[1].compilation.success for r in results]
            
            summary = {
                'model': model,
                'avg_score': sum(scores) / len(scores),
                'max_score': max(scores),
                'min_score': min(scores),
                'compilation_success_rate': sum(compilation_success) / len(compilation_success),
                'total_tests': len(results)
            }
            model_summaries.append(summary)
        
        model_summaries.sort(key=lambda x: x['avg_score'], reverse=True)
        
        comparison_results = []
        for model, results in all_results.items():
            for test_id, result in results:
                comparison_results.append((model, result))
        
        detailed_comparison = self.scoring_engine.compare_models(comparison_results)
        
        report = {
            'summary': model_summaries,
            'detailed_comparison': detailed_comparison,
            'timestamp': time.time()
        }
        
        report_file = self.output_dir / "comparison_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        return report

    def print_summary_report(self, report: Dict):
        print("\n" + "="*60)
        print("MODEL PERFORMANCE SUMMARY")
        print("="*60)
        
        for i, summary in enumerate(report['summary'], 1):
            print(f"{i}. {summary['model']}")
            print(f"   Average Score: {summary['avg_score']:.2f}")
            print(f"   Compilation Success Rate: {summary['compilation_success_rate']:.1%}")
            print(f"   Score Range: {summary['min_score']:.2f} - {summary['max_score']:.2f}")
            print(f"   Total Tests: {summary['total_tests']}")
            print()
        
        print("CATEGORY WINNERS:")
        winners = report['detailed_comparison']['category_winners']
        for category, winner in winners.items():
            print(f"  {category.title()}: {winner}")


def main():
    parser = argparse.ArgumentParser(description="Linux Driver AI Model Evaluation Framework")
    parser.add_argument("--models", nargs="+", default=["qwen2.5:latest"], 
                       help="List of models to evaluate")
    parser.add_argument("--driver-type", choices=["character_device", "block_device", "network_device"], 
                       help="Single driver type to test")
    parser.add_argument("--complexity", choices=["basic", "intermediate", "advanced"], 
                       default="basic", help="Complexity level")
    parser.add_argument("--output-dir", default="evaluation_results", 
                       help="Output directory for results")
    parser.add_argument("--comprehensive", action="store_true", 
                       help="Run comprehensive evaluation across all driver types")
    
    args = parser.parse_args()
    
    runner = TestSuiteRunner(args.models, args.output_dir)
    
    if args.comprehensive:
        print("Running comprehensive evaluation...")
        all_results = runner.run_comprehensive_evaluation()
        report = runner.generate_comparison_report(all_results)
        runner.print_summary_report(report)
    elif args.driver_type:
        print(f"Running single evaluation for {args.driver_type}...")
        for model in args.models:
            test_id, result = runner.run_single_evaluation(
                model, args.driver_type, args.complexity
            )
            print(f"\nDetailed Results for {model}:")
            print(f"  Test ID: {test_id}")
            print(f"  Overall Score: {result.overall_score:.2f}")
            print(f"  Compilation: {'PASS' if result.compilation.success else 'FAIL'}")
            print(f"  Build Time: {result.compilation.build_time:.2f}s")
            print(f"  Static Analysis Issues: {result.static_analysis.sparse_issues + result.static_analysis.checkpatch_violations}")
            print(f"  Security Score: {(result.security.buffer_safety_score + result.security.input_validation_score) / 2:.2f}")
            print(f"  Code Quality Score: {result.code_quality.maintainability_index:.2f}")
    else:
        print("Please specify --driver-type or use --comprehensive for full evaluation")


if __name__ == "__main__":
    main()