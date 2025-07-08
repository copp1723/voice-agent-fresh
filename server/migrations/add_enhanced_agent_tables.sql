-- Migration: Add enhanced agent customization tables
-- Description: Adds support for flexible agent configuration with goals, instructions, and domain knowledge

-- Agent Templates table
CREATE TABLE IF NOT EXISTS agent_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    base_prompt TEXT NOT NULL,
    voice_config JSONB DEFAULT '{}',
    industry VARCHAR(100),
    use_case VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation Goals table
CREATE TABLE IF NOT EXISTS conversation_goals (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    goal_type VARCHAR(50), -- 'schedule', 'qualify', 'support', 'survey', 'custom'
    success_criteria JSONB NOT NULL, -- {"required_fields": [], "conditions": []}
    required_data JSONB DEFAULT '[]', -- List of data points to collect
    completion_webhook TEXT, -- URL to call on completion
    max_duration_seconds INTEGER DEFAULT 600, -- 10 minutes default
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced Agent Configs table
CREATE TABLE IF NOT EXISTS enhanced_agent_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    template_id INTEGER REFERENCES agent_templates(id),
    
    -- Core configuration
    system_prompt TEXT,
    greeting_message TEXT,
    voice_id VARCHAR(100),
    voice_settings JSONB DEFAULT '{}',
    
    -- Behavioral settings
    personality_traits JSONB DEFAULT '[]',
    conversation_style VARCHAR(50) DEFAULT 'balanced',
    max_conversation_turns INTEGER DEFAULT 50,
    response_time_ms INTEGER DEFAULT 1000,
    
    -- Routing and priority
    keywords JSONB DEFAULT '[]',
    priority INTEGER DEFAULT 0,
    routing_confidence_threshold FLOAT DEFAULT 0.7,
    
    -- Status
    active BOOLEAN DEFAULT TRUE,
    test_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Custom settings
    custom_settings JSONB DEFAULT '{}'
);

