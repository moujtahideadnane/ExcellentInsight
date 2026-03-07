-- Enable RLS on core tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_jobs ENABLE ROW LEVEL SECURITY;

-- Create Policies for Organizations
-- Users can only see their own organization
CREATE POLICY org_isolation_policy ON organizations
    USING (id = (SELECT org_id FROM users WHERE id = current_setting('app.current_user_id', true)::UUID));

-- Create Policies for Users
-- Users can only see other users within the same organization
CREATE POLICY user_isolation_policy ON users
    USING (org_id = current_setting('app.current_org_id', true)::UUID);

-- Create Policies for Analysis Jobs
-- Users can only see jobs belonging to their organization
CREATE POLICY job_isolation_policy ON analysis_jobs
    USING (org_id = current_setting('app.current_org_id', true)::UUID);

-- Grant permissions to set these variables
-- Note: In a production environment, you might use a dedicated DB user with restricted bypassrls.
