-- Migration: Create validation_results table for dashboard
CREATE TABLE IF NOT EXISTS validation_results (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    correlation_id VARCHAR(100),
    decision VARCHAR(20) NOT NULL,
    priority VARCHAR(20),
    synthesis_score FLOAT,
    citation_score FLOAT,
    hallucination_rate FLOAT,
    total_time_ms FLOAT,
    synthesis_time_ms FLOAT,
    citation_time_ms FLOAT,
    hallucination_time_ms FLOAT,
    total_citations INTEGER DEFAULT 0,
    verified_citations INTEGER DEFAULT 0,
    interpretation_citations INTEGER DEFAULT 0,
    validation_details JSONB,
    review_status VARCHAR(20) DEFAULT 'pending',
    reviewer_id VARCHAR(100),
    reviewer_feedback TEXT,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_validation_results_decision ON validation_results(decision);
CREATE INDEX IF NOT EXISTS idx_validation_results_priority ON validation_results(priority);
CREATE INDEX IF NOT EXISTS idx_validation_results_created_at ON validation_results(created_at);
CREATE INDEX IF NOT EXISTS idx_validation_results_correlation_id ON validation_results(correlation_id);
CREATE INDEX IF NOT EXISTS idx_validation_results_review_status ON validation_results(review_status);
