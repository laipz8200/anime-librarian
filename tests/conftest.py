"""
Configuration for pytest.

This module sets up the test environment for all tests.
"""

import os
import sys

# Add the src directory to sys.path to import modules
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, src_path)

# This will be automatically imported by pytest before running tests
