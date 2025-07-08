"""
Dashboard Routes - Metrics and analytics endpoints
"""
import os
import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from sqlalchemy import func, and_
from src.models.call import Call, Message, AgentConfig, SMSLog, db
from src.models.user import User
from src.services.auth import jwt_required
from src.services.call_session import session_manager

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/metrics', methods=['GET'])
@jwt_required
def get_dashboard_metrics():
    """
    Get dashboard metrics for the main dashboard view
    """
    try:
        # Get date range from query params (default to last 7 days)
        days = int(request.args.get('days', 7))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get total calls
        total_calls = Call.query.filter(
            Call.start_time >= start_date
        ).count()
        
        # Get calls by status
        call_status_counts = db.session.query(
            Call.status, func.count(Call.id)
        ).filter(
            Call.start_time >= start_date
        ).group_by(Call.status).all()
        
        call_statuses = {
            status: count for status, count in call_status_counts
        }
        
        # Get active calls (from session manager)
        active_calls = len(session_manager.get_active_sessions())
        
        # Get average call duration
        avg_duration = db.session.query(
            func.avg(Call.duration)
        ).filter(
            and_(
                Call.start_time >= start_date,
                Call.status == 'completed'
            )
        ).scalar() or 0
        
        # Get calls by agent type
        agent_distribution = db.session.query(
            Call.agent_type, func.count(Call.id)
        ).filter(
            Call.start_time >= start_date
        ).group_by(Call.agent_type).all()
        
        # Get SMS stats
        total_sms = SMSLog.query.filter(
            SMSLog.created_at >= start_date
        ).count()
        
        sms_success = SMSLog.query.filter(
            and_(
                SMSLog.created_at >= start_date,
                SMSLog.status == 'sent'
            )
        ).count()
        
        # Calculate success rates
        call_success_rate = 0
        if total_calls > 0:
            completed_calls = call_statuses.get('completed', 0)
            call_success_rate = (completed_calls / total_calls) * 100
        
        sms_success_rate = 0
        if total_sms > 0:
            sms_success_rate = (sms_success / total_sms) * 100
        
        # Get hourly call volume for chart
        hourly_calls = db.session.query(
            func.date_trunc('hour', Call.start_time).label('hour'),
            func.count(Call.id).label('count')
        ).filter(
            Call.start_time >= start_date
        ).group_by('hour').order_by('hour').all()
        
        # Format hourly data
        call_volume_data = [
            {
                'time': hour.isoformat() if hour else None,
                'calls': count
            }
            for hour, count in hourly_calls
        ]
        
        # Get top issues/reasons
        top_issues = db.session.query(
            Message.content, func.count(Call.id)
        ).join(
            Call, Message.call_id == Call.id
        ).filter(
            and_(
                Call.start_time >= start_date,
                Message.is_ai == False  # Customer messages only
            )
        ).group_by(Message.content).order_by(
            func.count(Call.id).desc()
        ).limit(5).all()
        
        metrics = {
            'totalCalls': total_calls,
            'activeCalls': active_calls,
            'averageCallDuration': round(avg_duration, 2) if avg_duration else 0,
            'callSuccessRate': round(call_success_rate, 2),
            'totalSMS': total_sms,
            'smsSuccessRate': round(sms_success_rate, 2),
            'callStatuses': call_statuses,
            'agentDistribution': [
                {'agent': agent or 'unassigned', 'count': count}
                for agent, count in agent_distribution
            ],
            'callVolumeData': call_volume_data,
            'topIssues': [
                {'issue': content[:50] + '...' if len(content) > 50 else content, 'count': count}
                for content, count in top_issues
            ],
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            }
        }
        
        return jsonify(metrics), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return jsonify({'error': 'Failed to get metrics'}), 500

