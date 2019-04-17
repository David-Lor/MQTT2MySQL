# MQTT2MongoDB

A simple Python project that listen to one or more MQTT topics and save all the incoming messages on a MySQL/MariaDB database, as some sort of logger.

## Requirements

- Python 3.x (tested on 3.7)
- A running MQTT broker
- A working MySQL/MariaDB server, with a database created and permissions to create tables and insert data on it
- Libraries:
    * [pymysql](https://github.com/PyMySQL/PyMySQL)
    * [paho-mqtt](https://pypi.org/project/paho-mqtt)
- Docker recommended if available - you can use the [Python Autoclonable App Docker image](https://hub.docker.com/r/davidlor/python-autoclonable-app)
- Tested under Linux only

## Settings

Settings for both MQTT client and MySQL/MariaDB database server must be properly set using env variables or using .env files.
The full list of variables is located on the `sample.env` file, which can be modified to customize these settings.

If you want to set these variables through this file, it must be renamed to `.env`.
Otherwise, just set them as system env variables (recommended when using Docker).

Python modules include fallback default values in case env-variable values are not defined, or a `.env` file is not available, which are the same as showing on the `sample.env` file.
However, `SQL_USER`, `SQL_DATABASE` and `SQL_PASSWORD` don't have default values and must be defined.

## Installing

### Using Docker and the Python Autoclonable App image

This is the most preferred way to run MQTT2MySQL, if Docker is available.

```bash
docker run -d -e GIT_REPOSITORY:https://github.com/David-Lor/MQTT2MySQL.git -e SQL_USER:root -e SQL_PASS:1234 -e SQL_DATABASE:mqtt --name mqtt2mysql davidlor/python-autoclonable-app
```
IMPORTANT: Set all the required env variables with the `-e` option, following the examples provided above.

### Without Docker, without installing

This is the most preferred way to run MQTT2MySQL, if Docker is unavailable.

```bash
git clone https://github.com/David-Lor/MQTT2MySQL.git

# Rename and modify the .env file
mv MQTT2MySQL/sample.env MQTT2MySQL/.env
nano MQTT2MySQL/.env

# Run the app
python MQTT2MySQL
```
IMPORTANT: Rename the `sample.env` file to `.env` and properly et the variables inside.

### Without Docker, installing

This has not been tested.

```bash
git clone https://github.com/David-Lor/MQTT2MySQL.git

# Set your env variables system-wide

# Install
cd MQTT2MySQL
python setup.py install

# Run
mqtt2mysql
```

## Changelog

- 0.1.0 - Initial version
- 0.1.1 - New parameter to set the queue processing frequency; Show complete traceback when a message can't be inserted on the database; Switch timestamp to SQL Datetime datatype on "messages" SQL view

## TODO

- Connect to SSL-enabled MQTT brokers with certificate
