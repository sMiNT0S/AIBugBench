from setuptools import setup, find_packages

setup(
    name="ai-code-benchmark",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0",
        "requests>=2.25.0",
    ],
    author="AI Code Benchmark Team",
    description="Comprehensive AI code evaluation tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ai-code-benchmark",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
