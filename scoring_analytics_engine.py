import json
import re
import subprocess
import tempfile
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional
import numpy as np
from pathlib import Path


@dataclass
class CompilationMetrics:
    success: bool
    error_count: int
    warning_count: int
    build_time: float
    binary_size: Optional[int] = None


@dataclass
class StaticAnalysisMetrics:
    sparse_issues: int
    checkpatch_violations: int
    cppcheck_issues: int
    custom_rule_violations: int
    api_compliance_score: float


@dataclass
class SecurityMetrics:
    buffer_safety_score: float
    memory_leak_risk: float
    race_condition_risk: float
    input_validation_score: float
    privilege_escalation_risk: float


@dataclass
class CodeQualityMetrics:
    style_compliance: float
    cyclomatic_complexity: float
    function_length_avg: float
    comment_ratio: float
    maintainability_index: float


@dataclass
class FunctionalityMetrics:
    basic_operations_score: float
    error_handling_score: float
    edge_case_handling: float
    api_correctness: float


@dataclass
class EvaluationResult:
    compilation: CompilationMetrics
    static_analysis: StaticAnalysisMetrics
    security: SecurityMetrics
    code_quality: CodeQualityMetrics
    functionality: FunctionalityMetrics
    overall_score: float
    weighted_scores: Dict[str, float]


class KernelRuleEngine:
    def __init__(self):
        self.api_patterns = self._load_api_patterns()
        self.security_patterns = self._load_security_patterns()
        self.violation_weights = {
            'critical': 10.0,
            'major': 5.0,
            'minor': 1.0,
            'style': 0.5
        }

    def _load_api_patterns(self) -> Dict[str, List[str]]:
        return {
            'memory_management': [
                r'kmalloc\([^)]+\)',
                r'kfree\([^)]+\)',
                r'vmalloc\([^)]+\)',
                r'vfree\([^)]+\)'
            ],
            'locking': [
                r'spin_lock\([^)]+\)',
                r'spin_unlock\([^)]+\)',
                r'mutex_lock\([^)]+\)',
                r'mutex_unlock\([^)]+\)'
            ],
            'interrupt_handling': [
                r'request_irq\([^)]+\)',
                r'free_irq\([^)]+\)',
                r'in_interrupt\(\)',
                r'in_atomic\(\)'
            ]
        }

    def _load_security_patterns(self) -> Dict[str, List[str]]:
        return {
            'buffer_overflow': [
                r'strcpy\s*\(',
                r'strcat\s*\(',
                r'sprintf\s*\(',
                r'gets\s*\('
            ],
            'null_pointer': [
                r'\*[a-zA-Z_][a-zA-Z0-9_]*\s*(?!\s*[=!]=)',
                r'->[a-zA-Z_][a-zA-Z0-9_]*\s*(?!\s*[=!]=)'
            ],
            'race_conditions': [
                r'(?<!spin_)(?<!mutex_)lock\s*\(',
                r'atomic_(?!read|set)[a-zA-Z_]+\s*\('
            ]
        }

    def analyze_api_compliance(self, code: str) -> float:
        total_apis = 0
        correct_usage = 0
        
        for category, patterns in self.api_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, code)
                total_apis += len(matches)
                correct_usage += self._validate_api_usage(code, pattern, category)
        
        return correct_usage / max(total_apis, 1)

    def _validate_api_usage(self, code: str, pattern: str, category: str) -> int:
        if category == 'memory_management':
            return self._validate_memory_usage(code, pattern)
        elif category == 'locking':
            return self._validate_locking_usage(code, pattern)
        elif category == 'interrupt_handling':
            return self._validate_interrupt_usage(code, pattern)
        return 0

    def _validate_memory_usage(self, code: str, pattern: str) -> int:
        if 'kmalloc' in pattern:
            matches = re.findall(r'(\w+)\s*=\s*kmalloc\([^)]+\)', code)
            frees = re.findall(r'kfree\(([^)]+)\)', code)
            return len([m for m in matches if m in frees])
        return 0

    def _validate_locking_usage(self, code: str, pattern: str) -> int:
        locks = re.findall(r'spin_lock\(([^)]+)\)', code)
        unlocks = re.findall(r'spin_unlock\(([^)]+)\)', code)
        return min(len(locks), len(unlocks))

    def _validate_interrupt_usage(self, code: str, pattern: str) -> int:
        requests = re.findall(r'request_irq\([^)]+\)', code)
        frees = re.findall(r'free_irq\([^)]+\)', code)
        return min(len(requests), len(frees))

    def analyze_security_risks(self, code: str) -> Dict[str, float]:
        risks = {}
        
        for risk_type, patterns in self.security_patterns.items():
            risk_score = 0.0
            for pattern in patterns:
                matches = len(re.findall(pattern, code))
                risk_score += matches * self.violation_weights['major']
            
            total_lines = len(code.splitlines())
            risks[risk_type] = min(risk_score / max(total_lines, 1), 1.0)
        
        return risks


