# JIRA Linker SlackBot
A SlackBot that responds to messages that contain JIRA issue keys with a message that contains details about the JIRA issues. Runs in Amazon Lambda.

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
* Execute `python setup.py test` to run the tests locally

## Deployment
* Run `./deploy.sh` to deploy the code from your local machine to an existing Amazon Lambda function

## Install and Configuration

### Create the Lambda Function
* Create a new Lambda function
* Choose the Blank Function template
* Skip choosing a trigger
* Name it JIRALinkerSlackBot
* Choose Python 2.7 as the runtime
* Copy/paste the code from jira_linker_slack_bot.py into the code edit box
* Enter lambda_function.lambda_handler for the Handler function
* Set the Timeout to 10 seconds
* Role
    * Create new role from template
    * Name it JIRALinkerSlackBot
    * Choose Simple Microservice permissions from the policy templates
* Create a KMS key called JIRALinkerSlackBot and choose it
* Click through the wizard to save it
* Click on the Function
* Copy the ARN from the upper right corner of the UI

### Create the API Gateway
* Import the API
    * Edit the swagger file and paste the ARN from the Lambda function into the swagger file where it says PASTE_ARN_HERE
    * Create a new API
    * Choose Import from Swagger
    * Select the swagger file in the aws_config folder of this project
    * Click Import
* Grant Invoke Permissions
    * Click on the JIRA Linker API
    * Click on Resources
    * Click on ANY
    * Click on Integration Request
    * Click the pencil icon to the right of the Lambda function
    * Click the check icon
    * You will see a pop-up asking you to grant permissions for the API gateway to invoke your Lambda function. Click OK.
* Deploy the API
    * From Actions choose Deploy
    * Choose New Stage
    * Name the stage prod
    * Click Deploy
    * Copy the Invoke URL
* Add a Lambda trigger
    * Navigate to your Lambda function
    * Click on Triggers
    * Click on Add a Trigger
    * Click on the empty box icon and choose API Gateway
    * Choose the JIRA Linker API
    * Set Security to Open

### Create the Slack App
* Navigate to https://api.slack.com/apps and click Create New App
* Name the app JIRA Linker
* OAuth & Permissions
    * Enter the URL for your API gateway into the Redirect URLs edit box
* Bot User
    * Create a bot user named "jira_linker"

### Configure the Lambda Function
* Create environment variables from data in your slack and JIRA config
    * JIRA_PROJECT_KEYS: STORY|BUG
    * JIRA_SITE_URL: yourdomain.atlassian.net
    * ENCRYPTED_JIRA_USER_NAME
    * ENCRYPTED_JIRA_API_TOKEN
    * ENCRYPTED_SLACK_CLIENT_SECRET
    * ENCRYPTED_SLACK_CLIENT_ID
    * ENCRYPTED_SLACK_VERIFICATION_TOKEN
    * ENCRYPTED_SLACK_OAUTH_ACCESS_TOKEN: Leave this blank for now
* Encrypt the ENCRYPTED_* environment variables:
    * Choose Enable Encryption Helpers
    * Choose the JIRALinkerSlackBot encryption key
    * Click Encrypt next to each ENCRYPTED_* environment variable

### Configure Slack Events
* Event Subscriptions
    * Enter https://YOURAPIGATEWAY/prod/event as the Request URL
    * Choose the following Team Events:
        * message.channels
        * message.groups
        * message.im
        * message.mpim
    * Save
    * Enable events

### Install in your Slack Organization
* Navigate to https://YOURAPIGATEWAY/prod/install
* Click the Add to Slack button and follow the prompts
* Copy the OAuth token into the ENCRYPTED_SLACK_OAUTH_ACCESS_TOKEN environment variable in the Lambda function
* Choose Enable Encryption Helpers
* Choose the JIRALinkerSlackBot encryption key
* Click Encrypt the ENCRYPTED_SLACK_OAUTH_ACCESS_TOKEN environment variable
