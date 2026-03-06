"""Setup script for AI Daily Digest CLI tool."""

from setuptools import setup, find_packages

setup(
    name="ai-daily-digest",
    version="1.0.0",
    description="Daily AI news aggregation CLI tool",
    author="AI Daily Digest Team",
    python_requires=">=3.11",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.31,<3",
        "feedparser>=6.0,<7",
        "beautifulsoup4>=4.12,<5",
        "lxml>=5.0,<6",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4,<8",
            "ruff>=0.1,<1",
        ],
    },
    entry_points={
        "console_scripts": [
            "ai-digest=cli.__main__:main",
        ],
    },
)
