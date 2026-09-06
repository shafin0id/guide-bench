from setuptools import setup, find_packages

setup(
    name="guide-bench",
    version="1.0.0",
    description="Universal Multi-Agent Systems Benchmarking Suite & Evaluation Harness",
    author="Shafin Ahmad",
    packages=find_packages(exclude=["tests*", "output*"]),
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.7.0",
        "litellm>=1.40.0",
        "scipy>=1.12.0",
        "numpy>=1.26.0",
        "pandas>=2.2.0",
        "tabulate>=0.9.0",
        "cryptography>=42.0.0",
        "typing-extensions>=4.10.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.23.0",
        ],
        "frameworks": [
            "crewai>=0.41.0",
            "langgraph>=0.1.0",
            "pyautogen>=0.2.27",
        ],
    },
    entry_points={
        "console_scripts": [
            "mas-bench=core.runner:main",
            "guide-bench=core.runner:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
