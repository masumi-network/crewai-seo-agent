CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    website_url TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error TEXT
);

CREATE TABLE results (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    meta_tags JSONB,
    headings JSONB,
    keywords JSONB,
    links JSONB,
    images JSONB,
    content_stats JSONB,
    mobile_stats JSONB,
    performance_stats JSONB,
    recommendations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_website_url ON jobs(website_url); 