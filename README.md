# JIRA Linker SlackBot
A SlackBot that responds to messages that contain JIRA issue keys with a message that contains details about the JIRA issues. Runs in Amazon Lambda.

## Endpoint Usage Documentation
See https://ringrevenue.atlassian.net/wiki/display/QA/Lambda+Webhooks

## Development Environment Setup
This assumes you are on Mac OSX with Python 2.7 already installed:
* `virtualenv venv`
* `source venv/bin/activate`
* `pip install -r requirements_common.txt`
* `pip install -r requirements_test.txt`
* `pip install -r requirements_dev.txt`
* `aws help`
	* If you get an error running aws help about the six library, then:
	* `sudo rm -rf /System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/six.*`
* `aws configure`
	* Get AWS credentials with permission to deploy to Amazon Lambda

## Running tests
* Semaphore will run tests for you on each push
* Execute `python setup.py test` to run the tests locally

## Deployment
* Push to the master branch and Semaphore will automatically deploy the code for you
* If needed, run `./deploy.sh` to deploy the code from you local machine

## Lambda and API Gateway Configuration
* Exported configuration files are in the aws_config folder
* The config files are not automatically deployed
* If you make updates to the config directly in AWS, please export the settings and update this repo
