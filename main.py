from enum import Enum
from typing import List, Optional

class Environment(Enum):
    DEV = "devnet"
    QA = "QA"
    PROD = "prod"

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

'''
Configuration class for the DevNet Inspector agent.

Attributes:
    environment (Environment): The deployment environment (DEV/QA/PROD)
    scan_interval (int): How often to scan, in seconds (default: 60)
    modules (List[str]): List of modules to enable (default: empty list)
    log_level (LogLevel): Logging verbosity level (default: INFO)
    targets (List[tuple[str, int]]): List of target host/port tuples to monitor (default: empty list)
'''
class AgentConfig:
    environment: Environment
    scan_interval: int
    modules: List[str]
    log_level: LogLevel
    targets: List[tuple[str, int]]
    def __init__(self, 
             environment: Environment, 
             scan_interval: int = 60,  # Default scan interval
             modules: Optional[List[str]] = None,  # Could default to empty list
             log_level: LogLevel = LogLevel.INFO,  # Default log level
             targets: Optional[List[tuple[str, int]]] = None):  # Could default to empty list
        self.environment = environment
        self.scan_interval = scan_interval
        self.modules = modules or []
        self.log_level = log_level
        self.targets = targets or []

    @staticmethod
    def from_dict(config_dict: dict) -> 'AgentConfig':
        environment = Environment(config_dict['environment'])
        scan_interval = config_dict['scan_interval']
        modules = config_dict.get('modules', [])
        log_level = LogLevel(config_dict.get('log_level', LogLevel.INFO.value))
        targets = config_dict.get('targets', [])
        
        if not isinstance(targets, list):
            raise ValueError("Invalid targets format - must be a list")

        for target in targets:
            if not (isinstance(target, tuple) and len(target) == 2):
                raise ValueError("Invalid target format - must be tuple of (host, port)")
        return AgentConfig(environment, scan_interval, modules, log_level, targets)
    
    def __repr__(self):
        return f"AgentConfig(\n" \
               f"    environment={self.environment},\n" \
               f"    scan_interval={self.scan_interval},\n" \
               f"    modules={self.modules},\n" \
               f"    log_level={self.log_level},\n" \
               f"    targets={self.targets}\n" \
               f")"

def main():
    print("DevNet Inspector Starting...")
    config = AgentConfig.from_dict({
        'environment': 'devnet',
        'scan_interval': 60,
        'modules': ['network', 'system'],
        'log_level': 'DEBUG',
        'targets': [('192.168.1.1', 8080)]
    })
    print(config)

if __name__ == "__main__":
    main()

