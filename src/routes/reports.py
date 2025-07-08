"""
Report Generation Routes - Analytics and reporting endpoints
"""
import os
import logging
import csv
import json
from io import StringIO, BytesIO
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, send_file, Response
from sqlalchemy import func, and_, or_
from src.models.call import Call, Message, AgentConfig, SMSLog, db
from src.models.customer import Customer
from src.models.user import User
from src.services.auth import jwt_required, role_required

logger = logging.getLogger(__name__)

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/generate', methods=['POST'])
@jwt_required
def generate_report():
    """
    Generate a report based on specified filters
    """
    try:
        data = request.json
        report_type = data.get('reportType', 'call_summary')
        filters = data.get('filters', {})
        
        # Parse date range
        start_date = datetime.fromisoformat(filters.get('startDate')) if filters.get('startDate') else datetime.utcnow() - timedelta(days=30)
        end_date = datetime.fromisoformat(filters.get('endDate')) if filters.get('endDate') else datetime.utcnow()
        
        # Generate report based on type
        if report_type == 'call_summary':
            report_data = generate_call_summary_report(start_date, end_date, filters)
        elif report_type == 'agent_performance':
            report_data = generate_agent_performance_report(start_date, end_date, filters)
        elif report_type == 'customer_insights':
            report_data = generate_customer_insights_report(start_date, end_date, filters)
        elif report_type == 'sms_analytics':
            report_data = generate_sms_analytics_report(start_date, end_date, filters)
        else:
            return jsonify({'error': 'Invalid report type'}), 400
        
        # Store report (in production, this would be saved to S3 or similar)
        report_id = f"{report_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        return jsonify({
            'reportId': report_id,
            'reportUrl': f'/api/reports/{report_id}/download',
            'data': report_data,
            'generatedAt': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({'error': 'Failed to generate report'}), 500

@reports_bp.route('/reports/templates', methods=['GET'])
@jwt_required
def get_report_templates():
    """
    Get available report templates
    """
    templates = [
        {
            'id': 'call_summary',
            'name': 'Call Summary Report',
            'description': 'Comprehensive overview of call activity, outcomes, and trends'
        },
        {
            'id': 'agent_performance',
            'name': 'Agent Performance Report',
            'description': 'Performance metrics for each agent type including handling times and success rates'
        },
        {
            'id': 'customer_insights',
            'name': 'Customer Insights Report',
            'description': 'Analysis of customer interactions, frequency, and preferences'
        },
        {
            'id': 'sms_analytics',
            'name': 'SMS Analytics Report',
            'description': 'SMS follow-up effectiveness and engagement metrics'
        }
    ]
    
    return jsonify(templates), 200

@reports_bp.route('/reports/<report_id>/export', methods=['GET'])
@jwt_required
def export_report(report_id):
    """
    Export report in specified format (CSV, Excel, PDF)
    """
    try:
        format_type = request.args.get('format', 'csv')
        
        # In production, retrieve stored report data
        # For now, regenerate based on report ID pattern
        report_type = report_id.split('_')[0]
        
        # Get last 30 days of data for export
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        if format_type == 'csv':
            return export_as_csv(report_type, start_date, end_date)
        elif format_type == 'excel':
            return export_as_excel(report_type, start_date, end_date)
        elif format_type == 'pdf':
            # PDF generation would require additional libraries like ReportLab
            return jsonify({'error': 'PDF export not yet implemented'}), 501
        else:
            return jsonify({'error': 'Invalid export format'}), 400
            
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        return jsonify({'error': 'Failed to export report'}), 500

def generate_call_summary_report(start_date, end_date, filters):
    """Generate call summary report data"""
    # Base query
    query = Call.query.filter(
        and_(
            Call.start_time >= start_date,
            Call.start_time <= end_date
        )
    )
    
    # Apply filters
    if filters.get('agentType'):
        query = query.filter(Call.agent_type == filters['agentType'])
    if filters.get('status'):
        query = query.filter(Call.status == filters['status'])
    
    calls = query.all()
    
    # Calculate metrics
    total_calls = len(calls)
    completed_calls = len([c for c in calls if c.status == 'completed'])
    failed_calls = len([c for c in calls if c.status == 'failed'])
    avg_duration = sum(c.duration or 0 for c in calls) / total_calls if total_calls > 0 else 0
    
    # Calls by agent type
    agent_distribution = {}
    for call in calls:
        agent_type = call.agent_type or 'unassigned'
        agent_distribution[agent_type] = agent_distribution.get(agent_type, 0) + 1
    
    # Daily breakdown
    daily_calls = db.session.query(
        func.date(Call.start_time).label('date'),
        func.count(Call.id).label('count')
    ).filter(
        and_(
            Call.start_time >= start_date,
            Call.start_time <= end_date
        )
    ).group_by(func.date(Call.start_time)).all()
    
    return {
        'summary': {
            'totalCalls': total_calls,
            'completedCalls': completed_calls,
            'failedCalls': failed_calls,
            'averageDuration': round(avg_duration, 2),
            'successRate': round((completed_calls / total_calls * 100), 2) if total_calls > 0 else 0
        },
        'agentDistribution': agent_distribution,
        'dailyBreakdown': [
            {'date': day.strftime('%Y-%m-%d'), 'calls': count}
            for day, count in daily_calls
        ]
    }

