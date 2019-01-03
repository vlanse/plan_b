# PLAN_B
Utility for mid and long-range planning of software releases. For now it only works with a Jira
as issues data source and outputs result as an xlsx file.

## Installation
[Install python 3.6](https://www.python.org/downloads/) and virtualenv package (`pip3.6 install virtualenv`).

```bash
git clone https://github.com/vlanse/plan_b.git && cd plan_b
virtualenv -p python3.6 env; . env/bin/activate;
pip install -Ue .
```

## Usage
To use CLI you will first need configuration file. 
Sample configuration file is located at `tests/data/config-test.yml`
After configuration file is ready, CLI could be used like
```bash
cli --config=<path-to-config-file>
```

## Features to be done
* Service with REST API to enable easier sharing results with multiple people
* Web UI to allow people without technical expertise use the service
* Tracking of releases history as they progress to enable change management process
