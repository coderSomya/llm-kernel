# Make executable
chmod +x run.sh debug.sh

# Create results directory
mkdir results

# Run evaluation (will build automatically)
./run.sh --model qwen2.5:latest --test simple_char_driver

# Compare models
./run.sh --compare qwen2.5:latest codellama:latest

# Debug if needed
./debug.sh
