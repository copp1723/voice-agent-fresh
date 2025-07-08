"""
Knowledge Management API Routes
Provides CRUD operations for domain knowledge base with semantic search capabilities
"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from database import get_db
from models.enhanced_models import DomainKnowledge, AgentDomain, EnhancedAgentConfig
from services.knowledge_base import KnowledgeBase, EmbeddingService
from auth import require_auth
import logging
import csv
import io
import json
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)
knowledge_bp = Blueprint('knowledge_management', __name__, url_prefix='/api/knowledge')
domains_bp = Blueprint('domains_management', __name__, url_prefix='/api/domains')

# Initialize services
embedding_service = EmbeddingService()


@knowledge_bp.route('', methods=['POST'])
@require_auth
def add_knowledge():
    """Add a new knowledge entry"""
    db: Session = next(get_db())
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('domain_name'):
            return jsonify({'error': 'Domain name is required'}), 400
        if not data.get('content'):
            return jsonify({'error': 'Content is required'}), 400
        if not data.get('knowledge_type'):
            return jsonify({'error': 'Knowledge type is required'}), 400
        
        # Validate knowledge type
        valid_types = ['fact', 'process', 'policy', 'faq']
        if data['knowledge_type'] not in valid_types:
            return jsonify({'error': f'Knowledge type must be one of: {", ".join(valid_types)}'}), 400
        
        # Initialize knowledge base
        kb = KnowledgeBase(db, embedding_service)
        
        # Create knowledge entry
        knowledge = kb.add_knowledge(
            domain=data['domain_name'],
            content=data['content'],
            metadata={
                'knowledge_type': data['knowledge_type'],
                'title': data.get('title', ''),
                'tags': data.get('tags', []),
                'source': data.get('source', ''),
                'validity_period': data.get('validity_period', None)
            }
        )
        
        # Prepare response
        return jsonify({
            'success': True,
            'knowledge_id': knowledge.id,
            'message': f'Knowledge entry created successfully',
            'knowledge': {
                'id': knowledge.id,
                'domain_name': knowledge.domain_name,
                'title': knowledge.metadata.get('title', ''),
                'knowledge_type': knowledge.metadata.get('knowledge_type'),
                'content': knowledge.content,
                'version': knowledge.version,
                'active': knowledge.active,
                'created_at': knowledge.created_at.isoformat(),
                'updated_at': knowledge.updated_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding knowledge: {str(e)}")
        return jsonify({'error': 'Failed to add knowledge entry'}), 500
    finally:
        db.close()


@knowledge_bp.route('', methods=['GET'])
@require_auth
def list_knowledge():
    """List knowledge entries with optional domain filtering"""
    db: Session = next(get_db())
    try:
        # Get query parameters
        domain_filter = request.args.get('domain')
        active_only = request.args.get('active', 'true').lower() == 'true'
        knowledge_type = request.args.get('type')
        search_query = request.args.get('search')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Initialize knowledge base
        kb = KnowledgeBase(db, embedding_service)
        
        if search_query and domain_filter:
            # Use semantic search if search query is provided
            results = kb.search_relevant(search_query, domain_filter, top_k=limit)
            knowledge_items = []
            for knowledge, score in results:
                item_dict = {
                    'id': knowledge.id,
                    'domain_name': knowledge.domain_name,
                    'title': knowledge.metadata.get('title', ''),
                    'knowledge_type': knowledge.metadata.get('knowledge_type', knowledge.knowledge_type),
                    'content': knowledge.content,
                    'metadata': knowledge.metadata,
                    'version': knowledge.version,
                    'active': knowledge.active,
                    'relevance_score': score,
                    'created_at': knowledge.created_at.isoformat(),
                    'updated_at': knowledge.updated_at.isoformat()
                }
                knowledge_items.append(item_dict)
        else:
            # Regular listing with filters
            query = db.query(DomainKnowledge)
            
            if domain_filter:
                query = query.filter(DomainKnowledge.domain_name == domain_filter)
            
            if active_only:
                query = query.filter(DomainKnowledge.active == True)
            
            if knowledge_type:
                # Check both in the column and in metadata
                query = query.filter(
                    db.or_(
                        DomainKnowledge.knowledge_type == knowledge_type,
                        DomainKnowledge.metadata['knowledge_type'].astext == knowledge_type
                    )
                )
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            items = query.order_by(DomainKnowledge.created_at.desc()).offset(offset).limit(limit).all()
            
            knowledge_items = [{
                'id': item.id,
                'domain_name': item.domain_name,
                'title': item.metadata.get('title', item.title or ''),
                'knowledge_type': item.metadata.get('knowledge_type', item.knowledge_type),
                'content': item.content,
                'metadata': item.metadata,
                'version': item.version,
                'active': item.active,
                'created_at': item.created_at.isoformat(),
                'updated_at': item.updated_at.isoformat()
            } for item in items]
        
        return jsonify({
            'knowledge_items': knowledge_items,
            'total': len(knowledge_items) if search_query else total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error listing knowledge: {str(e)}")
        return jsonify({'error': 'Failed to list knowledge entries'}), 500
    finally:
        db.close()


@knowledge_bp.route('/<int:knowledge_id>', methods=['GET'])
@require_auth
def get_knowledge(knowledge_id: int):
    """Get a specific knowledge entry"""
    db: Session = next(get_db())
    try:
        knowledge = db.query(DomainKnowledge).filter_by(id=knowledge_id).first()
        
        if not knowledge:
            return jsonify({'error': 'Knowledge entry not found'}), 404
        
        # Get agents using this knowledge
        agent_domains = db.query(AgentDomain, EnhancedAgentConfig).join(
            EnhancedAgentConfig, AgentDomain.agent_id == EnhancedAgentConfig.id
        ).filter(
            AgentDomain.domain_id == knowledge_id
        ).all()
        
        agents_using = [{
            'agent_id': agent.id,
            'agent_name': agent.name,
            'relevance_score': agent_domain.relevance_score
        } for agent_domain, agent in agent_domains]
        
        return jsonify({
            'id': knowledge.id,
            'domain_name': knowledge.domain_name,
            'title': knowledge.metadata.get('title', knowledge.title or ''),
            'knowledge_type': knowledge.metadata.get('knowledge_type', knowledge.knowledge_type),
            'content': knowledge.content,
            'metadata': knowledge.metadata,
            'version': knowledge.version,
            'active': knowledge.active,
            'agents_using': agents_using,
            'created_at': knowledge.created_at.isoformat(),
            'updated_at': knowledge.updated_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting knowledge: {str(e)}")
        return jsonify({'error': 'Failed to get knowledge entry'}), 500
    finally:
        db.close()


@knowledge_bp.route('/<int:knowledge_id>', methods=['PUT'])
@require_auth
def update_knowledge(knowledge_id: int):
    """Update an existing knowledge entry"""
    db: Session = next(get_db())
    try:
        data = request.get_json()
        
        # Initialize knowledge base
        kb = KnowledgeBase(db, embedding_service)
        
        # Prepare metadata update
        metadata_update = None
        if any(key in data for key in ['title', 'knowledge_type', 'tags', 'source', 'validity_period']):
            knowledge = db.query(DomainKnowledge).filter_by(id=knowledge_id).first()
            if not knowledge:
                return jsonify({'error': 'Knowledge entry not found'}), 404
            
            metadata_update = knowledge.metadata.copy()
            for key in ['title', 'knowledge_type', 'tags', 'source', 'validity_period']:
                if key in data:
                    metadata_update[key] = data[key]
        
        # Update knowledge
        updated_knowledge = kb.update_knowledge(
            knowledge_id=knowledge_id,
            content=data.get('content'),
            metadata=metadata_update,
            active=data.get('active')
        )
        
        if not updated_knowledge:
            return jsonify({'error': 'Knowledge entry not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Knowledge entry updated successfully',
            'knowledge': {
                'id': updated_knowledge.id,
                'domain_name': updated_knowledge.domain_name,
                'title': updated_knowledge.metadata.get('title', ''),
                'knowledge_type': updated_knowledge.metadata.get('knowledge_type'),
                'content': updated_knowledge.content,
                'version': updated_knowledge.version,
                'active': updated_knowledge.active,
                'updated_at': updated_knowledge.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating knowledge: {str(e)}")
        return jsonify({'error': 'Failed to update knowledge entry'}), 500
    finally:
        db.close()


@knowledge_bp.route('/<int:knowledge_id>', methods=['DELETE'])
@require_auth
def delete_knowledge(knowledge_id: int):
    """Soft delete a knowledge entry"""
    db: Session = next(get_db())
    try:
        # Initialize knowledge base
        kb = KnowledgeBase(db, embedding_service)
        
        # Delete knowledge
        success = kb.delete_knowledge(knowledge_id)
        
        if not success:
            return jsonify({'error': 'Knowledge entry not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Knowledge entry deactivated successfully'
        })
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting knowledge: {str(e)}")
        return jsonify({'error': 'Failed to delete knowledge entry'}), 500
    finally:
        db.close()


@knowledge_bp.route('/import', methods=['POST'])
@require_auth
def import_knowledge():
    """Import knowledge entries from CSV or JSON"""
    db: Session = next(get_db())
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        domain_name = request.form.get('domain_name')
        
        if not domain_name:
            return jsonify({'error': 'Domain name is required'}), 400
        
        if not file.filename:
            return jsonify({'error': 'No file selected'}), 400
        
        # Initialize knowledge base
        kb = KnowledgeBase(db, embedding_service)
        
        # Process file based on extension
        entries = []
        
        if file.filename.endswith('.csv'):
            # Process CSV file
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_reader = csv.DictReader(stream)
            
            for row in csv_reader:
                entry = {
                    'content': row.get('content', ''),
                    'metadata': {
                        'title': row.get('title', ''),
                        'knowledge_type': row.get('type', row.get('knowledge_type', 'fact')),
                        'tags': row.get('tags', '').split(',') if row.get('tags') else [],
                        'source': row.get('source', '')
                    }
                }
                entries.append(entry)
                
        elif file.filename.endswith('.json'):
            # Process JSON file
            data = json.load(file.stream)
            
            if isinstance(data, list):
                entries = data
            elif isinstance(data, dict) and 'entries' in data:
                entries = data['entries']
            else:
                return jsonify({'error': 'Invalid JSON format. Expected array or object with "entries" key'}), 400
        else:
            return jsonify({'error': 'Unsupported file format. Use CSV or JSON'}), 400
        
        # Import entries
        successful, failed = kb.bulk_import_knowledge(domain_name, entries)
        
        return jsonify({
            'success': True,
            'message': f'Import completed: {successful} successful, {failed} failed',
            'successful': successful,
            'failed': failed
        })
        
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON file'}), 400
    except Exception as e:
        db.rollback()
        logger.error(f"Error importing knowledge: {str(e)}")
        return jsonify({'error': f'Failed to import knowledge: {str(e)}'}), 500
    finally:
        db.close()


@knowledge_bp.route('/generate-embeddings', methods=['POST'])
@require_auth
def generate_embeddings():
    """Regenerate embeddings for all or specific domain knowledge"""
    db: Session = next(get_db())
    try:
        data = request.get_json() or {}
        domain_filter = data.get('domain')
        
        # Initialize knowledge base
        kb = KnowledgeBase(db, embedding_service)
        
        # Regenerate embeddings
        count = kb.regenerate_embeddings(domain_filter)
        
        return jsonify({
            'success': True,
            'message': f'Regenerated embeddings for {count} knowledge entries',
            'count': count,
            'domain': domain_filter or 'all'
        })
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating embeddings: {str(e)}")
        return jsonify({'error': 'Failed to regenerate embeddings'}), 500
    finally:
        db.close()


@domains_bp.route('', methods=['GET'])
@require_auth
def list_domains():
    """List all unique domains"""
    db: Session = next(get_db())
    try:
        # Get all unique domain names
        domains = db.query(distinct(DomainKnowledge.domain_name)).filter(
            DomainKnowledge.active == True
        ).all()
        
        domain_list = []
        for (domain_name,) in domains:
            # Count knowledge entries per domain
            count = db.query(DomainKnowledge).filter(
                DomainKnowledge.domain_name == domain_name,
                DomainKnowledge.active == True
            ).count()
            
            # Count agents using this domain
            agent_count = db.query(AgentDomain).join(
                DomainKnowledge, AgentDomain.domain_id == DomainKnowledge.id
            ).filter(
                DomainKnowledge.domain_name == domain_name
            ).distinct(AgentDomain.agent_id).count()
            
            domain_list.append({
                'name': domain_name,
                'knowledge_count': count,
                'agent_count': agent_count
            })
        
        # Sort by name
        domain_list.sort(key=lambda x: x['name'])
        
        return jsonify({
            'domains': domain_list,
            'total': len(domain_list)
        })
        
    except Exception as e:
        logger.error(f"Error listing domains: {str(e)}")
        return jsonify({'error': 'Failed to list domains'}), 500
    finally:
        db.close()


@domains_bp.route('', methods=['POST'])
@require_auth
def create_domain():
    """Create a new domain with initial knowledge"""
    db: Session = next(get_db())
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Domain name is required'}), 400
        
        domain_name = data['name'].strip()
        
        # Check if domain already exists
        existing = db.query(DomainKnowledge).filter_by(
            domain_name=domain_name
        ).first()
        
        if existing:
            return jsonify({'error': f'Domain "{domain_name}" already exists'}), 400
        
        # Initialize knowledge base
        kb = KnowledgeBase(db, embedding_service)
        
        # Create initial knowledge entries if provided
        created_count = 0
        if data.get('initial_knowledge'):
            for entry in data['initial_knowledge']:
                if entry.get('content'):
                    kb.add_knowledge(
                        domain=domain_name,
                        content=entry['content'],
                        metadata={
                            'title': entry.get('title', ''),
                            'knowledge_type': entry.get('knowledge_type', 'fact'),
                            'tags': entry.get('tags', []),
                            'source': 'domain_creation'
                        }
                    )
                    created_count += 1
        
        # If no initial knowledge, create a placeholder entry
        if created_count == 0:
            kb.add_knowledge(
                domain=domain_name,
                content=data.get('description', f'Knowledge base for {domain_name}'),
                metadata={
                    'title': f'{domain_name} Overview',
                    'knowledge_type': 'fact',
                    'source': 'domain_creation'
                }
            )
            created_count = 1
        
        return jsonify({
            'success': True,
            'message': f'Domain "{domain_name}" created successfully',
            'domain': {
                'name': domain_name,
                'knowledge_count': created_count
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating domain: {str(e)}")
        return jsonify({'error': 'Failed to create domain'}), 500
    finally:
        db.close()


# Export route creation function for import formats
@knowledge_bp.route('/export-template/<format>', methods=['GET'])
@require_auth
def export_template(format: str):
    """Get a template file for importing knowledge"""
    if format == 'csv':
        csv_content = """title,content,type,tags,source
"Example FAQ","This is an example answer to a frequently asked question","faq","example,template","manual"
"Company Policy","Employees must follow the code of conduct","policy","policy,hr","employee_handbook"
"Process Step","First, verify the customer information","process","verification,process","training_manual"
"""
        return csv_content, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=knowledge_import_template.csv'
        }
    
    elif format == 'json':
        json_template = {
            "entries": [
                {
                    "content": "This is an example answer to a frequently asked question",
                    "metadata": {
                        "title": "Example FAQ",
                        "knowledge_type": "faq",
                        "tags": ["example", "template"],
                        "source": "manual"
                    }
                },
                {
                    "content": "Employees must follow the code of conduct",
                    "metadata": {
                        "title": "Company Policy",
                        "knowledge_type": "policy",
                        "tags": ["policy", "hr"],
                        "source": "employee_handbook"
                    }
                }
            ]
        }
        return jsonify(json_template), 200, {
            'Content-Type': 'application/json',
            'Content-Disposition': 'attachment; filename=knowledge_import_template.json'
        }
    
    else:
        return jsonify({'error': 'Invalid format. Use "csv" or "json"'}), 400