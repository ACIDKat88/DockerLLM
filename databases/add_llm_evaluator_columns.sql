-- Add LLMEvaluator metrics columns to analytics table
ALTER TABLE analytics
    ADD COLUMN IF NOT EXISTS llm_evaluator_CompositeRagasScore FLOAT,
    -- Add any additional LLMEvaluator metrics that might be useful
    ADD COLUMN IF NOT EXISTS llm_evaluator_factual_consistency FLOAT,
    ADD COLUMN IF NOT EXISTS llm_evaluator_answer_relevance FLOAT,
    ADD COLUMN IF NOT EXISTS llm_evaluator_context_relevance FLOAT,
    ADD COLUMN IF NOT EXISTS llm_evaluator_context_coverage FLOAT,
    ADD COLUMN IF NOT EXISTS llm_evaluator_coherence FLOAT,
    ADD COLUMN IF NOT EXISTS llm_evaluator_fluency FLOAT,
    -- Add timestamp for when LLMEvaluator metrics were last updated
    ADD COLUMN IF NOT EXISTS llm_evaluator_updated_at TIMESTAMP;

-- Add comment to explain the LLMEvaluator metrics
COMMENT ON COLUMN analytics.llm_evaluator_CompositeRagasScore IS 'Overall score from LLMEvaluator implementation';
COMMENT ON COLUMN analytics.llm_evaluator_factual_consistency IS 'Factual consistency score from LLMEvaluator';
COMMENT ON COLUMN analytics.llm_evaluator_answer_relevance IS 'Answer relevance score from LLMEvaluator';
COMMENT ON COLUMN analytics.llm_evaluator_context_relevance IS 'Context relevance score from LLMEvaluator';
COMMENT ON COLUMN analytics.llm_evaluator_context_coverage IS 'Context coverage score from LLMEvaluator';
COMMENT ON COLUMN analytics.llm_evaluator_coherence IS 'Coherence score from LLMEvaluator';
COMMENT ON COLUMN analytics.llm_evaluator_fluency IS 'Fluency score from LLMEvaluator';
COMMENT ON COLUMN analytics.llm_evaluator_updated_at IS 'Timestamp when LLMEvaluator metrics were last updated';

-- Add LLMEvaluator metrics columns to feedback table
ALTER TABLE feedback
    ADD COLUMN IF NOT EXISTS llm_evaluator_CompositeRagasScore FLOAT,
    -- Add any additional LLMEvaluator metrics that might be useful
    ADD COLUMN IF NOT EXISTS llm_evaluator_factual_consistency FLOAT,
    ADD COLUMN IF NOT EXISTS llm_evaluator_answer_relevance FLOAT,
    ADD COLUMN IF NOT EXISTS llm_evaluator_context_relevance FLOAT,
    ADD COLUMN IF NOT EXISTS llm_evaluator_context_coverage FLOAT,
    ADD COLUMN IF NOT EXISTS llm_evaluator_coherence FLOAT,
    ADD COLUMN IF NOT EXISTS llm_evaluator_fluency FLOAT,
    -- Add timestamp for when LLMEvaluator metrics were last updated
    ADD COLUMN IF NOT EXISTS llm_evaluator_updated_at TIMESTAMP;

-- Add comment to explain the LLMEvaluator metrics in feedback table
COMMENT ON COLUMN feedback.llm_evaluator_CompositeRagasScore IS 'Overall score from LLMEvaluator implementation';
COMMENT ON COLUMN feedback.llm_evaluator_factual_consistency IS 'Factual consistency score from LLMEvaluator';
COMMENT ON COLUMN feedback.llm_evaluator_answer_relevance IS 'Answer relevance score from LLMEvaluator';
COMMENT ON COLUMN feedback.llm_evaluator_context_relevance IS 'Context relevance score from LLMEvaluator';
COMMENT ON COLUMN feedback.llm_evaluator_context_coverage IS 'Context coverage score from LLMEvaluator';
COMMENT ON COLUMN feedback.llm_evaluator_coherence IS 'Coherence score from LLMEvaluator';
COMMENT ON COLUMN feedback.llm_evaluator_fluency IS 'Fluency score from LLMEvaluator';
COMMENT ON COLUMN feedback.llm_evaluator_updated_at IS 'Timestamp when LLMEvaluator metrics were last updated';

-- Create indexes for faster querying of LLMEvaluator metrics
CREATE INDEX IF NOT EXISTS idx_analytics_llm_evaluator_score 
    ON analytics(llm_evaluator_CompositeRagasScore);
CREATE INDEX IF NOT EXISTS idx_feedback_llm_evaluator_score 
    ON feedback(llm_evaluator_CompositeRagasScore);

-- Create a function to update LLMEvaluator metrics timestamp
CREATE OR REPLACE FUNCTION update_llm_evaluator_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.llm_evaluator_updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to automatically update timestamp when LLMEvaluator metrics are updated
CREATE TRIGGER update_analytics_llm_evaluator_timestamp
    BEFORE UPDATE OF 
        llm_evaluator_CompositeRagasScore,
        llm_evaluator_factual_consistency,
        llm_evaluator_answer_relevance,
        llm_evaluator_context_relevance,
        llm_evaluator_context_coverage,
        llm_evaluator_coherence,
        llm_evaluator_fluency
    ON analytics
    FOR EACH ROW
    EXECUTE FUNCTION update_llm_evaluator_timestamp();

CREATE TRIGGER update_feedback_llm_evaluator_timestamp
    BEFORE UPDATE OF 
        llm_evaluator_CompositeRagasScore,
        llm_evaluator_factual_consistency,
        llm_evaluator_answer_relevance,
        llm_evaluator_context_relevance,
        llm_evaluator_context_coverage,
        llm_evaluator_coherence,
        llm_evaluator_fluency
    ON feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_llm_evaluator_timestamp(); 