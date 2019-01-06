# plan_b
[![Build Status](https://travis-ci.org/vlanse/plan_b.svg?branch=master)](https://travis-ci.org/vlanse/plan_b)
[![codecov](https://codecov.io/gh/vlanse/plan_b/branch/master/graph/badge.svg)](https://codecov.io/gh/vlanse/plan_b)

Utility for mid and long-range planning of software releases. For now it only works with a Jira
as issues data source and outputs result as an xlsx file.

## Installation
[Install python 3.6](https://www.python.org/downloads/) and virtualenv package (`pip3.6 install virtualenv`).

```bash
git clone https://github.com/vlanse/plan_b.git && cd plan_b
make develop # virtualenv with installed dependencies will be created
```
plan_b script will be installed in virtualenv bin folder

## Usage
To use CLI you will first need configuration file. 
Sample configuration file is located [here](tests/cli/data/config-test.yml).
After configuration file is ready, CLI could be used like
```bash
plan_b --config=<path-to-config-file> --destination=<destination xlsx file path>
```
Sample plan created with example config (using mock Jira implementation)
could be downloaded [here](tests/cli/data/test.xlsx)

## Features to be done
* Service with REST API to enable easier sharing results with multiple people
* Web UI to allow people without technical expertise use the service
* Tracking of releases history as they progress to enable change management process
