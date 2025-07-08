"""
Goal Manager Service
Tracks and manages conversation goals during calls
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from models.enhanced_models import (
    ConversationGoal, AgentGoal, GoalProgress,
    EnhancedAgentConfig
)
from models import Call, Message
import json
import re
import logging

logger = logging.getLogger(__name__)

class GoalManager:
    """Manages conversation goals and tracks progress"""
    
    def __init__(self):
        self.active_conversations = {}  # call_id -> goal tracking data
        
    def start_conversation(self, db: Session, call_id: str, agent_id: int) -> Dict[str, Any]:
        """Initialize goal tracking for a new conversation"""
        
        # Get agent's goals
        agent_goals = db.query(AgentGoal).filter_by(
            agent_id=agent_id,
            active=True
        ).order_by(AgentGoal.priority.desc()).all()
        
        if not agent_goals:
            logger.warning(f"No goals found for agent {agent_id}")
            return {'goals': [], 'required_goals': []}
        
        # Initialize progress for each goal
        goal_data = {
            'agent_id': agent_id,
            'goals': [],
            'required_goals': [],
            'completed_goals': [],
            'start_time': datetime.utcnow()
        }
        
        for ag in agent_goals:
            goal = ag.goal
            
            # Create progress record
            progress = GoalProgress(
                call_id=call_id,
                agent_id=agent_id,
                goal_id=goal.id,
                status='in_progress',
                collected_data={},
                missing_data=goal.required_data or []
            )
            db.add(progress)
            
            goal_info = {
                'goal_id': goal.id,
                'name': goal.name,
                'type': goal.goal_type,
                'priority': ag.priority,
                'required': ag.required,
                'success_criteria': goal.success_criteria,
                'required_data': goal.required_data or [],
                'custom_criteria': ag.custom_criteria,
                'progress_id': None  # Will be set after commit
            }
            
            goal_data['goals'].append(goal_info)
            if ag.required:
                goal_data['required_goals'].append(goal.id)
        
        db.commit()
        
        # Update progress IDs
        progress_records = db.query(GoalProgress).filter_by(call_id=call_id).all()
        for progress in progress_records:
            for goal_info in goal_data['goals']:
                if goal_info['goal_id'] == progress.goal_id:
                    goal_info['progress_id'] = progress.id
        
        # Store in memory for fast access
        self.active_conversations[call_id] = goal_data
        
        return {
            'goals': goal_data['goals'],
            'required_goals': goal_data['required_goals']
        }
    
    def track_progress(self, db: Session, call_id: str, message_text: str, 
                      is_caller: bool = True) -> Dict[str, Any]:
        """Track goal progress based on conversation content"""
        
        if call_id not in self.active_conversations:
            logger.error(f"No active goal tracking for call {call_id}")
            return {'updated_goals': []}
        
        conversation_data = self.active_conversations[call_id]
        updated_goals = []
        
        # Only track caller messages for data extraction
        if is_caller:
            for goal_info in conversation_data['goals']:
                if goal_info['goal_id'] in conversation_data['completed_goals']:
                    continue
                    
                # Extract data based on goal type
                extracted_data = self._extract_goal_data(
                    message_text, 
                    goal_info['type'],
                    goal_info['required_data']
                )
                
                if extracted_data:
                    # Update progress in database
                    progress = db.query(GoalProgress).filter_by(
                        id=goal_info['progress_id']
                    ).first()
                    
                    if progress:
                        # Merge with existing data
                        current_data = progress.collected_data or {}
                        current_data.update(extracted_data)
                        progress.collected_data = current_data
                        
                        # Update missing data
                        missing = [field for field in goal_info['required_data'] 
                                 if field not in current_data]
                        progress.missing_data = missing
                        
                        # Calculate completion percentage
                        if goal_info['required_data']:
                            progress.completion_percentage = (
                                len(current_data) / len(goal_info['required_data']) * 100
                            )
                        
                        db.commit()
                        
                        updated_goals.append({
                            'goal_id': goal_info['goal_id'],
                            'name': goal_info['name'],
                            'collected_data': current_data,
                            'missing_data': missing,
                            'completion_percentage': progress.completion_percentage
                        })
        
        # Check for goal completion
        self._check_goal_completion(db, call_id)
        
        return {'updated_goals': updated_goals}
    
    def check_completion(self, db: Session, call_id: str) -> Dict[str, Any]:
        """Check if goals are completed and return status"""
        
        if call_id not in self.active_conversations:
            return {'all_required_completed': False, 'completed_goals': []}
        
        conversation_data = self.active_conversations[call_id]
        completed_goals = []
        
        for goal_info in conversation_data['goals']:
            progress = db.query(GoalProgress).filter_by(
                id=goal_info['progress_id']
            ).first()
            
            if progress and progress.status == 'completed':
                completed_goals.append({
                    'goal_id': goal_info['goal_id'],
                    'name': goal_info['name'],
                    'collected_data': progress.collected_data
                })
        
        # Check if all required goals are completed
        required_completed = all(
            goal_id in [g['goal_id'] for g in completed_goals]
            for goal_id in conversation_data['required_goals']
        )
        
        return {
            'all_required_completed': required_completed,
            'completed_goals': completed_goals,
            'total_goals': len(conversation_data['goals']),
            'required_goals_count': len(conversation_data['required_goals'])
        }
    
    def get_next_action(self, db: Session, call_id: str) -> Optional[Dict[str, Any]]:
        """Suggest next action based on goal progress"""
        
        if call_id not in self.active_conversations:
            return None
        
        conversation_data = self.active_conversations[call_id]
        
        # Find highest priority incomplete goal
        for goal_info in sorted(conversation_data['goals'], 
                               key=lambda x: x['priority'], reverse=True):
            if goal_info['goal_id'] in conversation_data['completed_goals']:
                continue
                
            progress = db.query(GoalProgress).filter_by(
                id=goal_info['progress_id']
            ).first()
            
            if progress and progress.missing_data:
                # Suggest question to collect missing data
                missing_field = progress.missing_data[0]
                question = self._generate_question_for_field(
                    missing_field, 
                    goal_info['type']
                )
                
                return {
                    'action': 'ask_question',
                    'goal_name': goal_info['name'],
                    'field': missing_field,
                    'suggested_question': question,
                    'priority': 'required' if goal_info['required'] else 'optional'
                }
        
        return None
    
    def end_conversation(self, db: Session, call_id: str) -> Dict[str, Any]:
        """Finalize goal tracking for ended conversation"""
        
        if call_id not in self.active_conversations:
            return {'summary': 'No goal tracking data available'}
        
        conversation_data = self.active_conversations[call_id]
        completion_status = self.check_completion(db, call_id)
        
        # Update any incomplete goals to failed
        for goal_info in conversation_data['goals']:
            if goal_info['goal_id'] not in conversation_data['completed_goals']:
                progress = db.query(GoalProgress).filter_by(
                    id=goal_info['progress_id']
                ).first()
                
                if progress and progress.status == 'in_progress':
                    progress.status = 'failed'
        
        db.commit()
        
        # Generate summary
        summary = {
            'duration_seconds': (datetime.utcnow() - conversation_data['start_time']).total_seconds(),
            'total_goals': len(conversation_data['goals']),
            'completed_goals': len(completion_status['completed_goals']),
            'required_goals_met': completion_status['all_required_completed'],
            'goals_summary': completion_status['completed_goals']
        }
        
        # Clean up memory
        del self.active_conversations[call_id]
        
        return summary
    
    def _extract_goal_data(self, text: str, goal_type: str, 
                          required_fields: List[str]) -> Dict[str, Any]:
        """Extract relevant data from text based on goal type"""
        
        extracted = {}
        text_lower = text.lower()
        
        # Common patterns
        patterns = {
            'date': r'(\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b|\b(?:tomorrow|today|next week)\b)',
            'time': r'(\b\d{1,2}:\d{2}\s*(?:am|pm)?\b|\b\d{1,2}\s*(?:am|pm)\b|\b(?:morning|afternoon|evening)\b)',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\b\d{3}[-.]?\d{3}[-.]?\d{4}\b|\b\d{10}\b)',
            'name': r'\bmy name is ([A-Za-z\s]+)\b|\bi\'m ([A-Za-z\s]+)\b',
            'company': r'\b(?:company|business|organization) (?:is |called )?([A-Za-z0-9\s&,.-]+)\b',
            'budget': r'\$?\d+(?:,\d{3})*(?:\.\d{2})?(?:\s*(?:k|thousand|million|m))?\b',
            'timeline': r'\b(?:within |in )?(\d+)\s*(?:days?|weeks?|months?)\b|\b(?:asap|immediately|urgent)\b'
        }
        
        # Goal-specific extraction
        if goal_type == 'schedule':
            # Look for appointment-related data
            if 'date' in required_fields:
                date_match = re.search(patterns['date'], text_lower)
                if date_match:
                    extracted['date'] = date_match.group(0)
                    
            if 'time' in required_fields:
                time_match = re.search(patterns['time'], text_lower)
                if time_match:
                    extracted['time'] = time_match.group(0)
                    
            if 'service_type' in required_fields:
                # Look for service mentions
                services = ['consultation', 'appointment', 'meeting', 'session', 
                           'checkup', 'review', 'demo', 'call']
                for service in services:
                    if service in text_lower:
                        extracted['service_type'] = service
                        break
                        
        elif goal_type == 'qualify':
            # Look for qualification data
            if 'budget' in required_fields:
                budget_match = re.search(patterns['budget'], text)
                if budget_match:
                    extracted['budget'] = budget_match.group(0)
                    
            if 'timeline' in required_fields:
                timeline_match = re.search(patterns['timeline'], text_lower)
                if timeline_match:
                    extracted['timeline'] = timeline_match.group(0)
                    
            if 'company_size' in required_fields:
                # Look for employee count
                size_match = re.search(r'\b(\d+)\s*(?:employees?|people|staff)\b', text_lower)
                if size_match:
                    extracted['company_size'] = size_match.group(1)
                    
            if 'decision_maker' in required_fields:
                # Look for authority indicators
                if any(role in text_lower for role in ['owner', 'ceo', 'president', 
                                                       'manager', 'director', 'head of']):
                    extracted['decision_maker'] = 'yes'
                elif 'need to check' in text_lower or 'ask my' in text_lower:
                    extracted['decision_maker'] = 'no'
                    
        # Extract contact info if needed
        if 'email' in required_fields:
            email_match = re.search(patterns['email'], text)
            if email_match:
                extracted['email'] = email_match.group(0)
                
        if 'phone' in required_fields:
            phone_match = re.search(patterns['phone'], text)
            if phone_match:
                extracted['phone'] = phone_match.group(0)
                
        if 'name' in required_fields:
            name_match = re.search(patterns['name'], text, re.IGNORECASE)
            if name_match:
                extracted['name'] = name_match.group(1) or name_match.group(2)
                
        return extracted
    
    def _check_goal_completion(self, db: Session, call_id: str) -> None:
        """Check if any goals have been completed"""
        
        conversation_data = self.active_conversations[call_id]
        
        for goal_info in conversation_data['goals']:
            if goal_info['goal_id'] in conversation_data['completed_goals']:
                continue
                
            progress = db.query(GoalProgress).filter_by(
                id=goal_info['progress_id']
            ).first()
            
            if not progress:
                continue
                
            # Check success criteria
            criteria = goal_info['success_criteria'] or {}
            custom_criteria = goal_info['custom_criteria'] or {}
            criteria.update(custom_criteria)  # Custom overrides default
            
            # Check required fields
            required_fields = criteria.get('required_fields', [])
            collected_data = progress.collected_data or {}
            
            fields_complete = all(field in collected_data for field in required_fields)
            
            # Check conditions
            conditions = criteria.get('conditions', [])
            conditions_met = True
            
            for condition in conditions:
                # Simple condition checking (can be expanded)
                if condition == 'confirmed_availability' and 'date' in collected_data:
                    conditions_met = True  # Simplified - would check actual availability
                elif condition == 'meets_minimum_criteria':
                    # Check if qualification criteria are met
                    if 'budget' in collected_data:
                        # Simplified budget check
                        conditions_met = True
                        
            # Mark as completed if all criteria met
            if fields_complete and conditions_met:
                progress.status = 'completed'
                progress.completed_at = datetime.utcnow()
                progress.completion_percentage = 100.0
                conversation_data['completed_goals'].append(goal_info['goal_id'])
                
                logger.info(f"Goal {goal_info['name']} completed for call {call_id}")
                
                # Trigger webhook if configured
                goal = db.query(ConversationGoal).filter_by(id=goal_info['goal_id']).first()
                if goal and goal.completion_webhook:
                    self._trigger_completion_webhook(
                        goal.completion_webhook,
                        call_id,
                        goal_info['name'],
                        collected_data
                    )
                    
        db.commit()
    
    def _generate_question_for_field(self, field: str, goal_type: str) -> str:
        """Generate appropriate question for missing field"""
        
        questions = {
            'date': "What date works best for you?",
            'time': "What time would you prefer?",
            'service_type': "What service are you interested in?",
            'budget': "What's your budget range for this project?",
            'timeline': "What's your timeline for making a decision?",
            'company_size': "How many employees does your company have?",
            'decision_maker': "Are you the decision maker for this purchase?",
            'email': "Could I get your email address?",
            'phone': "What's the best phone number to reach you?",
            'name': "May I have your name, please?",
            'issue_description': "Could you describe the issue you're experiencing?",
            'account_info': "Could you provide your account number or registered email?"
        }
        
        return questions.get(field, f"Could you provide your {field}?")
    
    def _trigger_completion_webhook(self, webhook_url: str, call_id: str, 
                                  goal_name: str, data: Dict[str, Any]) -> None:
        """Trigger webhook on goal completion"""
        
        # This would make an async HTTP request to the webhook
        # For now, just log it
        logger.info(f"Would trigger webhook {webhook_url} for goal {goal_name} completion")
        
    def get_goal_context(self, db: Session, call_id: str) -> str:
        """Get formatted goal context for prompt injection"""
        
        if call_id not in self.active_conversations:
            return ""
            
        conversation_data = self.active_conversations[call_id]
        completion_status = self.check_completion(db, call_id)
        
        context_parts = []
        
        # Add incomplete required goals
        incomplete_required = []
        for goal_info in conversation_data['goals']:
            if (goal_info['required'] and 
                goal_info['goal_id'] not in conversation_data['completed_goals']):
                progress = db.query(GoalProgress).filter_by(
                    id=goal_info['progress_id']
                ).first()
                
                if progress and progress.missing_data:
                    incomplete_required.append({
                        'name': goal_info['name'],
                        'missing': progress.missing_data
                    })
        
        if incomplete_required:
            context_parts.append("IMPORTANT - Still need to collect:")
            for goal in incomplete_required:
                context_parts.append(f"- For {goal['name']}: {', '.join(goal['missing'])}")
                
        # Add next suggested action
        next_action = self.get_next_action(db, call_id)
        if next_action:
            context_parts.append(f"\nSuggested next question: {next_action['suggested_question']}")
            
        return "\n".join(context_parts) if context_parts else ""