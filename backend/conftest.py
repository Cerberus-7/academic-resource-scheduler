"""Pytest bootstrap.

Settings requires SECRET_KEY. Tests use a throwaway, test-only key so the
suite runs on a fresh clone without a real backend/.env. Real environment
variables are not overridden.
"""
import os

os.environ.setdefault("SECRET_KEY", "test-only-key-not-a-real-secret-0123456789abcdef")
