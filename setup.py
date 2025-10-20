from setuptools import setup, find_packages
import os

# Read README for long description
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="pfapi",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy>=2.0.0",
        "pandas>=2.0.0",
        "matplotlib>=3.0.0",
    ],
    # extras_require={
    #     "dev": [
    #         "ipykernel>=6.0.0",
    #         "ipython>=9.0.0",
    #         "jupyter>=1.0.0",
    #     ],
    # },
    author="Martin Valencic",
    author_email="",
    description="A Python interface for building admittance matrices from PowerFactory network models for stability analysis.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/valenciaga1231/PFAPI",
    project_urls={
        "Bug Tracker": "https://github.com/valenciaga1231/PFAPI/issues",
        "Source Code": "https://github.com/valenciaga1231/PFAPI",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    keywords="powerfactory power-systems admittance-matrix stability-analysis",
)