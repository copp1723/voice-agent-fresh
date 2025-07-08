-- Migration: Add pgvector support for semantic search
-- Description: Adds pgvector extension and updates domain_knowledge table for vector similarity search

-- Enable pgvector extension (requires PostgreSQL with pgvector installed)
CREATE EXTENSION IF NOT EXISTS vector;

-- Add vector column to domain_knowledge table if using pgvector
-- Note: The embedding dimension should match your sentence transformer model (384 for all-MiniLM-L6-v2)
DO $$ 
BEGIN
    -- Check if pgvector extension is available
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        -- Add vector column if it doesn't exist
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'domain_knowledge' 
                      AND column_name = 'embedding') THEN
            ALTER TABLE domain_knowledge ADD COLUMN embedding vector(384);
        END IF;
        
        -- Create index for efficient similarity search
        CREATE INDEX IF NOT EXISTS idx_domain_knowledge_embedding 
        ON domain_knowledge USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
        
        -- Note: You'll need to populate the embedding column from embedding_vector JSON data
        -- This can be done programmatically through the KnowledgeBase service
    END IF;
END $$;

-- Add knowledge_type constraint if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.constraint_column_usage 
        WHERE table_name = 'domain_knowledge' 
        AND constraint_name = 'domain_knowledge_knowledge_type_check'
    ) THEN
        ALTER TABLE domain_knowledge 
        ADD CONSTRAINT domain_knowledge_knowledge_type_check 
        CHECK (knowledge_type IN ('fact', 'process', 'policy', 'faq'));
    END IF;
END $$;

-- Create a function to convert JSON embedding to vector (for migration)
CREATE OR REPLACE FUNCTION json_to_vector(json_data json) 
RETURNS vector AS $$
DECLARE
    vec_array float4[];
BEGIN
    -- Convert JSON array to PostgreSQL array
    vec_array := ARRAY(SELECT json_array_elements_text(json_data)::float4);
    -- Cast to vector type
    RETURN vec_array::vector;
EXCEPTION
    WHEN OTHERS THEN
        -- Return NULL if conversion fails
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Optional: Migrate existing embeddings from JSON to vector column
-- Uncomment and run this if you have existing data with embeddings
/*
UPDATE domain_knowledge 
SET embedding = json_to_vector(embedding_vector)
WHERE embedding_vector IS NOT NULL 
AND embedding IS NULL;
*/

-- Add comment to explain the columns
COMMENT ON COLUMN domain_knowledge.embedding_vector IS 'JSON storage of embeddings for compatibility';
COMMENT ON COLUMN domain_knowledge.embedding IS 'Native pgvector storage for efficient similarity search';