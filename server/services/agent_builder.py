"""
Agent Builder Service
Handles agent creation, customization, and prompt compilation
"""
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from models.enhanced_models import (
    EnhancedAgentConfig, AgentTemplate, AgentInstruction,
    AgentGoal, AgentDomain, ConversationGoal, DomainKnowledge
)
import json
import logging

logger = logging.getLogger(__name__)

class AgentBuilder:
    """Service for building and customizing agents"""
    
    def create_agent(self, db: Session, name: str, template_id: Optional[int] = None,
                    description: Optional[str] = None, customizations: Dict[str, Any] = None) -> EnhancedAgentConfig:
        """Create a new agent from template or scratch"""
        
        # Start with template if provided
        if template_id:
            template = db.query(AgentTemplate).filter_by(id=template_id).first()
            if not template:
                raise ValueError(f"Template {template_id} not found")
                
            agent = EnhancedAgentConfig(
                name=name,
                description=description or template.description,
                template_id=template_id,
                system_prompt=template.base_prompt,
                voice_settings=template.voice_config or {},
                personality_traits=customizations.get('personality_traits', ['professional', 'helpful']),
                conversation_style=customizations.get('conversation_style', 'balanced')
            )
        else:
            # Create from scratch
            agent = EnhancedAgentConfig(
                name=name,
                description=description,
                personality_traits=customizations.get('personality_traits', ['professional', 'helpful']),
                conversation_style=customizations.get('conversation_style', 'balanced'),
                voice_settings=customizations.get('voice_settings', {})
            )
        
        # Apply customizations
        if customizations:
            if 'greeting_message' in customizations:
                agent.greeting_message = customizations['greeting_message']
            if 'max_turns' in customizations:
                agent.max_conversation_turns = customizations['max_turns']
            if 'keywords' in customizations:
                agent.keywords = customizations['keywords']
            if 'priority' in customizations:
                agent.priority = customizations['priority']
                
        db.add(agent)
        db.flush()  # Get the ID without committing
        
        return agent
    
    def compile_system_prompt(self, db: Session, agent_id: int) -> str:
        """Compile the complete system prompt for an agent"""
        
        agent = db.query(EnhancedAgentConfig).filter_by(id=agent_id).first()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Start with base prompt
        if agent.template:
            prompt_parts = [agent.template.base_prompt]
        else:
            prompt_parts = ["You are a professional voice agent."]
        
        # Add personality traits
        if agent.personality_traits:
            traits_text = f"\nYour personality traits: {', '.join(agent.personality_traits)}."
            prompt_parts.append(traits_text)
        
        # Add conversation style
        style_descriptions = {
            'formal': 'Use formal, professional language.',
            'casual': 'Use casual, friendly language.',
            'balanced': 'Use a balanced mix of professional and friendly language.'
        }
        if agent.conversation_style in style_descriptions:
            prompt_parts.append(f"\nCommunication style: {style_descriptions[agent.conversation_style]}")
        
        # Add goals
        goals = self._get_agent_goals(db, agent_id)
        if goals:
            prompt_parts.append("\n## Your Goals:")
            for i, goal in enumerate(goals, 1):
                prompt_parts.append(f"{i}. {goal['name']}: {goal['description']}")
                if goal['required']:
                    prompt_parts.append(f"   (REQUIRED - Must be completed)")
                if goal['success_criteria']:
                    prompt_parts.append(f"   Success criteria: {json.dumps(goal['success_criteria'])}")
        
        # Add instructions
        instructions = self._get_agent_instructions(db, agent_id)
        if instructions['dos']:
            prompt_parts.append("\n## Things you SHOULD do:")
            for instruction in instructions['dos']:
                prompt_parts.append(f"- {instruction['instruction']}")
                
        if instructions['donts']:
            prompt_parts.append("\n## Things you should NOT do:")
            for instruction in instructions['donts']:
                prompt_parts.append(f"- {instruction['instruction']}")
        
        # Add domain knowledge context
        domains = self._get_agent_domains(db, agent_id)
        if domains:
            prompt_parts.append("\n## Knowledge Base Access:")
            prompt_parts.append("You have access to information about:")
            for domain in domains:
                prompt_parts.append(f"- {domain['name']}")
            prompt_parts.append("Use this knowledge to provide accurate, detailed responses.")
        
        # Add conversation guidelines
        prompt_parts.append("\n## Conversation Guidelines:")
        prompt_parts.append(f"- Maximum conversation turns: {agent.max_conversation_turns}")
        prompt_parts.append(f"- Target response time: {agent.response_time_ms}ms")
        prompt_parts.append("- Keep responses concise and natural for voice conversation")
        prompt_parts.append("- Listen actively and acknowledge what the caller says")
        prompt_parts.append("- If you don't understand something, politely ask for clarification")
        
        # Compile final prompt
        final_prompt = "\n".join(prompt_parts)
        
        # Update the agent's system prompt
        agent.system_prompt = final_prompt
        db.commit()
        
        return final_prompt
    
    def get_compiled_prompt(self, db: Session, agent_id: int) -> str:
        """Get the compiled system prompt without updating"""
        agent = db.query(EnhancedAgentConfig).filter_by(id=agent_id).first()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
            
        if not agent.system_prompt:
            return self.compile_system_prompt(db, agent_id)
            
        return agent.system_prompt
    
    def validate_agent_config(self, db: Session, agent_id: int) -> Dict[str, Any]:
        """Validate that an agent has all required components"""
        
        agent = db.query(EnhancedAgentConfig).filter_by(id=agent_id).first()
        if not agent:
            return {'valid': False, 'errors': ['Agent not found']}
        
        errors = []
        warnings = []
        
        # Check required fields
        if not agent.name:
            errors.append('Agent name is required')
        if not agent.system_prompt:
            errors.append('System prompt is missing')
            
        # Check goals
        goals = self._get_agent_goals(db, agent_id)
        required_goals = [g for g in goals if g['required']]
        if not goals:
            warnings.append('No goals assigned to agent')
        elif not required_goals:
            warnings.append('No required goals set')
            
        # Check instructions
        instructions = self._get_agent_instructions(db, agent_id)
        if not instructions['dos'] and not instructions['donts']:
            warnings.append('No instructions defined')
            
        # Check voice profile
        if not agent.voice_profile:
            warnings.append('No voice profile configured')
        elif agent.voice_profile.training_status != 'ready':
            warnings.append(f'Voice profile training status: {agent.voice_profile.training_status}')
            
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'ready_for_production': len(errors) == 0 and not agent.test_mode
        }
    
    def _get_agent_goals(self, db: Session, agent_id: int) -> List[Dict[str, Any]]:
        """Get all active goals for an agent"""
        
        agent_goals = db.query(AgentGoal).filter_by(
            agent_id=agent_id,
            active=True
        ).order_by(AgentGoal.priority.desc()).all()
        
        goals = []
        for ag in agent_goals:
            goal = ag.goal
            goals.append({
                'id': goal.id,
                'name': goal.name,
                'description': goal.description,
                'type': goal.goal_type,
                'required': ag.required,
                'priority': ag.priority,
                'success_criteria': goal.success_criteria,
                'required_data': goal.required_data,
                'custom_criteria': ag.custom_criteria
            })
            
        return goals
    
    def _get_agent_instructions(self, db: Session, agent_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get all active instructions for an agent"""
        
        instructions = db.query(AgentInstruction).filter_by(
            agent_id=agent_id,
            active=True
        ).order_by(AgentInstruction.priority.desc()).all()
        
        dos = []
        donts = []
        
        for inst in instructions:
            inst_data = {
                'id': inst.id,
                'instruction': inst.instruction,
                'category': inst.category,
                'priority': inst.priority,
                'context_trigger': inst.context_trigger
            }
            
            if inst.instruction_type == 'do':
                dos.append(inst_data)
            else:
                donts.append(inst_data)
                
        return {'dos': dos, 'donts': donts}
    
    def _get_agent_domains(self, db: Session, agent_id: int) -> List[Dict[str, Any]]:
        """Get all domains assigned to an agent"""
        
        # Query agent domains with joined domain knowledge
        agent_domains = db.query(AgentDomain, DomainKnowledge).join(
            DomainKnowledge, AgentDomain.domain_id == DomainKnowledge.id
        ).filter(
            AgentDomain.agent_id == agent_id,
            DomainKnowledge.active == True
        ).order_by(AgentDomain.relevance_score.desc()).all()
        
        # Collect unique domain names
        domains = []
        seen_domains = set()
        
        for ad, dk in agent_domains:
            if dk.domain_name not in seen_domains:
                seen_domains.add(dk.domain_name)
                domains.append({
                    'id': dk.id,
                    'name': dk.domain_name,
                    'relevance_score': ad.relevance_score
                })
            
        return domains
    
    def clone_agent(self, db: Session, source_agent_id: int, new_name: str) -> EnhancedAgentConfig:
        """Clone an existing agent with a new name"""
        
        source = db.query(EnhancedAgentConfig).filter_by(id=source_agent_id).first()
        if not source:
            raise ValueError(f"Source agent {source_agent_id} not found")
        
        # Create new agent with same properties
        new_agent = EnhancedAgentConfig(
            name=new_name,
            description=f"Clone of {source.name}",
            template_id=source.template_id,
            system_prompt=source.system_prompt,
            greeting_message=source.greeting_message,
            voice_settings=source.voice_settings,
            personality_traits=source.personality_traits,
            conversation_style=source.conversation_style,
            max_conversation_turns=source.max_conversation_turns,
            response_time_ms=source.response_time_ms,
            keywords=source.keywords,
            priority=source.priority,
            routing_confidence_threshold=source.routing_confidence_threshold,
            custom_settings=source.custom_settings,
            test_mode=True  # Start clones in test mode
        )
        
        db.add(new_agent)
        db.flush()
        
        # Clone goals
        for ag in source.goals:
            new_goal = AgentGoal(
                agent_id=new_agent.id,
                goal_id=ag.goal_id,
                priority=ag.priority,
                required=ag.required,
                active=ag.active,
                custom_criteria=ag.custom_criteria
            )
            db.add(new_goal)
        
        # Clone instructions
        for inst in source.instructions:
            new_inst = AgentInstruction(
                agent_id=new_agent.id,
                instruction_type=inst.instruction_type,
                category=inst.category,
                instruction=inst.instruction,
                priority=inst.priority,
                active=inst.active,
                context_trigger=inst.context_trigger
            )
            db.add(new_inst)
        
        # Clone domains
        for ad in source.domains:
            new_domain = AgentDomain(
                agent_id=new_agent.id,
                domain_id=ad.domain_id,
                relevance_score=ad.relevance_score
            )
            db.add(new_domain)
        
        db.commit()
        
        return new_agent