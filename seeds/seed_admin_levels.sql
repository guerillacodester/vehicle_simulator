-- Insert 4 admin levels with proper Strapi v5 structure
-- Uses ON CONFLICT to prevent duplicate inserts
INSERT INTO admin_levels (
    document_id,
    level,
    name,
    description,
    locale,
    published_at,
    created_at,
    updated_at
) VALUES
(
    gen_random_uuid(),
    6,
    'Parish',
    'First-level administrative division (Parishes)',
    'en',
    NOW(),
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    8,
    'Town',
    'Town-level administrative boundary',
    'en',
    NOW(),
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    9,
    'Suburb',
    'Suburb or neighborhood district',
    'en',
    NOW(),
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    10,
    'Neighbourhood',
    'Small neighborhood or locality',
    'en',
    NOW(),
    NOW(),
    NOW()
)
ON CONFLICT (level) DO NOTHING;

-- Verify
SELECT id, level, name, locale, published_at IS NOT NULL as published FROM admin_levels ORDER BY level;
