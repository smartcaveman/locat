#!/usr/bin/env python3
"""Create and optionally seed the source inventory SQLite database."""

import argparse
import csv
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "source_inventory.sqlite"


def read_csv(filename):
    with (ROOT / "data" / filename).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def seed(connection):
    for row in read_csv("source_categories.csv"):
        connection.execute(
            """INSERT INTO source_categories (slug, name, description, discovery_procedure)
               VALUES (:slug, :name, :description, :discovery_procedure)
               ON CONFLICT(slug) DO UPDATE SET
                 name = excluded.name, description = excluded.description,
                 discovery_procedure = excluded.discovery_procedure""",
            row,
        )

    for row in read_csv("artifact_schemas.csv"):
        connection.execute(
            """INSERT INTO artifact_schemas
               (name, version, artifact_model, traversal_protocol, notes)
               VALUES (:name, :version, :artifact_model, :traversal_protocol, :notes)
               ON CONFLICT(name) DO UPDATE SET
                 version = excluded.version, artifact_model = excluded.artifact_model,
                 traversal_protocol = excluded.traversal_protocol, notes = excluded.notes""",
            row,
        )

    for row in read_csv("category_schemas.csv"):
        connection.execute(
            """INSERT INTO category_schemas (category_id, schema_id, is_default)
               VALUES (
                 (SELECT id FROM source_categories WHERE slug = ?),
                 (SELECT id FROM artifact_schemas WHERE name = ?), 1)
               ON CONFLICT(category_id, schema_id) DO UPDATE SET is_default = 1""",
            (row["category_slug"], row["schema_name"]),
        )

    for row in read_csv("sources.csv"):
        connection.execute(
            """INSERT INTO sources
               (category_id, schema_id, name, base_url, discovery_procedure, crawl_notes, active)
               VALUES (
                 (SELECT id FROM source_categories WHERE slug = :category_slug),
                 (SELECT id FROM artifact_schemas WHERE name = :schema_name),
                 :name, :base_url, :discovery_procedure, :crawl_notes, :active)
               ON CONFLICT(name) DO UPDATE SET
                 category_id = excluded.category_id, schema_id = excluded.schema_id,
                 base_url = excluded.base_url, discovery_procedure = excluded.discovery_procedure,
                 crawl_notes = excluded.crawl_notes, active = excluded.active""",
            row,
        )
        connection.execute(
            """INSERT INTO source_magnitude_estimates
               (source_id, metric_name, metric_value, metric_unit, estimate_kind,
                provenance, source_url, observed_on)
               VALUES (
                 (SELECT id FROM sources WHERE name = :name), :metric_name,
                 NULLIF(:metric_value, ''), :metric_unit, :estimate_kind, :provenance,
                 :source_url, :observed_on)
               ON CONFLICT(source_id, metric_name, observed_on) DO UPDATE SET
                 metric_value = excluded.metric_value, metric_unit = excluded.metric_unit,
                 estimate_kind = excluded.estimate_kind, provenance = excluded.provenance,
                 source_url = excluded.source_url""",
            row,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--no-seed", action="store_true", help="Create the schema without loading CSV data.")
    args = parser.parse_args()

    args.database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.database) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript((ROOT / "db" / "source_inventory.sql").read_text(encoding="utf-8"))
        if not args.no_seed:
            seed(connection)
    print(f"Initialized {args.database}")


if __name__ == "__main__":
    main()
