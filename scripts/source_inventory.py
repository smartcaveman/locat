#!/usr/bin/env python3
"""CRUD command-line interface for the source inventory database."""

import argparse
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "source_inventory.sqlite"
TABLES = {
    "category": "source_categories",
    "schema": "artifact_schemas",
    "source": "sources",
    "estimate": "source_magnitude_estimates",
}
WRITABLE_COLUMNS = {
    "source_categories": {"slug", "name", "description", "discovery_procedure"},
    "artifact_schemas": {"name", "version", "artifact_model", "traversal_protocol", "notes"},
    "sources": {
        "category_id",
        "schema_id",
        "name",
        "base_url",
        "discovery_procedure",
        "crawl_notes",
        "active",
    },
    "source_magnitude_estimates": {
        "source_id",
        "metric_name",
        "metric_value",
        "metric_unit",
        "estimate_kind",
        "provenance",
        "source_url",
        "observed_on",
    },
}


def connect(database):
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def parse_fields(field_values):
    fields = {}
    for field_value in field_values:
        key, separator, value = field_value.partition("=")
        if not separator or not key:
            raise argparse.ArgumentTypeError("Fields must use KEY=VALUE format.")
        fields[key] = value
    return fields


def validate_fields(table, fields):
    invalid_columns = set(fields) - WRITABLE_COLUMNS[table]
    if invalid_columns:
        raise SystemExit(f"Unknown or non-writable column(s): {', '.join(sorted(invalid_columns))}.")
    return fields


def list_records(connection, table):
    rows = connection.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()
    for row in rows:
        print(dict(row))


def get_record(connection, table, record_id):
    row = connection.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
    if row is None:
        raise SystemExit(f"No {table} record exists with id {record_id}.")
    print(dict(row))


def add_record(connection, table, fields):
    if not fields:
        raise SystemExit("At least one field is required.")
    columns = ", ".join(fields)
    placeholders = ", ".join("?" for _ in fields)
    cursor = connection.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", tuple(fields.values())
    )
    connection.commit()
    print(cursor.lastrowid)


def update_record(connection, table, record_id, fields):
    if not fields:
        raise SystemExit("At least one field is required.")
    assignments = ", ".join(f"{column} = ?" for column in fields)
    cursor = connection.execute(
        f"UPDATE {table} SET {assignments} WHERE id = ?",
        (*fields.values(), record_id),
    )
    if cursor.rowcount == 0:
        raise SystemExit(f"No {table} record exists with id {record_id}.")
    connection.commit()


def delete_record(connection, table, record_id):
    cursor = connection.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
    if cursor.rowcount == 0:
        raise SystemExit(f"No {table} record exists with id {record_id}.")
    connection.commit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List records.")
    list_parser.add_argument("entity", choices=TABLES)
    get_parser = subparsers.add_parser("get", help="Show one record.")
    get_parser.add_argument("entity", choices=TABLES)
    get_parser.add_argument("id", type=int)
    add_parser = subparsers.add_parser("add", help="Create a record.")
    add_parser.add_argument("entity", choices=TABLES)
    add_parser.add_argument("fields", nargs="+", help="Column values as KEY=VALUE.")
    update_parser = subparsers.add_parser("update", help="Update a record.")
    update_parser.add_argument("entity", choices=TABLES)
    update_parser.add_argument("id", type=int)
    update_parser.add_argument("fields", nargs="+", help="Column values as KEY=VALUE.")
    delete_parser = subparsers.add_parser("delete", help="Delete a record.")
    delete_parser.add_argument("entity", choices=TABLES)
    delete_parser.add_argument("id", type=int)
    args = parser.parse_args()

    table = TABLES[args.entity]
    with connect(args.database) as connection:
        if args.command == "list":
            list_records(connection, table)
        elif args.command == "get":
            get_record(connection, table, args.id)
        elif args.command == "add":
            add_record(connection, table, validate_fields(table, parse_fields(args.fields)))
        elif args.command == "update":
            update_record(connection, table, args.id, validate_fields(table, parse_fields(args.fields)))
        else:
            delete_record(connection, table, args.id)


if __name__ == "__main__":
    main()
