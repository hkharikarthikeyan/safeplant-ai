"""
Pytest configuration and fixtures for SafePlant AI tests.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    """Create test Flask application."""
    os.environ["FLASK_ENV"] = "testing"
    test_app = create_app("testing")
    yield test_app


@pytest.fixture(scope="session")
def db(app):
    """Create database for testing."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture(scope="function")
def db_session(db, app):
    """Create a fresh database session for each test."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        db.session.bind = connection
        yield db.session
        db.session.remove()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="session")
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture(scope="session")
def generated_data(app, db):
    """Generate starter dataset once for all tests."""
    with app.app_context():
        from app.generators.master_generator import generate_all
        counts = generate_all(mode="starter", seed=20261022, run_id="TEST-RUN-001")
        db.session.commit()
        yield counts