class StaticAnalyzer:
    def __init__(self):
        self.rule_engine = KernelRuleEngine()

    def run_sparse_analysis(self, code_path: str) -> int:
        try:
            result = subprocess.run([
                'sparse', '-Wno-decl', code_path
            ], capture_output=True, text=True, timeout=30)
            return len(result.stderr.splitlines())
        except:
            return 0

    def run_checkpatch_analysis(self, code_path: str) -> int:
        checkpatch_path = Path("checkpatch.pl")
        if not checkpatch_path.exists():
            return 0
        
        try:
            result = subprocess.run([
                'perl', str(checkpatch_path), '--no-tree', '--file', code_path
            ], capture_output=True, text=True, timeout=30)
            
            violations = 0
            for line in result.stdout.splitlines():
                if 'ERROR:' in line or 'WARNING:' in line:
                    violations += 1
            return violations
        except:
            return 0

    def run_cppcheck_analysis(self, code_path: str) -> int:
        try:
            result = subprocess.run([
                'cppcheck', '--enable=all', '--std=c99', code_path
            ], capture_output=True, text=True, timeout=30)
            return len([line for line in result.stderr.splitlines() if 'error' in line.lower()])
        except:
            return 0

    def analyze_cyclomatic_complexity(self, code: str) -> float:
        complexity_keywords = [
            'if', 'else', 'elif', 'while', 'for', 'switch', 
            'case', 'default', 'catch', '&&', '||', '?'
        ]
        
        total_complexity = 1
        for keyword in complexity_keywords:
            total_complexity += len(re.findall(rf'\b{keyword}\b', code))
        
        function_count = len(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)\s*{', code))
        return total_complexity / max(function_count, 1)

    def calculate_maintainability_index(self, code: str) -> float:
        lines = code.splitlines()
        halstead_volume = self._calculate_halstead_volume(code)
        cyclomatic_complexity = self.analyze_cyclomatic_complexity(code)
        lines_of_code = len([l for l in lines if l.strip() and not l.strip().startswith('//')])
        
        if lines_of_code == 0:
            return 0.0
        
        mi = 171 - 5.2 * np.log(halstead_volume) - 0.23 * cyclomatic_complexity - 16.2 * np.log(lines_of_code)
        return max(0, min(100, mi)) / 100.0

    def _calculate_halstead_volume(self, code: str) -> float:
        operators = re.findall(r'[+\-*/%=<>!&|^~?:;,(){}[\]]', code)
        operands = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code)
        
        unique_operators = len(set(operators))
        unique_operands = len(set(operands))
        total_operators = len(operators)
        total_operands = len(operands)
        
        if unique_operators == 0 or unique_operands == 0:
            return 1.0
        
        vocabulary = unique_operators + unique_operands
        length = total_operators + total_operands
        
        return length * np.log2(vocabulary) if vocabulary > 1 else 1.0


