from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements/base.txt", encoding="utf-8") as fh:
    install_requires = fh.read().splitlines()

setup(
    name="itbase",
    version="0.1.0",
    author="ITBase Team",
    author_email="support@itbase.example.com",
    description="IT Asset Management System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LelikTrue/ITBase-",
    packages=find_packages(exclude=["tests*"]),
    package_data={"app": ["py.typed"]},
    python_requires=">=3.12",
    install_requires=install_requires,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: FastAPI",
        "Topic :: Office/Business",
        "Topic :: System :: Systems Administration",
    ],
)
