"""
Smart Call Routing Service - Intelligent agent selection based on caller intent
"""
import os
import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from src.models.call import AgentConfig, db

logger = logging.getLogger(__name__)

class AgentConfigProvider(ABC):
    """
    Abstract base class for agent configuration providers.
    Defines the interface for loading, accessing, and updating agent configurations.
    """

    @abstractmethod
    def load_agent_configs(self) -> None:
        """
        Load agent configurations from the data source.
        """
        pass

    @abstractmethod
    def get_agent_config(self, agent_type: str) -> Optional[AgentConfig]:
        """
        Retrieve the configuration for a specific agent type.
        """
        pass

    @abstractmethod
    def get_all_agent_configs(self) -> Dict[str, AgentConfig]:
        """
        Retrieve all agent configurations.
        """
        pass

    @abstractmethod
    def update_agent_config(self, agent_type: str, updates: Dict[str, Any]) -> bool:
        """
        Update the configuration for a specific agent type.
        """
        pass

    @abstractmethod
    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Retrieve statistics about agent configurations.
        """
        pass


class SQLAgentConfigProvider(AgentConfigProvider):
    """
    SQL-based implementation of AgentConfigProvider.
    Handles all database interactions related to agent configurations.
    """

    def __init__(self):
        self.agent_configs: Dict[str, AgentConfig] = {}

    def load_agent_configs(self) -> None:
        """
        Load agent configurations from the database.
        """
        try:
            configs = AgentConfig.query.all()
            self.agent_configs = {config.agent_type: config for config in configs}
            logger.info(f"Loaded {len(self.agent_configs)} agent configurations")
        except Exception as e:
            logger.error(f"Error loading agent configs: {e}")
            self.agent_configs = {}

    def get_agent_config(self, agent_type: str) -> Optional[AgentConfig]:
        """
        Retrieve the configuration for a specific agent type.
        """
        if not self.agent_configs:
            self.load_agent_configs()
        return self.agent_configs.get(agent_type)

    def get_all_agent_configs(self) -> Dict[str, AgentConfig]:
        """
        Retrieve all agent configurations.
        """
        if not self.agent_configs:
            self.load_agent_configs()
        return self.agent_configs

    def update_agent_config(self, agent_type: str, updates: Dict[str, Any]) -> bool:
        """
        Update the configuration for a specific agent type.
        """
        try:
            config = AgentConfig.query.filter_by(agent_type=agent_type).first()
            if not config:
                return False

            allowed_fields = [
                'name', 'description', 'system_prompt', 'max_turns',
                'timeout_seconds', 'voice_provider', 'voice_model',
                'priority', 'sms_template'
            ]

            for field, value in updates.items():
                if field in allowed_fields and hasattr(config, field):
                    setattr(config, field, value)
                elif field == 'keywords':
                    config.set_keywords(value)

            db.session.commit()
            self.load_agent_configs()
            logger.info(f"Updated agent configuration for {agent_type}")
            return True

        except Exception as e:
            logger.error(f"Error updating agent config: {e}")
            db.session.rollback()
            return False

    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Retrieve statistics about agent configurations.
        """
        if not self.agent_configs:
            self.load_agent_configs()
        return {
            'total_agents': len(self.agent_configs),
            'available_agents': list(self.agent_configs.keys()),
            'agent_details': {
                agent_type: {
                    'name': config.name,
                    'keywords_count': len(config.get_keywords()),
                    'priority': config.priority
                }
                for agent_type, config in self.agent_configs.items()
            }
        }