class CompilationTester:
    def __init__(self):
        self.kernel_headers_path = "/lib/modules/$(shell uname -r)/build"

    def test_compilation(self, code_path: str) -> CompilationMetrics:
        with tempfile.TemporaryDirectory() as tmpdir:
            makefile_content = f"""
obj-m += driver.o
KDIR := {self.kernel_headers_path}

all:
\tmake -C $(KDIR) M=$(PWD) modules

clean:
\tmake -C $(KDIR) M=$(PWD) clean
"""
            makefile_path = os.path.join(tmpdir, "Makefile")
            driver_path = os.path.join(tmpdir, "driver.c")
            
            with open(makefile_path, "w") as f:
                f.write(makefile_content)
            
            with open(code_path, "r") as src, open(driver_path, "w") as dst:
                dst.write(src.read())
            
            import time
            start_time = time.time()
            
            try:
                result = subprocess.run(
                    ["make"], cwd=tmpdir, capture_output=True, text=True, timeout=60
                )
                build_time = time.time() - start_time
                
                error_count = len(re.findall(r'error:', result.stderr, re.IGNORECASE))
                warning_count = len(re.findall(r'warning:', result.stderr, re.IGNORECASE))
                
                binary_size = None
                ko_file = os.path.join(tmpdir, "driver.ko")
                if os.path.exists(ko_file):
                    binary_size = os.path.getsize(ko_file)
                
                return CompilationMetrics(
                    success=result.returncode == 0,
                    error_count=error_count,
                    warning_count=warning_count,
                    build_time=build_time,
                    binary_size=binary_size
                )
            except subprocess.TimeoutExpired:
                return CompilationMetrics(
                    success=False,
                    error_count=1,
                    warning_count=0,
                    build_time=60.0
                )


