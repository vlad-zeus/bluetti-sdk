"""Setup script for Power SDK."""

import os

from setuptools import find_packages, setup

# Read long description from README
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_path):
    with open(readme_path, encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "Protocol-agnostic device control SDK"

setup(
    name="power-sdk",
    version="2.0.0",
    author="Zeus Fabric Team",
    author_email="",
    description="Protocol-agnostic device control SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/power-sdk",
    packages=find_packages(exclude=["tests", "tests.*", "tools", "docs"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Home Automation",
        "Topic :: System :: Hardware",
    ],
    python_requires=">=3.8",
    install_requires=[
        "paho-mqtt>=1.6.0",
        "cryptography>=3.4",
        "PyYAML>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.950",
        ],
    },
    # CLI tools coming in v2.1.0
    # entry_points={
    #     "console_scripts": [
    #         "power-cli=power_sdk.cli:main",
    #     ],
    # },
)