class CallRouter:
    """
    Intelligent call routing system that analyzes caller intent
    and routes to appropriate specialized agents.
    """

    def __init__(self, agent_config_provider: AgentConfigProvider = None):
        # Use the provided config provider or default to SQLAgentConfigProvider
        self.agent_config_provider = agent_config_provider or SQLAgentConfigProvider()
        # Ensure configs are loaded
        self.agent_config_provider.load_agent_configs()

    def analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze user input to determine best agent match

        Args:
            user_input: Caller's spoken input

        Returns:
            Routing decision with agent type and confidence
        """
        user_input_lower = user_input.lower().strip()

        # TODO: Pluginize the intent analyzer and keyword matcher to decouple rules/AI intent logic
        # This is where a plugin registry or MCP hook could be invoked to analyze intent

        # Score each agent based on keyword matches
        agent_scores = []

        agent_configs = self.agent_config_provider.get_all_agent_configs()

        for agent_type, config in agent_configs.items():
            score = 0
            matched_keywords = []
            keywords = config.get_keywords()

            # Check for keyword matches
            for keyword in keywords:
                if keyword.lower() in user_input_lower:
                    # Weight by keyword specificity and agent priority
                    keyword_weight = len(keyword) * config.priority
                    score += keyword_weight
                    matched_keywords.append(keyword)

            # Bonus for multiple keyword matches
            if len(matched_keywords) > 1:
                score += len(matched_keywords) * 2

            # Bonus for exact phrase matches
            for keyword in keywords:
                if keyword.lower() == user_input_lower:
                    score += 50  # High bonus for exact match

            if score > 0:
                agent_scores.append({
                    'agent_type': agent_type,
                    'config': config,
                    'score': score,
                    'matched_keywords': matched_keywords
                })

        # Sort by score (highest first)
        agent_scores.sort(key=lambda x: x['score'], reverse=True)

        if agent_scores:
            best_match = agent_scores[0]
            # Normalize confidence to 0-1 scale
            max_possible_score = 100
            confidence = min(best_match['score'] / max_possible_score, 1.0)

            return {
                'agent_type': best_match['agent_type'],
                'confidence': confidence,
                'matched_keywords': best_match['matched_keywords'],
                'config': best_match['config']
            }
        else:
            # Default to general agent
            general_config = agent_configs.get('general')
            return {
                'agent_type': 'general',
                'confidence': 0.1,
                'matched_keywords': [],
                'config': general_config
            }

    def route_call(self, call_sid: str, user_input: str, phone_number: str) -> Dict[str, Any]:
        """
        Route a call to the appropriate agent

        Args:
            call_sid: Twilio call SID
            user_input: Caller's initial input
            phone_number: Caller's phone number

        Returns:
            Complete routing decision
        """
        # Analyze intent
        routing_analysis = self.analyze_intent(user_input)

        # Get agent configuration
        agent_config = routing_analysis['config']

        if not agent_config:
            # Fallback to general agent
            agent_config = self.agent_config_provider.get_agent_config('general')
            if not agent_config:
                # Create minimal fallback
                return {
                    'call_sid': call_sid,
                    'phone_number': phone_number,
                    'agent_type': 'general',
                    'system_prompt': 'You are a helpful customer service representative for A Killion Voice. Be friendly, professional, and concise.',
                    'confidence': 0.1,
                    'matched_keywords': [],
                    'voice_model': 'alloy',
                    'max_turns': 20,
                    'sms_template': 'Thanks for calling A Killion Voice! We discussed your inquiry and provided assistance.'
                }

        # Create routing decision
        routing_decision = {
            'call_sid': call_sid,
            'phone_number': phone_number,
            'agent_type': routing_analysis['agent_type'],
            'system_prompt': agent_config.system_prompt,
            'confidence': routing_analysis['confidence'],
            'matched_keywords': routing_analysis['matched_keywords'],
            'voice_model': getattr(agent_config, 'voice_model', 'alloy'),
            'voice_provider': getattr(agent_config, 'voice_provider', 'openai'),
            'max_turns': getattr(agent_config, 'max_turns', 20),
            'timeout_seconds': getattr(agent_config, 'timeout_seconds', 30),
            'sms_template': agent_config.sms_template,
            'initial_input': user_input
        }

        logger.info(f"Routed call {call_sid} to {routing_analysis['agent_type']} agent (confidence: {routing_analysis['confidence']:.2f})")

        return routing_decision

    def get_agent_info(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific agent type

        Args:
            agent_type: Agent type to query

        Returns:
            Agent information or None
        """
        config = self.agent_config_provider.get_agent_config(agent_type)
        return config.to_dict() if config else None

    def get_all_agents(self) -> List[Dict[str, Any]]:
        """
        Get information about all available agents

        Returns:
            List of agent configurations
        """
        agent_configs = self.agent_config_provider.get_all_agent_configs()

        return [
            {
                'agent_type': config.agent_type,
                'name': config.name,
                'description': config.description,
                'keywords': config.get_keywords(),
                'priority': config.priority,
                'system_prompt': config.system_prompt[:100] + '...' if len(config.system_prompt) > 100 else config.system_prompt
            }
            for config in agent_configs.values()
        ]

    def update_agent_config(self, agent_type: str, updates: Dict[str, Any]) -> bool:
        """
        Update agent configuration

        Args:
            agent_type: Agent type to update
            updates: Dictionary of updates to apply

        Returns:
            True if successful
        """
        return self.agent_config_provider.update_agent_config(agent_type, updates)

    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Get routing statistics

        Returns:
            Statistics about call routing
        """
        return self.agent_config_provider.get_routing_stats()


# Global router instance
call_router = CallRouter()