def generate_agent_performance_report(start_date, end_date, filters):
    """Generate agent performance report data"""
    agents = AgentConfig.query.all()
    performance_data = []
    
    for agent in agents:
        # Get calls for this agent
        calls = Call.query.filter(
            and_(
                Call.agent_type == agent.agent_type,
                Call.start_time >= start_date,
                Call.start_time <= end_date
            )
        ).all()
        
        if not calls:
            continue
        
        total_calls = len(calls)
        completed_calls = len([c for c in calls if c.status == 'completed'])
        avg_duration = sum(c.duration or 0 for c in calls) / total_calls
        avg_messages = sum(c.message_count or 0 for c in calls) / total_calls
        
        performance_data.append({
            'agentType': agent.agent_type,
            'agentName': agent.name,
            'totalCalls': total_calls,
            'completedCalls': completed_calls,
            'averageDuration': round(avg_duration, 2),
            'averageMessages': round(avg_messages, 2),
            'successRate': round((completed_calls / total_calls * 100), 2),
            'routingAccuracy': round(sum(c.routing_confidence or 0 for c in calls) / total_calls * 100, 2)
        })
    
    return {
        'agents': performance_data,
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }
    }

def generate_customer_insights_report(start_date, end_date, filters):
    """Generate customer insights report data"""
    # Get customers with activity in date range
    customers_with_calls = db.session.query(
        Customer.id,
        Customer.phone_number,
        Customer.name,
        func.count(Call.id).label('call_count'),
        func.avg(Call.duration).label('avg_duration')
    ).join(
        Call, Customer.id == Call.customer_id
    ).filter(
        and_(
            Call.start_time >= start_date,
            Call.start_time <= end_date
        )
    ).group_by(Customer.id).all()
    
    # Top customers
    top_customers = sorted(customers_with_calls, key=lambda x: x.call_count, reverse=True)[:10]
    
    # Customer segmentation
    segments = {
        'frequent': len([c for c in customers_with_calls if c.call_count >= 5]),
        'regular': len([c for c in customers_with_calls if 2 <= c.call_count < 5]),
        'occasional': len([c for c in customers_with_calls if c.call_count == 1])
    }
    
    return {
        'totalCustomers': len(customers_with_calls),
        'topCustomers': [
            {
                'phoneNumber': c.phone_number,
                'name': c.name or 'Unknown',
                'callCount': c.call_count,
                'avgDuration': round(c.avg_duration or 0, 2)
            }
            for c in top_customers
        ],
        'segments': segments,
        'newCustomers': Customer.query.filter(
            and_(
                Customer.created_at >= start_date,
                Customer.created_at <= end_date
            )
        ).count()
    }

def generate_sms_analytics_report(start_date, end_date, filters):
    """Generate SMS analytics report data"""
    # Get SMS logs
    sms_logs = SMSLog.query.filter(
        and_(
            SMSLog.sent_at >= start_date,
            SMSLog.sent_at <= end_date
        )
    ).all()
    
    total_sms = len(sms_logs)
    sent_sms = len([s for s in sms_logs if s.status == 'sent'])
    delivered_sms = len([s for s in sms_logs if s.status == 'delivered'])
    
    # SMS by agent type
    sms_by_agent = {}
    for sms in sms_logs:
        agent_type = sms.agent_type or 'unknown'
        sms_by_agent[agent_type] = sms_by_agent.get(agent_type, 0) + 1
    
    return {
        'summary': {
            'totalSMS': total_sms,
            'sentSMS': sent_sms,
            'deliveredSMS': delivered_sms,
            'deliveryRate': round((delivered_sms / sent_sms * 100), 2) if sent_sms > 0 else 0
        },
        'byAgentType': sms_by_agent
    }

def export_as_csv(report_type, start_date, end_date):
    """Export report data as CSV"""
    output = StringIO()
    writer = csv.writer(output)
    
    if report_type == 'call_summary':
        # Write headers
        writer.writerow(['Date', 'Call ID', 'Phone Number', 'Agent Type', 'Duration', 'Status'])
        
        # Get calls
        calls = Call.query.filter(
            and_(
                Call.start_time >= start_date,
                Call.start_time <= end_date
            )
        ).all()
        
        # Write data
        for call in calls:
            writer.writerow([
                call.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                call.call_sid,
                call.from_number,
                call.agent_type,
                call.duration,
                call.status
            ])
    
    # Create response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={report_type}_report.csv'
        }
    )

def export_as_excel(report_type, start_date, end_date):
    """Export report data as Excel (would require openpyxl or xlsxwriter)"""
    # This is a placeholder - actual implementation would use openpyxl
    return jsonify({'error': 'Excel export requires additional libraries'}), 501