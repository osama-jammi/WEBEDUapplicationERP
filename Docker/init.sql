


-- Créer l'utilisateur si n'existe pas (pour sécurité)
-- DO
-- $$
-- BEGIN
--   CREATE ROLE openpg WITH LOGIN PASSWORD 'openpgpwd';
-- EXCEPTION WHEN DUPLICATE_OBJECT THEN
--   NULL;
-- END
-- $$;

-- Donner les droits
GRANT ALL PRIVILEGES ON DATABASE ensiasd_v20 TO openpg;

-- Créer extension pour UUID si nécessaire
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Créer extension pour JSON
CREATE EXTENSION IF NOT EXISTS "json";

-- Logs pour vérifier
SELECT 'PostgreSQL initialized for ENSIASD' as status;