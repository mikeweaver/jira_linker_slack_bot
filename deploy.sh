rm -f deploy.zip
zip -r deploy.zip *.py
aws lambda update-function-code --function jira_linker_slack_bot --publish --zip-file fileb://deploy.zip
rm -f deploy.zip
