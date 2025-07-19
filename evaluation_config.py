import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class ScoringWeights:
    compilation: float = 0.30
    static_analysis: float = 0.25
    security: float = 0.25
    code_quality: float = 0.15
    functionality: float = 0.05


@dataclass
class ToolConfig:
    sparse_enabled: bool = True
    checkpatch_enabled: bool = True
    cppcheck_enabled: bool = True
    custom_rules_enabled: bool = True
    timeout_seconds: int = 30


@dataclass
class EvaluationConfig:
    scoring_weights: ScoringWeights
    tool_config: ToolConfig
    ollama_base_url: str = "http://10.145.25.39:11434"
    default_model: str = "qwen2.5:latest"
    output_directory: str = "evaluation_results"
    kernel_headers_path: str = "/lib/modules/$(shell uname -r)/build"
    max_build_time: int = 60
    enable_parallel_evaluation: bool = True
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'EvaluationConfig':
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            
            scoring_weights = ScoringWeights(**data.get('scoring_weights', {}))
            tool_config = ToolConfig(**data.get('tool_config', {}))
            
            config_data = {k: v for k, v in data.items() 
                          if k not in ['scoring_weights', 'tool_config']}
            
            return cls(
                scoring_weights=scoring_weights,
                tool_config=tool_config,
                **config_data
            )
        except FileNotFoundError:
            return cls.create_default()
    
    @classmethod
    def create_default(cls) -> 'EvaluationConfig':
        return cls(
            scoring_weights=ScoringWeights(),
            tool_config=ToolConfig()
        )
    
    def save_to_file(self, config_path: str):
        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)


# Default test configurations
TEST_CONFIGURATIONS = {
    "character_device_basic": {
        "name": "Basic Character Device",
        "prompt_template": """
Create a simple character device driver that supports basic read/write operations with a
{buffer_size} internal buffer. Include proper module initialization and cleanup functions.

Requirements:
- Implement file_operations structure with read, write, open, release
- Use proper kernel memory allocation (kmalloc/kfree)
- Include proper error handling
- Add MODULE_LICENSE, MODULE_AUTHOR, MODULE_DESCRIPTION

Return only the C code, no explanations.
""",
        "parameters": {"buffer_size": "1KB"},
        "expected_features": ["file_operations", "read", "write", "open", "release", "module_init", "module_exit"],
        "complexity": "basic"
    },
    
    "character_device_advanced": {
        "name": "Advanced Character Device with IOCTL",
        "prompt_template": """
Create an advanced character device driver with ioctl support, proper locking,
and a {buffer_size} circular buffer. Include device number allocation and sysfs integration.

Requirements:
- Implement full file_operations including ioctl
- Use spinlocks for thread safety
- Implement circular buffer for data storage
- Add sysfs attributes for device configuration
- Include proper device class and device creation
- Handle multiple device instances

Return only the C code, no explanations.
""",
        "parameters": {"buffer_size": "4KB"},
        "expected_features": ["unlocked_ioctl", "spinlock", "circular_buffer", "sysfs", "device_create"],
        "complexity": "advanced"
    },
    
    "platform_device_basic": {
        "name": "Basic Platform Device Driver",
        "prompt_template": """
Create a platform device driver for a memory-mapped device with basic probe/remove functions.

Requirements:
- Implement platform_driver structure
- Handle device tree bindings
- Map memory regions using ioremap
- Implement proper probe and remove functions
- Add power management support (suspend/resume)

Return only the C code, no explanations.
""",
        "parameters": {},
        "expected_features": ["platform_driver", "probe", "remove", "ioremap", "of_match"],
        "complexity": "intermediate"
    },
    
    "network_device_basic": {
        "name": "Basic Network Device Driver",
        "prompt_template": """
Create a simple network device driver that can transmit and receive packets.

Requirements:
- Implement net_device_ops structure
- Handle packet transmission and reception
- Implement basic network statistics
- Add proper network device registration
- Include interrupt handling for packet events

Return only the C code, no explanations.
""",
        "parameters": {},
        "expected_features": ["net_device_ops", "hard_start_xmit", "napi", "alloc_netdev"],
        "complexity": "intermediate"
    },
    
    "usb_device_basic": {
        "name": "Basic USB Device Driver", 
        "prompt_template": """
Create a USB device driver for a bulk transfer device.

Requirements:
- Implement usb_driver structure
- Handle probe and disconnect functions
- Manage USB endpoints for bulk transfers
- Implement read/write operations via USB
- Include proper USB error handling

Return only the C code, no explanations.
""",
        "parameters": {},
        "expected_features": ["usb_driver", "probe", "disconnect", "usb_bulk", "urb"],
        "complexity": "intermediate"
    }
}


