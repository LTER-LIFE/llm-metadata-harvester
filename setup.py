from setuptools import setup, find_packages

setup(
    name="llm_metadata_harvester",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "openai",
        "google",
        "python-dotenv",
        "tqdm",
        "tiktoken",
        "requests",
        "beautifulsoup4",
        "playwright",
        "nest_asyncio",
        "pyyaml",
    ],
    python_requires=">=3.8",
)