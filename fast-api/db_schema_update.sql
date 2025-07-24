-- Add RAGAS metric columns to the analytics table
ALTER TABLE analytics 
ADD COLUMN IF NOT EXISTS faithfulness FLOAT,
ADD COLUMN IF NOT EXISTS answer_relevancy FLOAT,
ADD COLUMN IF NOT EXISTS context_relevancy FLOAT, 
ADD COLUMN IF NOT EXISTS context_precision FLOAT,
ADD COLUMN IF NOT EXISTS context_recall FLOAT,
ADD COLUMN IF NOT EXISTS harmfulness FLOAT;

-- Add RAGAS metric columns to the feedback table
ALTER TABLE feedback
ADD COLUMN IF NOT EXISTS faithfulness FLOAT,
ADD COLUMN IF NOT EXISTS answer_relevancy FLOAT,
ADD COLUMN IF NOT EXISTS context_relevancy FLOAT, 
ADD COLUMN IF NOT EXISTS context_precision FLOAT,
ADD COLUMN IF NOT EXISTS context_recall FLOAT,
ADD COLUMN IF NOT EXISTS harmfulness FLOAT;

-- Create an index on the context_relevancy column for faster queries
CREATE INDEX IF NOT EXISTS idx_analytics_context_relevancy ON analytics (context_relevancy);

-- Create an index on the faithfulness column for faster queries
CREATE INDEX IF NOT EXISTS idx_analytics_faithfulness ON analytics (faithfulness);

-- Comment for the new columns
COMMENT ON COLUMN analytics.faithfulness IS 'RAGAS metric: Measures whether the generated answer contains only information present in the retrieved contexts';
COMMENT ON COLUMN analytics.answer_relevancy IS 'RAGAS metric: Measures how relevant the answer is to the question';
COMMENT ON COLUMN analytics.context_relevancy IS 'RAGAS metric: Measures how relevant the retrieved contexts are to the question';
COMMENT ON COLUMN analytics.context_precision IS 'RAGAS metric: Measures the precision of context retrieval';
COMMENT ON COLUMN analytics.context_recall IS 'RAGAS metric: Measures the recall of context retrieval';
COMMENT ON COLUMN analytics.harmfulness IS 'RAGAS metric: Measures whether the generated answer contains harmful content'; 