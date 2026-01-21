"""Setup script for GDHistogram."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="gdhistogram",
    version="1.0.0",
    author="GDHistogram Team",
    description="Google Docs Revision History Analyzer - Analyze typing behavior and detect anomalies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NagusameCS/GDHistogram",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Office Suites",
        "Topic :: Text Processing :: General",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "gdhistogram=gdhistogram.main:main",
        ],
        "gui_scripts": [
            "gdhistogram-gui=gdhistogram.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "gdhistogram": ["resources/*"],
    },
)