# Kernel API compliance rules
KERNEL_API_RULES = {
    "memory_management": [
        {
            "pattern": r"kmalloc\s*\([^)]+\)",
            "requires": ["kfree", "NULL check"],
            "severity": "critical",
            "description": "kmalloc must be paired with kfree and checked for NULL"
        },
        {
            "pattern": r"vmalloc\s*\([^)]+\)", 
            "requires": ["vfree", "NULL check"],
            "severity": "critical",
            "description": "vmalloc must be paired with vfree and checked for NULL"
        }
    ],
    
    "locking": [
        {
            "pattern": r"spin_lock\s*\([^)]+\)",
            "requires": ["spin_unlock"],
            "severity": "critical", 
            "description": "spin_lock must be paired with spin_unlock"
        },
        {
            "pattern": r"mutex_lock\s*\([^)]+\)",
            "requires": ["mutex_unlock"],
            "severity": "critical",
            "description": "mutex_lock must be paired with mutex_unlock"
        }
    ],
    
    "interrupt_handling": [
        {
            "pattern": r"request_irq\s*\([^)]+\)",
            "requires": ["free_irq"],
            "severity": "major",
            "description": "request_irq must be paired with free_irq in cleanup"
        }
    ],
    
    "device_management": [
        {
            "pattern": r"device_create\s*\([^)]+\)",
            "requires": ["device_destroy"],
            "severity": "major", 
            "description": "device_create must be paired with device_destroy"
        },
        {
            "pattern": r"class_create\s*\([^)]+\)",
            "requires": ["class_destroy"],
            "severity": "major",
            "description": "class_create must be paired with class_destroy"
        }
    ]
}


# Security vulnerability patterns
SECURITY_PATTERNS = {
    "buffer_overflow": [
        {"pattern": r"strcpy\s*\(", "severity": "critical", "description": "Use strncpy instead of strcpy"},
        {"pattern": r"strcat\s*\(", "severity": "critical", "description": "Use strncat instead of strcat"}, 
        {"pattern": r"sprintf\s*\(", "severity": "major", "description": "Use snprintf instead of sprintf"},
        {"pattern": r"gets\s*\(", "severity": "critical", "description": "Never use gets() function"}
    ],
    
    "integer_overflow": [
        {"pattern": r"[\w\s]+\s*\+\s*[\w\s]+\s*<\s*[\w\s]+", "severity": "minor", "description": "Check for integer overflow"},
        {"pattern": r"[\w\s]+\s*\*\s*[\w\s]+", "severity": "minor", "description": "Multiplication may overflow"}
    ],
    
    "null_pointer": [
        {"pattern": r"\*\w+\s*(?![=!]=)", "severity": "major", "description": "Potential null pointer dereference"},
        {"pattern": r"\w+->\w+\s*(?![=!]=)", "severity": "major", "description": "Potential null pointer dereference"}
    ],
    
    "race_conditions": [
        {"pattern": r"(?<!atomic_)(?<!spin_lock)(?<!mutex_lock)\w+\s*=\s*\w+", "severity": "minor", "description": "Potential race condition"},
        {"pattern": r"if\s*\([^)]*\w+[^)]*\)\s*{[^}]*\w+\s*=", "severity": "minor", "description": "Check-then-use race condition"}
    ]
}


def load_config(config_path: str = "evaluation_config.json") -> EvaluationConfig:
    """Load configuration from file or create default"""
    return EvaluationConfig.load_from_file(config_path)


def save_default_config(config_path: str = "evaluation_config.json"):
    """Save default configuration to file"""
    config = EvaluationConfig.create_default()
    config.save_to_file(config_path)
    print(f"Default configuration saved to {config_path}")


if __name__ == "__main__":
    # Create default config file
    save_default_config()
    
    # Print test configurations
    print("\nAvailable Test Configurations:")
    for key, test in TEST_CONFIGURATIONS.items():
        print(f"  {key}: {test['name']} ({test['complexity']})")
        print(f"    Features: {', '.join(test['expected_features'])}")
        print()