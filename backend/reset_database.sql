-- Reset database by dropping all tables
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO training;
GRANT ALL ON SCHEMA public TO public;
