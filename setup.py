from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nw_stats",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="SNWK Competition Data Collection and Statistics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "lxml>=4.9.0",
    ],
    extras_require={
        "dashboard": [
            "streamlit>=1.25.0",
            "plotly>=5.10.0",
            "matplotlib>=3.5.0",
            "seaborn>=0.11.0",
        ],
        "notebooks": [
            "jupyter>=1.0.0",
            "ipykernel>=6.15.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "mypy>=1.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
        "all": [
            "streamlit>=1.25.0",
            "plotly>=5.10.0",
            "matplotlib>=3.5.0",
            "seaborn>=0.11.0",
            "jupyter>=1.0.0",
            "ipykernel>=6.15.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "nw-scrape=nw_stats.data_collection.scrape_data:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="nosework, competition, statistics, data-analysis, web-scraping",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/nw_stats/issues",
        "Source": "https://github.com/yourusername/nw_stats",
    },
)