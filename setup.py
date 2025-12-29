"""
Setup configuration for Context Management System.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="context-management-system",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Production-grade Context Management System for LLM Applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/context-management-system",
    packages=find_packages(exclude=["tests", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cms=cms.cli:main",  # Optional CLI tool
        ],
    },
    include_package_data=True,
    package_data={
        "cms": ["config/*.yaml"],
    },
)
