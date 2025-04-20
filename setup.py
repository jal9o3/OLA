from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("OLA/find_locations.pyx", language_level=3)
)