@dashboard_bp.route('/dashboard/agent-metrics', methods=['GET'])
@jwt_required
def get_agent_metrics():
    """
    Get detailed metrics for each agent type
    """
    try:
        # Get date range from query params
        days = int(request.args.get('days', 7))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all agent configurations
        agents = AgentConfig.query.all()
        
        agent_metrics = []
        
        for agent in agents:
            # Get call stats for this agent
            total_calls = Call.query.filter(
                and_(
                    Call.agent_type == agent.agent_type,
                    Call.start_time >= start_date
                )
            ).count()
            
            completed_calls = Call.query.filter(
                and_(
                    Call.agent_type == agent.agent_type,
                    Call.start_time >= start_date,
                    Call.status == 'completed'
                )
            ).count()
            
            avg_duration = db.session.query(
                func.avg(Call.duration)
            ).filter(
                and_(
                    Call.agent_type == agent.agent_type,
                    Call.start_time >= start_date,
                    Call.status == 'completed'
                )
            ).scalar() or 0
            
            # Check if agent is currently active
            active_sessions = [
                s for s in session_manager.get_active_sessions()
                if s.get('agent_type') == agent.agent_type
            ]
            
            agent_metrics.append({
                'agentType': agent.agent_type,
                'name': agent.name,
                'status': 'busy' if active_sessions else 'available',
                'totalCalls': total_calls,
                'completedCalls': completed_calls,
                'averageDuration': round(avg_duration, 2) if avg_duration else 0,
                'successRate': round((completed_calls / total_calls * 100), 2) if total_calls > 0 else 0,
                'activeCalls': len(active_sessions)
            })
        
        return jsonify({
            'agents': agent_metrics,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting agent metrics: {e}")
        return jsonify({'error': 'Failed to get agent metrics'}), 500

@dashboard_bp.route('/dashboard/call-distribution', methods=['GET'])
@jwt_required
def get_call_distribution():
    """
    Get call distribution data for charts
    """
    try:
        # Get date range
        days = int(request.args.get('days', 7))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get distribution by agent type
        agent_distribution = db.session.query(
            Call.agent_type,
            func.count(Call.id).label('count'),
            func.avg(Call.duration).label('avg_duration')
        ).filter(
            Call.start_time >= start_date
        ).group_by(Call.agent_type).all()
        
        # Get distribution by hour of day
        hourly_distribution = db.session.query(
            func.extract('hour', Call.start_time).label('hour'),
            func.count(Call.id).label('count')
        ).filter(
            Call.start_time >= start_date
        ).group_by('hour').order_by('hour').all()
        
        # Get distribution by day of week
        daily_distribution = db.session.query(
            func.extract('dow', Call.start_time).label('day'),
            func.count(Call.id).label('count')
        ).filter(
            Call.start_time >= start_date
        ).group_by('day').order_by('day').all()
        
        # Format data
        distribution_data = {
            'byAgent': [
                {
                    'agent': agent or 'unassigned',
                    'calls': count,
                    'avgDuration': round(avg_dur, 2) if avg_dur else 0
                }
                for agent, count, avg_dur in agent_distribution
            ],
            'byHour': [
                {'hour': int(hour), 'calls': count}
                for hour, count in hourly_distribution
            ],
            'byDayOfWeek': [
                {'day': int(day), 'calls': count}
                for day, count in daily_distribution
            ],
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            }
        }
        
        return jsonify(distribution_data), 200
        
    except Exception as e:
        logger.error(f"Error getting call distribution: {e}")
        return jsonify({'error': 'Failed to get call distribution'}), 500

@dashboard_bp.route('/health', methods=['GET'])
def health_check():
    """
    System health check endpoint
    """
    try:
        # Check database connection
        db_healthy = True
        try:
            db.session.execute('SELECT 1')
        except:
            db_healthy = False
        
        # Get active sessions
        active_sessions = session_manager.get_active_sessions()
        
        # Get system stats
        health_data = {
            'status': 'healthy' if db_healthy else 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': 'healthy' if db_healthy else 'unhealthy',
                'websocket': 'healthy',  # Always healthy if this endpoint responds
                'twilio': 'configured' if os.getenv('TWILIO_ACCOUNT_SID') else 'not configured',
                'openrouter': 'configured' if os.getenv('OPENROUTER_API_KEY') else 'not configured'
            },
            'stats': {
                'activeCalls': len(active_sessions),
                'totalAgents': AgentConfig.query.count(),
                'totalUsers': User.query.count()
            }
        }
        
        return jsonify(health_data), 200
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500