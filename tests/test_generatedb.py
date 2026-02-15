import os
from unittest.mock import MagicMock, patch

import pytest

import generatedb


def test_setup_database_removes_existing():
    """Test that setup_database removes the existing database file if it exists."""
    with (
            patch("generatedb.os.path.exists") as mock_exists,
            patch("generatedb.os.remove") as mock_remove,
            patch("generatedb.sqlite3.connect") as mock_connect,
    ):
        # Configure mocks
        mock_exists.return_value = True
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Patch DB_FILE
        original_db_file = generatedb.DB_FILE
        generatedb.DB_FILE = "dummy_path.sqlite3"

        try:
            generatedb.setup_database()

            # Verify os.remove was called with the correct path
            mock_exists.assert_called_with("dummy_path.sqlite3")
            mock_remove.assert_called_with("dummy_path.sqlite3")

        finally:
            generatedb.DB_FILE = original_db_file


def test_setup_database_does_not_remove_non_existing():
    """Test that setup_database does NOT remove the database file if it does not exist."""
    with (
            patch("generatedb.os.path.exists") as mock_exists,
            patch("generatedb.os.remove") as mock_remove,
            patch("generatedb.sqlite3.connect") as mock_connect,
    ):
        # Configure mocks
        mock_exists.return_value = False
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Patch DB_FILE
        original_db_file = generatedb.DB_FILE
        generatedb.DB_FILE = "dummy_path.sqlite3"

        try:
            generatedb.setup_database()

            # Verify os.remove was NOT called
            mock_exists.assert_called_with("dummy_path.sqlite3")
            mock_remove.assert_not_called()

        finally:
            generatedb.DB_FILE = original_db_file


def test_setup_database_creates_schema(tmp_path):
    """Test that setup_database creates the correct tables and schema."""
    db_file = tmp_path / "test_whoistel.sqlite3"

    # Patch DB_FILE
    original_db_file = generatedb.DB_FILE
    generatedb.DB_FILE = str(db_file)

    try:
        # Call setup_database
        conn = generatedb.setup_database()
        conn.close()

        # Verify file exists
        assert db_file.exists()

        # Connect to verify schema
        verify_conn = generatedb.sqlite3.connect(str(db_file))
        cursor = verify_conn.cursor()

        # Verify Tables
        tables = [
            "PlagesNumerosGeographiques",
            "PlagesNumeros",
            "Operateurs",
            "Communes",
        ]

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            assert table in existing_tables, f"Table {table} not created"

        # Verify Columns for PlagesNumerosGeographiques
        cursor.execute("PRAGMA table_info(PlagesNumerosGeographiques);")
        columns_geo = {row[1] for row in cursor.fetchall()}
        expected_geo = {"PlageTel", "CodeOperateur", "CodeInsee"}
        assert expected_geo.issubset(columns_geo), (
            f"Missing columns in PlagesNumerosGeographiques: {expected_geo - columns_geo}"
        )

        # Verify Columns for Communes
        cursor.execute("PRAGMA table_info(Communes);")
        columns_communes = {row[1] for row in cursor.fetchall()}
        expected_communes = {
            "CodeInsee",
            "NomCommune",
            "CodePostal",
            "NomDepartement",
            "Latitude",
            "Longitude",
        }
        assert expected_communes.issubset(columns_communes), (
            f"Missing columns in Communes: {expected_communes - columns_communes}"
        )

        verify_conn.close()

    finally:
        generatedb.DB_FILE = original_db_file
