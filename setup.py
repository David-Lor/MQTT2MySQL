#!/usr/bin/env python

from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

setup(
    name="mqtt2mysql",
    version="1.0.1",
    author="David Lorenzo",
    description="A service to store all the sent MQTT messages on a MySQL/MariaDB database",
    packages=("mqtt2mysql",),
    install_requires=("aiomqtt", "aiomysql", "python-dotenv"),
    entry_points={
        'console_scripts': ['mqtt2mysql=mqtt2mysql:run'],
    },
    license="Apache 2.0",
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
)
