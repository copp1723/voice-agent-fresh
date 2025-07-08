"""
Customer Management Routes
"""
import logging
from flask import Blueprint, jsonify, request
from sqlalchemy import or_, and_
from src.models.customer import Customer, Tag, db
from src.models.call import Call, SMSLog
from src.services.auth import jwt_required

logger = logging.getLogger(__name__)

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/customers', methods=['GET'])
@jwt_required
def get_customers():
    """
    Get all customers with optional filtering
    """
    try:
        # Get query parameters
        search = request.args.get('search', '')
        tags = request.args.getlist('tags')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))
        
        # Build query
        query = Customer.query
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    Customer.phone_number.contains(search),
                    Customer.name.contains(search),
                    Customer.email.contains(search)
                )
            )
        
        # Apply tag filter
        if tags:
            query = query.join(Customer.tags).filter(Tag.name.in_(tags))
        
        # Order by last contact
        query = query.order_by(Customer.last_contact.desc().nullslast())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        
        return jsonify({
            'customers': [c.to_dict() for c in pagination.items],
            'total': pagination.total,
            'page': page,
            'pageSize': page_size,
            'totalPages': pagination.pages
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting customers: {e}")
        return jsonify({'error': 'Failed to get customers'}), 500

@customer_bp.route('/customers/<int:customer_id>', methods=['GET'])
@jwt_required
def get_customer(customer_id):
    """
    Get a specific customer with detailed information
    """
    try:
        customer = Customer.query.get_or_404(customer_id)
        return jsonify(customer.to_dict(include_stats=True)), 200
        
    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {e}")
        return jsonify({'error': 'Failed to get customer'}), 500

@customer_bp.route('/customers', methods=['POST'])
@jwt_required
def create_customer():
    """
    Create a new customer
    """
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('phoneNumber'):
            return jsonify({'error': 'Phone number is required'}), 400
        
        # Check if customer already exists
        existing = Customer.query.filter_by(phone_number=data['phoneNumber']).first()
        if existing:
            return jsonify({'error': 'Customer with this phone number already exists'}), 400
        
        # Create customer
        customer = Customer(
            phone_number=data['phoneNumber'],
            name=data.get('name'),
            email=data.get('email'),
            notes=data.get('notes')
        )
        
        # Add tags if provided
        if data.get('tags'):
            for tag_name in data['tags']:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                customer.tags.append(tag)
        
        db.session.add(customer)
        db.session.commit()
        
        return jsonify(customer.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create customer'}), 500

@customer_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@jwt_required
def update_customer(customer_id):
    """
    Update customer information
    """
    try:
        customer = Customer.query.get_or_404(customer_id)
        data = request.json
        
        # Update basic fields
        if 'name' in data:
            customer.name = data['name']
        if 'email' in data:
            customer.email = data['email']
        if 'notes' in data:
            customer.notes = data['notes']
        
        # Update tags
        if 'tags' in data:
            # Clear existing tags
            customer.tags = []
            
            # Add new tags
            for tag_name in data['tags']:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                customer.tags.append(tag)
        
        db.session.commit()
        
        return jsonify(customer.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update customer'}), 500

@customer_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
@jwt_required
def delete_customer(customer_id):
    """
    Delete a customer
    """
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        # Note: This will not delete calls/SMS due to foreign key constraints
        # Consider soft delete or archiving instead
        db.session.delete(customer)
        db.session.commit()
        
        return '', 204
        
    except Exception as e:
        logger.error(f"Error deleting customer {customer_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete customer'}), 500

@customer_bp.route('/customers/<int:customer_id>/calls', methods=['GET'])
@jwt_required
def get_customer_calls(customer_id):
    """
    Get all calls for a specific customer
    """
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))
        
        # Get calls
        calls = customer.calls.order_by(Call.start_time.desc()).paginate(
            page=page, per_page=page_size, error_out=False
        )
        
        return jsonify({
            'calls': [call.to_dict() for call in calls.items],
            'total': calls.total,
            'page': page,
            'pageSize': page_size,
            'totalPages': calls.pages
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting customer calls: {e}")
        return jsonify({'error': 'Failed to get customer calls'}), 500

@customer_bp.route('/customers/<int:customer_id>/sms', methods=['GET'])
@jwt_required
def get_customer_sms(customer_id):
    """
    Get SMS conversation history for a customer
    """
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        # Get SMS logs
        sms_logs = customer.sms_logs.order_by(SMSLog.sent_at.desc()).limit(50).all()
        
        return jsonify({
            'customerId': customer_id,
            'phoneNumber': customer.phone_number,
            'messages': [sms.to_dict() for sms in sms_logs],
            'total': len(sms_logs)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting customer SMS: {e}")
        return jsonify({'error': 'Failed to get SMS history'}), 500

@customer_bp.route('/customers/tags', methods=['GET'])
@jwt_required
def get_tags():
    """
    Get all available customer tags
    """
    try:
        tags = Tag.query.order_by(Tag.name).all()
        return jsonify([tag.to_dict() for tag in tags]), 200
        
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        return jsonify({'error': 'Failed to get tags'}), 500

@customer_bp.route('/customers/by-phone/<phone_number>', methods=['GET'])
@jwt_required
def get_customer_by_phone(phone_number):
    """
    Get customer by phone number (used internally)
    """
    try:
        customer = Customer.query.filter_by(phone_number=phone_number).first()
        
        if not customer:
            # Create new customer record
            customer = Customer(phone_number=phone_number)
            db.session.add(customer)
            db.session.commit()
        
        return jsonify(customer.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error getting customer by phone: {e}")
        return jsonify({'error': 'Failed to get customer'}), 500