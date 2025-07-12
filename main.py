from enum import Enum
import json,yaml
import logging
from typing import List, Optional, Tuple, Annotated
from pydantic import BaseModel, Field, field_validator, ValidationError, ConfigDict


#str is used so that when you use this enum to string , it will convert data to string and give back.
class Environment(str, Enum):
    DEV = "dev"
    QA = "QA"
    PROD = "prod"

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Target(BaseModel):
    model_config = ConfigDict(frozen=True)  # Make targets immutable
    
    host: str = Field(..., description="Target hostname or IP address")
    port: Annotated[int, Field(ge=1, le=65535)] = Field(..., description="Target port number")
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Host cannot be empty')
        return v.strip()
    
    def to_tuple(self) -> Tuple[str, int]:
        return (self.host, self.port)
    
    @classmethod
    def from_tuple(cls, target_tuple: Tuple[str, int]) -> 'Target':
        return cls(host=target_tuple[0], port=target_tuple[1])

class AgentConfig(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,  # Validate when attributes are set
        extra='forbid',  # Reject extra fields
        str_strip_whitespace=True,  # Strip whitespace from strings
        use_enum_values=True  # Use enum values in serialization
    )
    
    environment: Environment = Field(..., description="Deployment environment")
    scan_interval: Annotated[int, Field(ge=1, le=86400)] = Field(
        default=60, 
        description="Scan interval in seconds (1-86400)"
    )
    modules: List[str] = Field(
        default_factory=list, 
        description="List of enabled modules"
    )
    log_level: LogLevel = Field(
        default=LogLevel.INFO, 
        description="Logging level"
    )
    targets: List[Target] = Field(
        default_factory=list, 
        description="List of target hosts and ports"
    )
    
    @field_validator('scan_interval')
    @classmethod
    def validate_scan_interval(cls, v: int) -> int:
        if v < 1:
            raise ValueError('Scan interval must be at least 1 second')
        if v > 86400:  # 24 hours
            raise ValueError('Scan interval cannot exceed 24 hours')
        return v
    
    @field_validator('modules')
    @classmethod
    def validate_modules(cls, v: List[str]) -> List[str]:
        if not all(isinstance(module, str) and module.strip() for module in v):
            raise ValueError('All modules must be non-empty strings')
        return [module.strip() for module in v]
    
    @field_validator('targets')
    @classmethod
    def validate_targets(cls, v: List[Target]) -> List[Target]:
        if not all(isinstance(target, Target) for target in v):
            raise ValueError('All targets must be valid Target objects')
        return v
    
    def to_json(self) -> str:
        return self.model_dump_json(indent=4)
    
    def to_yaml(self) -> str:
        # Convert to dict and handle targets specially
        config_dict = self.model_dump()
        config_dict['targets'] = [[target.host, target.port] for target in self.targets]
        return yaml.dump(config_dict, default_flow_style=False)
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'AgentConfig':
        # Convert targets from tuples/lists to Target objects
        if 'targets' in config_dict:
            targets = []
            for target in config_dict['targets']:
                if isinstance(target, (tuple, list)) and len(target) == 2:
                    targets.append(Target(host=target[0], port=target[1]))
                elif isinstance(target, dict) and 'host' in target and 'port' in target:
                    targets.append(Target(**target))
                else:
                    raise ValueError(f"Invalid target format: {target}")
            config_dict['targets'] = targets
        
        return cls(**config_dict)
    
    def save(self, file_path: str) -> None:
        """Save configuration to file"""
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'w') as f:
                    f.write(self.to_json())
            elif file_path.endswith('.yaml'):
                with open(file_path, 'w') as f:
                    f.write(self.to_yaml())
            else:
                raise ValueError("Unsupported file extension - must be .json or .yaml")
        except Exception as e:
            logging.error(f"Error saving config to {file_path}: {e}")
            raise
    
    @classmethod
    def load(cls, file_path: str) -> 'AgentConfig':
        """Load configuration from file"""
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    config_dict = json.load(f)
                    return cls.from_dict(config_dict)
            elif file_path.endswith('.yaml'):
                with open(file_path, 'r') as f:
                    config_dict = yaml.safe_load(f)
                    return cls.from_dict(config_dict)
            else:
                raise ValueError("Unsupported file extension - must be .json or .yaml")
        except Exception as e:
            logging.error(f"Error loading config from {file_path}: {e}")
            raise
    
    def get_targets_as_tuples(self) -> List[Tuple[str, int]]:
        """Get targets as list of tuples for backward compatibility"""
        return [target.to_tuple() for target in self.targets]
    
    def add_target(self, host: str, port: int) -> None:
        """Add a new target"""
        self.targets.append(Target(host=host, port=port))
    
    def remove_target(self, host: str, port: int) -> None:
        """Remove a target by host and port"""
        self.targets = [t for t in self.targets if not (t.host == host and t.port == port)]
    
    def model_dump(self, **kwargs):
        """Override model_dump to handle targets properly"""
        data = super().model_dump(**kwargs)
        data['targets'] = [[target.host, target.port] for target in self.targets]
        return data

def main():
    print("DevNet Inspector Starting...")
    
    # Example with validation
    try:
        config = AgentConfig.from_dict({
            'environment': 'dev',
            'scan_interval': 60,
            'modules': ['network', 'system'],
            'log_level': 'DEBUG',
            'targets': [('192.168.1.1', 8080), ('example.com', 443)]
        })
        print("Configuration created successfully:")
        print(config)
        
        # Save to files
        config.save('config.json')
        config.save('config.yaml')
        
        # Load from file
        loaded_config = AgentConfig.load('config.yaml')
        print("\nLoaded configuration:")
        print(loaded_config)
        
        # Example of validation errors
        print("\nTesting validation errors:")
        
        # Invalid scan interval
        try:
            invalid_config = AgentConfig.from_dict({
                'environment': 'dev',
                'scan_interval': -1,  # Invalid
                'targets': [('192.168.1.1', 8080)]
            })
        except ValidationError as e:
            print(f"Validation error (scan_interval): {e}")
        
        # Invalid port
        try:
            invalid_config = AgentConfig.from_dict({
                'environment': 'dev',
                'scan_interval': 60,
                'targets': [('192.168.1.1', 99999)]  # Invalid port
            })
        except ValidationError as e:
            print(f"Validation error (port): {e}")
        
        # Invalid environment
        try:
            invalid_config = AgentConfig.from_dict({
                'environment': 'invalid_env',  # Invalid environment
                'scan_interval': 60,
                'targets': [('192.168.1.1', 8080)]
            })
        except ValidationError as e:
            print(f"Validation error (environment): {e}")
        
        # Test model methods
        print("\nTesting Pydantic v2 features:")
        print(f"Model schema: {AgentConfig.model_json_schema()}")
        print(f"Config fields: {list(AgentConfig.model_fields.keys())}")
        
    except ValidationError as e:
        print(f"Configuration validation failed: {e}")

if __name__ == "__main__":
    main()

