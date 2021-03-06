from setuptools import setup

setup(
    name="mqtt2mysql",
    version="0.1.1",
    author="David Lorenzo",
    description="A tool to save all the MQTT messages on a MySQL/MariaDB database",
    long_description="Store all the MQTT messages of a broker on a MySQL/MariaDB database. "
                     "Whitelist and blacklist filters are available.",
    packages=["mqtt2mysql"],
    install_requires=["paho-mqtt", "pymysql", "python-dotenv"],
    entry_points={
        'console_scripts': ['mqtt2mysql=mqtt2mysql:run'],
    }
)
