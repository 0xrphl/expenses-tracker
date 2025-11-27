-- Setup script to create users in Supabase
-- Run this after creating the schema

-- Note: You'll need to create users through Supabase Auth UI first, then run this
-- Or use the Supabase Admin API to create users programmatically

-- After users are created in auth.users, insert them into the users table
-- Replace the email and user IDs with actual values from Supabase Auth

-- For rafael user (replace USER_ID_1 with actual UUID from auth.users)
-- INSERT INTO users (id, username, email) 
-- VALUES ('USER_ID_1', 'rafael', 'rafael@example.com')
-- ON CONFLICT (id) DO NOTHING;

-- For yessica user (replace USER_ID_2 with actual UUID from auth.users)
-- INSERT INTO users (id, username, email)
-- VALUES ('USER_ID_2', 'yessica', 'yessica@example.com')
-- ON CONFLICT (id) DO NOTHING;

-- Alternative: Use Supabase Management API or Dashboard to create users
-- Password: Fourier98*expenses