-- Agent Instructions table
CREATE TABLE IF NOT EXISTS agent_instructions (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES enhanced_agent_configs(id) ON DELETE CASCADE,
    instruction_type VARCHAR(50) NOT NULL CHECK (instruction_type IN ('do', 'dont')),
    category VARCHAR(100),
    instruction TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    context_trigger JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Domain Knowledge table
CREATE TABLE IF NOT EXISTS domain_knowledge (
    id SERIAL PRIMARY KEY,
    domain_name VARCHAR(255) NOT NULL,
    knowledge_type VARCHAR(50) NOT NULL CHECK (knowledge_type IN ('fact', 'process', 'policy', 'faq')),
    title VARCHAR(255),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding_vector JSON,
    version INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent Goals junction table
CREATE TABLE IF NOT EXISTS agent_goals (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES enhanced_agent_configs(id) ON DELETE CASCADE,
    goal_id INTEGER NOT NULL REFERENCES conversation_goals(id),
    priority INTEGER DEFAULT 0,
    required BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    custom_criteria JSONB,
    UNIQUE(agent_id, goal_id)
);

-- Agent Domains junction table
CREATE TABLE IF NOT EXISTS agent_domains (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES enhanced_agent_configs(id) ON DELETE CASCADE,
    domain_id INTEGER NOT NULL REFERENCES domain_knowledge(id),
    relevance_score FLOAT DEFAULT 1.0,
    UNIQUE(agent_id, domain_id)
);

-- Voice Profiles table
CREATE TABLE IF NOT EXISTS voice_profiles (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL UNIQUE REFERENCES enhanced_agent_configs(id) ON DELETE CASCADE,
    voice_provider VARCHAR(50) DEFAULT 'chatterbox',
    voice_model VARCHAR(100),
    voice_clone_id VARCHAR(255),
    
    -- Voice characteristics
    base_emotion VARCHAR(50) DEFAULT 'neutral',
    emotion_range JSONB DEFAULT '{}',
    prosody_settings JSONB DEFAULT '{}',
    
    -- Sample storage
    sample_audio_urls JSONB DEFAULT '[]',
    training_status VARCHAR(50) DEFAULT 'pending',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Goal Progress tracking table
CREATE TABLE IF NOT EXISTS goal_progress (
    id SERIAL PRIMARY KEY,
    call_id VARCHAR(255) NOT NULL,
    agent_id INTEGER NOT NULL REFERENCES enhanced_agent_configs(id),
    goal_id INTEGER NOT NULL REFERENCES conversation_goals(id),
    
    -- Progress tracking
    status VARCHAR(50) DEFAULT 'in_progress',
    collected_data JSONB DEFAULT '{}',
    missing_data JSONB DEFAULT '[]',
    completion_percentage FLOAT DEFAULT 0.0,
    
    -- Timestamps
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Conversation context
    relevant_messages JSONB DEFAULT '[]'
);

-- Performance Metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES enhanced_agent_configs(id),
    call_id VARCHAR(255),
    metric_type VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_agent_instructions_agent_id ON agent_instructions(agent_id);
CREATE INDEX idx_agent_goals_agent_id ON agent_goals(agent_id);
CREATE INDEX idx_agent_domains_agent_id ON agent_domains(agent_id);
CREATE INDEX idx_goal_progress_call_id ON goal_progress(call_id);
CREATE INDEX idx_goal_progress_agent_id ON goal_progress(agent_id);
CREATE INDEX idx_performance_metrics_agent_id ON performance_metrics(agent_id);
CREATE INDEX idx_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX idx_domain_knowledge_domain_name ON domain_knowledge(domain_name);

-- Create update timestamp triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agent_templates_updated_at BEFORE UPDATE ON agent_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_enhanced_agent_configs_updated_at BEFORE UPDATE ON enhanced_agent_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_domain_knowledge_updated_at BEFORE UPDATE ON domain_knowledge
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_voice_profiles_updated_at BEFORE UPDATE ON voice_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default templates
INSERT INTO agent_templates (name, description, base_prompt, voice_config, industry, use_case) VALUES
('Appointment Scheduler', 'Template for scheduling appointments', 
'You are a professional appointment scheduling assistant. Your goal is to help callers schedule appointments efficiently while being friendly and accommodating.',
'{"emotion": "friendly", "speed": 1.0, "pitch": 0}',
'general', 'scheduling'),

('Lead Qualifier', 'Template for qualifying sales leads',
'You are a professional sales qualification specialist. Your goal is to identify qualified leads by understanding their needs, timeline, and budget.',
'{"emotion": "professional", "speed": 0.95, "pitch": -1}',
'sales', 'qualification'),

('Customer Support', 'Template for handling support inquiries',
'You are a knowledgeable customer support representative. Your goal is to help resolve customer issues efficiently while maintaining a positive experience.',
'{"emotion": "empathetic", "speed": 1.0, "pitch": 0}',
'general', 'support');

-- Insert default conversation goals
INSERT INTO conversation_goals (name, description, goal_type, success_criteria, required_data) VALUES
('Schedule Appointment', 'Successfully schedule an appointment', 'schedule',
'{"required_fields": ["date", "time", "service_type"], "conditions": ["confirmed_availability"]}',
'["preferred_date", "preferred_time", "service_type", "contact_info"]'),

('Qualify Lead', 'Qualify a sales lead', 'qualify',
'{"required_fields": ["budget", "timeline", "decision_maker"], "conditions": ["meets_minimum_criteria"]}',
'["company_size", "budget_range", "timeline", "decision_maker", "pain_points"]'),

('Resolve Issue', 'Resolve a customer support issue', 'support',
'{"required_fields": ["issue_type", "resolution"], "conditions": ["customer_satisfied"]}',
'["issue_description", "account_info", "previous_attempts"]');