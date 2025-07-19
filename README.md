# Linux Device Driver LLM Evaluation Framework

## Overview

This project evaluates Large Language Models (LLMs) for their ability to generate Linux kernel device drivers. It provides a comprehensive framework that tests LLM-generated driver code across multiple dimensions including compilation success, static analysis, security vulnerabilities, code quality, and functionality.

## Assignment Goals

- **Automated Evaluation**: Test LLMs on various driver types (character, block, network, platform, USB)
- **Multi-dimensional Scoring**: Assess code quality, security, compilation, and functionality
- **Comparative Analysis**: Compare different models' performance across driver generation tasks
- **Standardized Testing**: Provide consistent evaluation metrics for LLM-generated kernel code

## Project Structure

```
main files
├── evaluation_pipeline.py      # Main orchestration script
├── scoring_analytics_engine.py # Core evaluation and scoring logic
├── evaluation_config.py        # Configuration and test definitions
├── enhanced_evaluation.py     # Extended evaluation features
├── kernel_standards.txt       # Linux kernel coding standards
├── generated_driver.c         # Output from driver generation
├── requirements.txt           # Python dependencies
└── README.md                 # This file

standalone testing files
├── analyze_kernel_code.py      # Standalone kernel code analysis
├── trial.py                   # Simple driver generation test

docker files
├── Dockerfile                 # Docker container definition
├── run.sh                     # Docker execution script
├── run_training.sh            # Training execution script
└── debug.sh                   # Debug container script
```

## Workflow

1. **Prompt Generation**: Creates specific prompts for different driver types and complexity levels
2. **LLM Interaction**: Sends prompts to Ollama API and receives generated C code
3. **Code Analysis**: Evaluates generated code using multiple tools:
   - Compilation testing with kernel module build system
   - Static analysis with sparse, cppcheck, and checkpatch
   - Security vulnerability detection
   - Code quality metrics (complexity, maintainability)
4. **Scoring**: Calculates weighted scores across all evaluation dimensions
5. **Reporting**: Generates detailed comparison reports and performance summaries

## Prerequisites

### System Requirements
- **Docker**: Docker Engine installed and running
- **Ollama**: Running locally with required models
- **Network Access**: For Docker to communicate with host Ollama service

### Python Dependencies
```bash
pip install -r requirements.txt
```

## Installation

### 1. Install Docker
```bash
# Install Docker (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo systemctl enable docker

# Or use Docker Desktop for other platforms
```

### 2. Start Ollama
```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required model
ollama pull qwen2.5:latest

# Start Ollama service
ollama serve
```

### 3. Build Docker Image
```bash
docker build -t driver-eval .
```

## Usage

### Docker-based Evaluation
```bash
# Run comprehensive evaluation
./run.sh --comprehensive --models qwen2.5:latest

# Run single driver type test
./run.sh --driver-type character_device --complexity basic --models qwen2.5:latest

# Run training loop
./run_training.sh --epochs 10 --models qwen2.5:latest
```

### Local Development
```bash
# Install Python dependencies locally
pip install -r requirements.txt

# Run evaluation pipeline locally
python evaluation_pipeline.py --comprehensive --models qwen2.5:latest

# Quick trial (generate single driver)
python trial.py
```

### Debug Container
```bash
# Access container shell for debugging
./debug.sh
```

## Results

### Output Structure
```
results/
├── {model}_{driver_type}_{complexity}_{timestamp}_generated.c
├── {model}_{driver_type}_{complexity}_{timestamp}_results.json
└── comparison_report.json
```

### Scoring Categories
- **Compilation (30%)**: Success/failure, build time, binary size
- **Static Analysis (25%)**: Sparse issues, checkpatch violations, cppcheck issues
- **Security (25%)**: Buffer safety, memory leaks, race conditions, input validation
- **Code Quality (15%)**: Style compliance, complexity, maintainability
- **Functionality (5%)**: Basic operations, error handling, API correctness

## Configuration

### Available Driver Types
- `character_device`: Simple read/write device drivers
- `block_device`: Block storage device drivers
- `network_device`: Network interface drivers
- `platform_device`: Platform-specific device drivers
- `usb_device`: USB device drivers

### Complexity Levels
- `basic`: Core functionality only
- `intermediate`: Includes error handling and edge cases
- `advanced`: Performance optimizations and advanced features

### Customizing Evaluation
Edit `evaluation_config.py` to modify:
- Scoring weights for different categories
- Test configurations for different driver types
- Security patterns and kernel API rules
- Tool configurations (timeouts, enabled tools)

## File Descriptions

### Core Files

#### `evaluation_pipeline.py`
Main orchestration script that coordinates the entire evaluation process.
- CLI interface for running evaluations
- Integration with Ollama API
- Prompt generation for different driver types
- Results collection and reporting
- Comprehensive evaluation across multiple models and driver types

#### `scoring_analytics_engine.py`
Core evaluation engine that analyzes generated driver code.
- Compilation testing using kernel module build system
- Static analysis integration (sparse, cppcheck, checkpatch)
- Security vulnerability detection
- Code quality metrics calculation
- Weighted scoring across multiple dimensions

#### `evaluation_config.py`
Configuration management and test definitions.
- Scoring weights and tool configurations
- Test configurations for different driver types
- Kernel API compliance rules
- Security vulnerability patterns
- Default evaluation settings

#### `enhanced_evaluation.py`
Extended evaluation features with training capabilities.
- Advanced evaluation metrics
- Training loop for model improvement
- Extended reporting capabilities

### Docker Files

#### `Dockerfile`
Defines the Docker container environment.
- Ubuntu 22.04 base image
- Linux kernel headers and build tools
- Python dependencies
- Static analysis tools (sparse, cppcheck)

#### `run.sh`
Main execution script for Docker-based evaluation.
- Automatic IP detection for Ollama connection
- Volume mounting for results
- Environment variable configuration

#### `run_training.sh`
Training execution script for model improvement.
- Training loop execution
- Model parameter optimization
- Extended evaluation capabilities

### Standalone Files

#### `analyze_kernel_code.py`
Standalone script for analyzing individual kernel driver files.
- Compilation testing
- Static analysis
- Kernel coding style checking
- Code metrics calculation
- Automatic download of checkpatch.pl

#### `trial.py`
Simple test script for generating a single driver.
- Basic Ollama integration
- Driver generation with kernel standards
- Output to generated_driver.c

## Troubleshooting

### Common Issues

#### Ollama Connection Error
```
Error communicating with Ollama: Connection refused
```
**Solution**: Ensure Ollama is running (`ollama serve`) and the model is pulled.

#### Docker Build Failures
```
docker: command not found
```
**Solution**: Install Docker and ensure the service is running.

#### Network Connectivity Issues
```
Cannot reach Ollama at HOST_IP:11434
```
**Solution**: Check that Ollama is running and accessible from the Docker container.

#### Permission Issues
```
Permission denied: checkpatch.pl
```
**Solution**: The Docker container automatically handles permissions for checkpatch.pl.

### Debug Mode
Access the container shell for debugging:
```bash
./debug.sh
```

## Score Interpretation

### Score Breakdown
- **90-100**: Excellent - Production-ready code
- **70-89**: Good - Minor issues, mostly functional
- **50-69**: Fair - Some issues, needs improvement
- **30-49**: Poor - Significant issues
- **0-29**: Failed - Major problems

### Key Metrics
- **Compilation Success Rate**: Percentage of generated code that compiles
- **Security Score**: Vulnerability assessment
- **Code Quality**: Maintainability and style compliance
- **Overall Score**: Weighted combination of all metrics

