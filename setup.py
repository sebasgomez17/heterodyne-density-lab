"""Setuptools bridge; metadata and requirements are in pyproject.toml."""
from setuptools import setup
setup(cffi_modules=["build_ffi.py:ffibuilder"])
