"""
Agent Management API Routes
Provides CRUD operations for flexible agent configuration
"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from database import get_db
from models.enhanced_models import (
    EnhancedAgentConfig, AgentTemplate, ConversationGoal,
    AgentInstruction, DomainKnowledge, AgentGoal, AgentDomain,
    VoiceProfile
)
from services.agent_builder import AgentBuilder
from auth import require_auth
import logging

logger = logging.getLogger(__name__)
agent_bp = Blueprint('agent_management', __name__, url_prefix='/api/agents')
agent_builder = AgentBuilder()

@agent_bp.route('', methods=['GET'])
@require_auth
def list_agents():
    """List all agents with optional filtering"""
    db: Session = next(get_db())
    try:
        # Get query parameters
        active_only = request.args.get('active', 'true').lower() == 'true'
        include_test = request.args.get('include_test', 'false').lower() == 'true'
        
        # Build query
        query = db.query(EnhancedAgentConfig)
        if active_only:
            query = query.filter(EnhancedAgentConfig.active == True)
        if not include_test:
            query = query.filter(EnhancedAgentConfig.test_mode == False)
            
        agents = query.all()
        
        # Format response
        return jsonify({
            'agents': [{
                'id': agent.id,
                'name': agent.name,
                'description': agent.description,
                'template_name': agent.template.name if agent.template else None,
                'active': agent.active,
                'test_mode': agent.test_mode,
                'goal_count': len(agent.goals),
                'instruction_count': len(agent.instructions),
                'created_at': agent.created_at.isoformat()
            } for agent in agents]
        })
    finally:
        db.close()

@agent_bp.route('/<int:agent_id>', methods=['GET'])
@require_auth
def get_agent(agent_id):
    """Get detailed agent configuration"""
    db: Session = next(get_db())
    try:
        agent = db.query(EnhancedAgentConfig).filter_by(id=agent_id).first()
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
            
        return jsonify({
            'id': agent.id,
            'name': agent.name,
            'description': agent.description,
            'template': {
                'id': agent.template.id,
                'name': agent.template.name
            } if agent.template else None,
            'system_prompt': agent.system_prompt,
            'greeting_message': agent.greeting_message,
            'voice_settings': agent.voice_settings,
            'personality_traits': agent.personality_traits,
            'conversation_style': agent.conversation_style,
            'goals': [{
                'id': ag.goal.id,
                'name': ag.goal.name,
                'priority': ag.priority,
                'required': ag.required
            } for ag in agent.goals if ag.active],
            'instructions': {
                'dos': [{'id': i.id, 'instruction': i.instruction, 'category': i.category}
                       for i in agent.instructions if i.instruction_type == 'do' and i.active],
                'donts': [{'id': i.id, 'instruction': i.instruction, 'category': i.category}
                         for i in agent.instructions if i.instruction_type == 'dont' and i.active]
            },
            'domains': [{
                'id': ad.domain.id,
                'name': ad.domain.domain_name,
                'relevance_score': ad.relevance_score
            } for ad in agent.domains],
            'voice_profile': {
                'provider': agent.voice_profile.voice_provider,
                'base_emotion': agent.voice_profile.base_emotion,
                'training_status': agent.voice_profile.training_status
            } if agent.voice_profile else None,
            'routing': {
                'keywords': agent.keywords,
                'priority': agent.priority,
                'confidence_threshold': agent.routing_confidence_threshold
            },
            'settings': {
                'max_turns': agent.max_conversation_turns,
                'response_time_ms': agent.response_time_ms,
                'custom': agent.custom_settings
            }
        })
    finally:
        db.close()

@agent_bp.route('', methods=['POST'])
@require_auth
def create_agent():
    """Create a new agent from template or scratch"""
    db: Session = next(get_db())
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Agent name is required'}), 400
            
        # Check if agent name already exists
        existing = db.query(EnhancedAgentConfig).filter_by(name=data['name']).first()
        if existing:
            return jsonify({'error': 'Agent name already exists'}), 400
            
        # Create agent using builder service
        agent = agent_builder.create_agent(
            db=db,
            name=data['name'],
            template_id=data.get('template_id'),
            description=data.get('description'),
            customizations=data.get('customizations', {})
        )
        
        # Add goals if provided
        if data.get('goals'):
            for goal_data in data['goals']:
                goal = db.query(ConversationGoal).filter_by(id=goal_data['id']).first()
                if goal:
                    agent_goal = AgentGoal(
                        agent_id=agent.id,
                        goal_id=goal.id,
                        priority=goal_data.get('priority', 0),
                        required=goal_data.get('required', False)
                    )
                    db.add(agent_goal)
        
        # Add instructions if provided
        if data.get('instructions'):
            for inst_type in ['dos', 'donts']:
                for instruction in data['instructions'].get(inst_type, []):
                    agent_inst = AgentInstruction(
                        agent_id=agent.id,
                        instruction_type='do' if inst_type == 'dos' else 'dont',
                        instruction=instruction['text'],
                        category=instruction.get('category'),
                        priority=instruction.get('priority', 0)
                    )
                    db.add(agent_inst)
        
        # Add domains if provided
        if data.get('domains'):
            for domain_id in data['domains']:
                domain = db.query(DomainKnowledge).filter_by(id=domain_id).first()
                if domain:
                    agent_domain = AgentDomain(
                        agent_id=agent.id,
                        domain_id=domain_id
                    )
                    db.add(agent_domain)
        
        # Create voice profile
        voice_data = data.get('voice', {})
        voice_profile = VoiceProfile(
            agent_id=agent.id,
            voice_provider=voice_data.get('provider', 'chatterbox'),
            base_emotion=voice_data.get('base_emotion', 'friendly'),
            emotion_range=voice_data.get('emotion_range', {})
        )
        db.add(voice_profile)
        
        db.commit()
        
        # Compile the system prompt
        agent_builder.compile_system_prompt(db, agent.id)
        
        return jsonify({
            'success': True,
            'agent_id': agent.id,
            'message': f'Agent "{agent.name}" created successfully'
        }), 201
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating agent: {str(e)}")
        return jsonify({'error': 'Failed to create agent'}), 500
    finally:
        db.close()

@agent_bp.route('/<int:agent_id>', methods=['PUT'])
@require_auth
def update_agent(agent_id):
    """Update agent configuration"""
    db: Session = next(get_db())
    try:
        agent = db.query(EnhancedAgentConfig).filter_by(id=agent_id).first()
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
            
        data = request.json
        
        # Update basic fields
        if 'name' in data:
            agent.name = data['name']
        if 'description' in data:
            agent.description = data['description']
        if 'active' in data:
            agent.active = data['active']
        if 'test_mode' in data:
            agent.test_mode = data['test_mode']
            
        # Update settings
        if 'settings' in data:
            settings = data['settings']
            if 'max_turns' in settings:
                agent.max_conversation_turns = settings['max_turns']
            if 'response_time_ms' in settings:
                agent.response_time_ms = settings['response_time_ms']
            if 'custom' in settings:
                agent.custom_settings = settings['custom']
                
        # Update voice settings
        if 'voice_settings' in data:
            agent.voice_settings = data['voice_settings']
            
        # Update personality
        if 'personality_traits' in data:
            agent.personality_traits = data['personality_traits']
        if 'conversation_style' in data:
            agent.conversation_style = data['conversation_style']
            
        db.commit()
        
        # Recompile system prompt if needed
        if any(key in data for key in ['personality_traits', 'conversation_style']):
            agent_builder.compile_system_prompt(db, agent.id)
            
        return jsonify({
            'success': True,
            'message': f'Agent "{agent.name}" updated successfully'
        })
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating agent: {str(e)}")
        return jsonify({'error': 'Failed to update agent'}), 500
    finally:
        db.close()

@agent_bp.route('/<int:agent_id>', methods=['DELETE'])
@require_auth
def delete_agent(agent_id):
    """Delete an agent"""
    db: Session = next(get_db())
    try:
        agent = db.query(EnhancedAgentConfig).filter_by(id=agent_id).first()
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
            
        agent_name = agent.name
        db.delete(agent)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': f'Agent "{agent_name}" deleted successfully'
        })
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting agent: {str(e)}")
        return jsonify({'error': 'Failed to delete agent'}), 500
    finally:
        db.close()

# Goal Management Endpoints
@agent_bp.route('/<int:agent_id>/goals', methods=['POST'])
@require_auth
def add_agent_goal(agent_id):
    """Add a goal to an agent"""
    db: Session = next(get_db())
    try:
        agent = db.query(EnhancedAgentConfig).filter_by(id=agent_id).first()
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
            
        data = request.json
        goal = db.query(ConversationGoal).filter_by(id=data['goal_id']).first()
        if not goal:
            return jsonify({'error': 'Goal not found'}), 404
            
        # Check if goal already assigned
        existing = db.query(AgentGoal).filter_by(
            agent_id=agent_id,
            goal_id=data['goal_id']
        ).first()
        
        if existing:
            return jsonify({'error': 'Goal already assigned to agent'}), 400
            
        agent_goal = AgentGoal(
            agent_id=agent_id,
            goal_id=data['goal_id'],
            priority=data.get('priority', 0),
            required=data.get('required', False),
            custom_criteria=data.get('custom_criteria')
        )
        db.add(agent_goal)
        db.commit()
        
        # Recompile system prompt
        agent_builder.compile_system_prompt(db, agent_id)
        
        return jsonify({
            'success': True,
            'message': f'Goal "{goal.name}" added to agent'
        })
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding goal: {str(e)}")
        return jsonify({'error': 'Failed to add goal'}), 500
    finally:
        db.close()

@agent_bp.route('/<int:agent_id>/goals/<int:goal_id>', methods=['DELETE'])
@require_auth
def remove_agent_goal(agent_id, goal_id):
    """Remove a goal from an agent"""
    db: Session = next(get_db())
    try:
        agent_goal = db.query(AgentGoal).filter_by(
            agent_id=agent_id,
            goal_id=goal_id
        ).first()
        
        if not agent_goal:
            return jsonify({'error': 'Goal assignment not found'}), 404
            
        db.delete(agent_goal)
        db.commit()
        
        # Recompile system prompt
        agent_builder.compile_system_prompt(db, agent_id)
        
        return jsonify({
            'success': True,
            'message': 'Goal removed from agent'
        })
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing goal: {str(e)}")
        return jsonify({'error': 'Failed to remove goal'}), 500
    finally:
        db.close()

# Instruction Management Endpoints
@agent_bp.route('/<int:agent_id>/instructions', methods=['POST'])
@require_auth
def add_agent_instruction(agent_id):
    """Add an instruction to an agent"""
    db: Session = next(get_db())
    try:
        agent = db.query(EnhancedAgentConfig).filter_by(id=agent_id).first()
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
            
        data = request.json
        
        instruction = AgentInstruction(
            agent_id=agent_id,
            instruction_type=data['type'],  # 'do' or 'dont'
            instruction=data['instruction'],
            category=data.get('category'),
            priority=data.get('priority', 0),
            context_trigger=data.get('context_trigger')
        )
        db.add(instruction)
        db.commit()
        
        # Recompile system prompt
        agent_builder.compile_system_prompt(db, agent_id)
        
        return jsonify({
            'success': True,
            'instruction_id': instruction.id,
            'message': 'Instruction added successfully'
        })
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding instruction: {str(e)}")
        return jsonify({'error': 'Failed to add instruction'}), 500
    finally:
        db.close()

# Template Management Endpoints
@agent_bp.route('/templates', methods=['GET'])
@require_auth
def list_templates():
    """List available agent templates"""
    db: Session = next(get_db())
    try:
        templates = db.query(AgentTemplate).all()
        
        return jsonify({
            'templates': [{
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'industry': template.industry,
                'use_case': template.use_case,
                'created_at': template.created_at.isoformat()
            } for template in templates]
        })
    finally:
        db.close()

# Test Agent Endpoint
@agent_bp.route('/<int:agent_id>/test', methods=['POST'])
@require_auth
def test_agent(agent_id):
    """Test an agent with a sample conversation"""
    db: Session = next(get_db())
    try:
        agent = db.query(EnhancedAgentConfig).filter_by(id=agent_id).first()
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
            
        data = request.json
        test_input = data.get('input', 'Hello, I need help')
        
        # Get compiled prompt
        system_prompt = agent_builder.get_compiled_prompt(db, agent_id)
        
        # Here you would normally call your LLM service
        # For now, return a mock response
        return jsonify({
            'agent_name': agent.name,
            'system_prompt_preview': system_prompt[:500] + '...' if len(system_prompt) > 500 else system_prompt,
            'test_input': test_input,
            'mock_response': f"Hello! I'm {agent.name}. {agent.greeting_message or 'How can I help you today?'}",
            'goals': [ag.goal.name for ag in agent.goals if ag.active],
            'voice_settings': agent.voice_settings
        })
        
    finally:
        db.close()