PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS source_categories (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    discovery_procedure TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifact_schemas (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    version TEXT NOT NULL DEFAULT '1',
    artifact_model TEXT NOT NULL,
    traversal_protocol TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS category_schemas (
    category_id INTEGER NOT NULL REFERENCES source_categories(id) ON DELETE CASCADE,
    schema_id INTEGER NOT NULL REFERENCES artifact_schemas(id) ON DELETE RESTRICT,
    is_default INTEGER NOT NULL DEFAULT 0 CHECK (is_default IN (0, 1)),
    PRIMARY KEY (category_id, schema_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS one_default_schema_per_category
    ON category_schemas(category_id) WHERE is_default = 1;

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES source_categories(id) ON DELETE RESTRICT,
    schema_id INTEGER NOT NULL REFERENCES artifact_schemas(id) ON DELETE RESTRICT,
    name TEXT NOT NULL UNIQUE,
    base_url TEXT NOT NULL UNIQUE,
    discovery_procedure TEXT NOT NULL DEFAULT '',
    crawl_notes TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS source_magnitude_estimates (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    metric_unit TEXT NOT NULL,
    estimate_kind TEXT NOT NULL CHECK (estimate_kind IN ('estimate', 'published')),
    provenance TEXT NOT NULL,
    source_url TEXT NOT NULL DEFAULT '',
    observed_on TEXT NOT NULL DEFAULT '',
    UNIQUE (source_id, metric_name, observed_on)
);

CREATE INDEX IF NOT EXISTS sources_by_category ON sources(category_id);
CREATE INDEX IF NOT EXISTS estimates_by_source ON source_magnitude_estimates(source_id);