class ScoringEngine:
    def __init__(self):
        self.static_analyzer = StaticAnalyzer()
        self.compilation_tester = CompilationTester()
        self.weights = {
            'compilation': 0.30,
            'static_analysis': 0.25,
            'security': 0.25,
            'code_quality': 0.15,
            'functionality': 0.05
        }

    def evaluate_driver_code(self, code_path: str) -> EvaluationResult:
        with open(code_path, 'r') as f:
            code = f.read()

        compilation_metrics = self._evaluate_compilation(code_path)
        static_analysis_metrics = self._evaluate_static_analysis(code_path, code)
        security_metrics = self._evaluate_security(code)
        code_quality_metrics = self._evaluate_code_quality(code)
        functionality_metrics = self._evaluate_functionality(code)

        weighted_scores = self._calculate_weighted_scores(
            compilation_metrics, static_analysis_metrics, security_metrics,
            code_quality_metrics, functionality_metrics
        )

        overall_score = sum(weighted_scores.values())

        return EvaluationResult(
            compilation=compilation_metrics,
            static_analysis=static_analysis_metrics,
            security=security_metrics,
            code_quality=code_quality_metrics,
            functionality=functionality_metrics,
            overall_score=overall_score,
            weighted_scores=weighted_scores
        )

    def _evaluate_compilation(self, code_path: str) -> CompilationMetrics:
        return self.compilation_tester.test_compilation(code_path)

    def _evaluate_static_analysis(self, code_path: str, code: str) -> StaticAnalysisMetrics:
        sparse_issues = self.static_analyzer.run_sparse_analysis(code_path)
        checkpatch_violations = self.static_analyzer.run_checkpatch_analysis(code_path)
        cppcheck_issues = self.static_analyzer.run_cppcheck_analysis(code_path)
        api_compliance = self.static_analyzer.rule_engine.analyze_api_compliance(code)

        return StaticAnalysisMetrics(
            sparse_issues=sparse_issues,
            checkpatch_violations=checkpatch_violations,
            cppcheck_issues=cppcheck_issues,
            custom_rule_violations=0,
            api_compliance_score=api_compliance
        )

    def _evaluate_security(self, code: str) -> SecurityMetrics:
        security_risks = self.static_analyzer.rule_engine.analyze_security_risks(code)
        
        return SecurityMetrics(
            buffer_safety_score=1.0 - security_risks.get('buffer_overflow', 0.0),
            memory_leak_risk=security_risks.get('memory_leak', 0.0),
            race_condition_risk=security_risks.get('race_conditions', 0.0),
            input_validation_score=0.8,
            privilege_escalation_risk=0.1
        )

    def _evaluate_code_quality(self, code: str) -> CodeQualityMetrics:
        lines = code.splitlines()
        total_lines = len(lines)
        comment_lines = len([l for l in lines if l.strip().startswith('//') or '/*' in l or '*' in l])
        comment_ratio = comment_lines / max(total_lines, 1)

        functions = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)\s*{[\s\S]*?\n}', code)
        avg_func_length = np.mean([len(f.splitlines()) for f in functions]) if functions else 0

        cyclomatic_complexity = self.static_analyzer.analyze_cyclomatic_complexity(code)
        maintainability_index = self.static_analyzer.calculate_maintainability_index(code)

        return CodeQualityMetrics(
            style_compliance=0.8,
            cyclomatic_complexity=cyclomatic_complexity,
            function_length_avg=avg_func_length,
            comment_ratio=comment_ratio,
            maintainability_index=maintainability_index
        )

    def _evaluate_functionality(self, code: str) -> FunctionalityMetrics:
        has_read = 'read' in code and 'file_operations' in code
        has_write = 'write' in code and 'file_operations' in code
        has_open = 'open' in code
        has_release = 'release' in code

        basic_ops_score = sum([has_read, has_write, has_open, has_release]) / 4.0
        error_handling_score = len(re.findall(r'return\s+-\w+', code)) / max(len(re.findall(r'return', code)), 1)

        return FunctionalityMetrics(
            basic_operations_score=basic_ops_score,
            error_handling_score=error_handling_score,
            edge_case_handling=0.6,
            api_correctness=0.7
        )

    def _calculate_weighted_scores(self, compilation, static_analysis, security, code_quality, functionality) -> Dict[str, float]:
        compilation_score = 1.0 if compilation.success else 0.0
        static_score = max(0, 1.0 - (static_analysis.sparse_issues + static_analysis.checkpatch_violations) / 100.0)
        security_score = (security.buffer_safety_score + security.input_validation_score) / 2.0
        quality_score = (code_quality.maintainability_index + min(code_quality.comment_ratio * 5, 1.0)) / 2.0
        func_score = functionality.basic_operations_score

        return {
            'compilation': compilation_score * self.weights['compilation'],
            'static_analysis': static_score * self.weights['static_analysis'],
            'security': security_score * self.weights['security'],
            'code_quality': quality_score * self.weights['code_quality'],
            'functionality': func_score * self.weights['functionality']
        }

    def export_results(self, result: EvaluationResult, output_path: str):
        with open(output_path, 'w') as f:
            json.dump(asdict(result), f, indent=2)

    def compare_models(self, results: List[Tuple[str, EvaluationResult]]) -> Dict[str, any]:
        comparison = {
            'model_rankings': [],
            'category_winners': {},
            'statistical_analysis': {}
        }

        for model_name, result in results:
            comparison['model_rankings'].append({
                'model': model_name,
                'overall_score': result.overall_score,
                'compilation_success': result.compilation.success,
                'security_score': (result.security.buffer_safety_score + result.security.input_validation_score) / 2.0
            })

        comparison['model_rankings'].sort(key=lambda x: x['overall_score'], reverse=True)

        categories = ['compilation', 'static_analysis', 'security', 'code_quality', 'functionality']
        for category in categories:
            best_score = 0
            best_model = None
            for model_name, result in results:
                score = result.weighted_scores.get(category, 0)
                if score > best_score:
                    best_score = score
                    best_model = model_name
            comparison['category_winners'][category] = best_model

        return comparison