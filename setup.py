from setuptools import find_packages, setup

setup(
    name="lesson_generator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
        "google-generativeai",
        "pydantic",
    ],
)
