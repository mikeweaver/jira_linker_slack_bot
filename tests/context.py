import pytest
from flexmock import flexmock
import json
import os
import sys
import unittest
import base64
import boto3

os.environ['ENCRYPTED_SLACK_CLIENT_SECRET'] = base64.encodestring('slack client secret')
os.environ['JIRA_PROJECT_KEYS'] = 'STORY|WEB'
os.environ['JIRA_SITE_URL'] = 'test.atlassian.net'
os.environ['ENCRYPTED_SLACK_CLIENT_ID'] = base64.encodestring('slack client id')
os.environ['ENCRYPTED_JIRA_API_TOKEN'] = base64.encodestring('test api token')
os.environ['ENCRYPTED_SLACK_OAUTH_ACCESS_TOKEN'] = base64.encodestring('test oauth token')
os.environ['ENCRYPTED_JIRA_USER_NAME'] = base64.encodestring('test user name')
os.environ['ENCRYPTED_SLACK_VERIFICATION_TOKEN'] = base64.encodestring('test verification token')

# mockout the KMS decryption
def decrypt_mock(CiphertextBlob):
    return {
        'Plaintext': CiphertextBlob
    }

mock_kms_client = flexmock(decrypt=decrypt_mock)
flexmock(boto3).should_receive('client').and_return(mock_kms_client)

sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('.'))

