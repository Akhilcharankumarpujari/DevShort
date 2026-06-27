-- Create databases for TechHub microservices
SELECT 'CREATE DATABASE techhub_users'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'techhub_users')\gexec

SELECT 'CREATE DATABASE techhub_products'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'techhub_products')\gexec

SELECT 'CREATE DATABASE techhub_orders'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'techhub_orders')\gexec

SELECT 'CREATE DATABASE techhub_inventory'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'techhub_inventory')\gexec

SELECT 'CREATE DATABASE techhub_payments'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'techhub_payments')\gexec
