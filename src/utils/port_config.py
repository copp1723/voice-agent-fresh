"""
Port Configuration Manager - Standardizes port handling across all startup methods
"""
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class PortConfigManager:
    """
    Manages port configuration with proper precedence and validation
    """
    
    def __init__(self):
        self.default_ports = {
            'backend': 5000,
            'frontend': 3000,
            'production': 10000,
            'development': 5000
        }
        
        self.detected_port = None
        self.port_source = None
        
        # Detect port configuration
        self._detect_port_configuration()
    
    def _detect_port_configuration(self):
        """Detect port configuration from various sources with proper precedence"""
        
        # Order of precedence:
        # 1. Command line argument (PORT env var set by process)
        # 2. Environment variable from .env file
        # 3. Runtime environment detection
        # 4. Default based on Flask environment
        
        # 1. Check for PORT environment variable (highest priority)
        port_env = os.getenv('PORT')
        if port_env:
            try:
                self.detected_port = int(port_env)
                self.port_source = 'environment_variable'
                logger.info(f"Port detected from environment: {self.detected_port}")
                return
            except ValueError:
                logger.warning(f"Invalid PORT environment variable: {port_env}")
        
        # 2. Check Flask environment for default
        flask_env = os.getenv('FLASK_ENV', 'development')
        
        if flask_env == 'production':
            self.detected_port = self.default_ports['production']
            self.port_source = 'production_default'
        else:
            self.detected_port = self.default_ports['development']
            self.port_source = 'development_default'
        
        logger.info(f"Port detected from {self.port_source}: {self.detected_port}")
    
    def get_port(self, context: Optional[str] = None) -> int:
        """
        Get the appropriate port for the given context
        
        Args:
            context: Context hint ('backend', 'frontend', 'production', 'development')
            
        Returns:
            Port number
        """
        
        # If context is provided, use it to override
        if context and context in self.default_ports:
            context_port = self.default_ports[context]
            logger.info(f"Using context-specific port for '{context}': {context_port}")
            return context_port
        
        # Otherwise, use detected port
        return self.detected_port
    
    def get_port_config(self) -> Dict[str, Any]:
        """Get comprehensive port configuration"""
        return {
            'detected_port': self.detected_port,
            'port_source': self.port_source,
            'flask_env': os.getenv('FLASK_ENV', 'development'),
            'default_ports': self.default_ports,
            'recommendations': self._get_port_recommendations()
        }
    
    def _get_port_recommendations(self) -> Dict[str, Any]:
        """Get port configuration recommendations"""
        flask_env = os.getenv('FLASK_ENV', 'development')
        
        recommendations = {
            'current_setup': 'good',
            'issues': [],
            'suggestions': []
        }
        
        # Check for port conflicts
        if self.detected_port == self.default_ports['frontend']:
            recommendations['issues'].append(
                f"Backend port ({self.detected_port}) conflicts with default frontend port"
            )
            recommendations['suggestions'].append(
                "Consider using port 5000 for backend and 3000 for frontend"
            )
            recommendations['current_setup'] = 'needs_attention'
        
        # Check environment alignment
        if flask_env == 'production' and self.detected_port != self.default_ports['production']:
            recommendations['issues'].append(
                f"Production environment but using non-production port ({self.detected_port})"
            )
            recommendations['suggestions'].append(
                f"Consider using port {self.default_ports['production']} for production"
            )
        
        return recommendations
    
    def standardize_env_file(self, env_file_path: str = '.env') -> bool:
        """
        Standardize port configuration in .env file
        
        Args:
            env_file_path: Path to .env file
            
        Returns:
            Success boolean
        """
        try:
            if not os.path.exists(env_file_path):
                logger.warning(f"Environment file not found: {env_file_path}")
                return False
            
            # Read current .env file
            with open(env_file_path, 'r') as f:
                lines = f.readlines()
            
            # Find and update PORT line
            port_line_found = False
            flask_env = os.getenv('FLASK_ENV', 'development')
            
            # Determine recommended port
            if flask_env == 'production':
                recommended_port = self.default_ports['production']
            else:
                recommended_port = self.default_ports['development']
            
            # Update or add PORT line
            for i, line in enumerate(lines):
                if line.startswith('PORT='):
                    lines[i] = f'PORT={recommended_port}\n'
                    port_line_found = True
                    break
            
            # Add PORT line if not found
            if not port_line_found:
                lines.append(f'\n# Port Configuration\nPORT={recommended_port}\n')
            
            # Write back to file
            with open(env_file_path, 'w') as f:
                f.writelines(lines)
            
            logger.info(f"Standardized port configuration in {env_file_path}: {recommended_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to standardize .env file: {e}")
            return False
    
    def create_port_config_summary(self) -> str:
        """Create a summary of port configuration"""
        config = self.get_port_config()
        
        summary = f"""
# Port Configuration Summary

## Current Configuration
- Detected Port: {config['detected_port']}
- Port Source: {config['port_source']}
- Flask Environment: {config['flask_env']}

## Default Ports
- Development: {config['default_ports']['development']}
- Production: {config['default_ports']['production']}
- Frontend: {config['default_ports']['frontend']}

## Recommendations
- Setup Status: {config['recommendations']['current_setup']}
"""
        
        if config['recommendations']['issues']:
            summary += "\n### Issues Found:\n"
            for issue in config['recommendations']['issues']:
                summary += f"- {issue}\n"
        
        if config['recommendations']['suggestions']:
            summary += "\n### Suggestions:\n"
            for suggestion in config['recommendations']['suggestions']:
                summary += f"- {suggestion}\n"
        
        summary += """
## Standard Configuration

### Development
```bash
# .env file
FLASK_ENV=development
PORT=5000
```

### Production
```bash
# .env file  
FLASK_ENV=production
PORT=10000
```

### Frontend (separate)
```bash
# frontend/.env
VITE_API_BASE_URL=http://localhost:5000/api
```
"""
        
        return summary
    
    def validate_port_configuration(self) -> Dict[str, Any]:
        """Validate current port configuration"""
        config = self.get_port_config()
        
        validation = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'recommendations': []
        }
        
        # Check if port is in valid range
        if not (1024 <= self.detected_port <= 65535):
            validation['valid'] = False
            validation['errors'].append(f"Port {self.detected_port} is outside valid range (1024-65535)")
        
        # Check for common port conflicts
        common_ports = {
            80: 'HTTP',
            443: 'HTTPS',
            3000: 'React Development Server',
            3306: 'MySQL',
            5432: 'PostgreSQL',
            6379: 'Redis'
        }
        
        if self.detected_port in common_ports:
            validation['warnings'].append(
                f"Port {self.detected_port} is commonly used by {common_ports[self.detected_port]}"
            )
        
        # Check environment alignment
        flask_env = os.getenv('FLASK_ENV', 'development')
        if flask_env == 'production' and self.detected_port < 10000:
            validation['recommendations'].append(
                "Consider using higher port number (10000+) for production"
            )
        
        return validation

# Global instance
port_manager = PortConfigManager()

def get_standardized_port(context: Optional[str] = None) -> int:
    """
    Get standardized port for the application
    
    Args:
        context: Optional context hint
        
    Returns:
        Port number
    """
    return port_manager.get_port(context)

def get_port_config() -> Dict[str, Any]:
    """Get comprehensive port configuration"""
    return port_manager.get_port_config()

def standardize_ports() -> bool:
    """Standardize port configuration across the project"""
    return port_manager.standardize_env_file()
