import base64
import boto3
import httplib
import json
import logging
import os
import re
import urllib
import urllib2
from urlparse import parse_qs

# TODO: Docs
# TODO: CD/CI & tests
# TODO: Scrub message output in logs

kms = boto3.client('kms')
# Lambda doesn't allow commas in ENV variables, so I could not use a JSON array
JIRA_PROJECT_KEYS = os.environ['JIRA_PROJECT_KEYS'].split('|')
JIRA_SITE_URL = os.environ['JIRA_SITE_URL']
JIRA_USER_NAME =kms.decrypt(CiphertextBlob=base64.b64decode(os.environ['ENCRYPTED_JIRA_USER_NAME']))['Plaintext']
JIRA_API_TOKEN = kms.decrypt(CiphertextBlob=base64.b64decode(os.environ['ENCRYPTED_JIRA_API_TOKEN']))['Plaintext']
SLACK_VERIFICATION_TOKEN = kms.decrypt(CiphertextBlob=base64.b64decode(os.environ['ENCRYPTED_SLACK_VERIFICATION_TOKEN']))['Plaintext']
SLACK_CLIENT_ID = kms.decrypt(CiphertextBlob=base64.b64decode(os.environ['ENCRYPTED_SLACK_CLIENT_ID']))['Plaintext']
SLACK_CLIENT_SECRET = kms.decrypt(CiphertextBlob=base64.b64decode(os.environ['ENCRYPTED_SLACK_CLIENT_SECRET']))['Plaintext']
SLACK_OAUTH_ACCESS_TOKEN = kms.decrypt(CiphertextBlob=base64.b64decode(os.environ['ENCRYPTED_SLACK_OAUTH_ACCESS_TOKEN']))['Plaintext']
SILENCE_FOR_N_MESSAGES = int(os.environ.get('SILENCE_FOR_N_MESSAGES', 30))

OAUTH_URL='https://{0}/prod/oauth'
SLACK_API_URL = 'https://slack.com/api/{0}'
JIRA_ISSUE_API_URL = 'https://{0}/rest/api/2/issue/{1}'

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def respond_json(body=None, status_code='200'):
    return respond(body=json.dumps(body), status_code=status_code, content_type='application/json')

def respond(body=None, status_code='200', content_type=None):
    response = {
        'statusCode': status_code,
        'body': None,
        'headers': {}
    }
    if body:
        response['body'] = body

    if content_type:
        response['headers']['Content-Type'] = content_type

    return response

def post_slack_api_request(method, body):
    data = urllib.urlencode(body)
    print(data)
    request = urllib2.Request(SLACK_API_URL.format(method), data)
    request.add_header("Content-Type",'application/x-www-form-urlencoded')
    response = urllib2.urlopen(request)
    body = json.loads(response.read())
    return body['ok'], body

def post_slack_message_with_attachments(channel, thread_ts, attachments):
    api_request_body = {
        'token': SLACK_OAUTH_ACCESS_TOKEN,
        'channel': channel,
        'attachments': json.dumps(attachments)
    }
    if thread_ts:
        api_request_body['thread_ts'] = thread_ts

    print(json.dumps(api_request_body))
    _, api_response_body = post_slack_api_request('chat.postMessage', api_request_body)
    print(api_response_body)

def get_jira_issue(key):
    request = urllib2.Request(JIRA_ISSUE_API_URL.format(JIRA_SITE_URL, key))
    request.add_header('Content-Type', 'application/json')
    echoded_auth_header = base64.b64encode('{0}:{1}'.format(JIRA_USER_NAME, JIRA_API_TOKEN))
    request.add_header('Authorization', 'Basic {0}'.format(echoded_auth_header))
    try:
        response = urllib2.urlopen(request)
        return json.loads(response.read())
    except urllib2.HTTPError as e:
        return None

def remove_code_snippets(text):
    # slack represents code snippets with ```
    return re.compile('```((?!```).)*```', re.MULTILINE|re.DOTALL).sub('', text)

def upper_case_and_remove_duplicates(values):
    return set([value.upper() for value in values])

def get_jira_keys_excluding_code_snippets(text):
    return get_jira_keys(remove_code_snippets(text))

def get_jira_keys(text):
    keys = re.compile(
        '''(?:^|\s|_|-|"|'|,|>|/)((?:{0})[- _]\d+)'''.format('|'.join(JIRA_PROJECT_KEYS)),
        re.IGNORECASE
    ).findall(text)
    return upper_case_and_remove_duplicates(keys)

def handle_verification_event(event):
    response_body = {
        "challenge": event['challenge']
    }
    return respond_json(body=response_body)

def get_last_n_messages_from_channel(channel, timestamp, count):
    if channel[:1] == 'D':
        method = 'im.history'
    elif channel[:1] == 'G':
        method = 'groups.history'
    else:
        method = 'channels.history'

    api_request_body = {
        'token': SLACK_OAUTH_ACCESS_TOKEN,
        'channel': channel,
        'count': count,
        'latest': timestamp
    }

    success, api_response_body = post_slack_api_request(method, api_request_body)
    if success:
        return [message['text'] for message in api_response_body['messages'] if message.get('text')]
    else:
        print(api_response_body)
        print('Failed to get messages from the channel')
        return []

def exclude_keys_mentioned_in_the_last_n_messages(channel_id, timestamp, count, keys):
    remaining_keys = set(keys)
    if count <= 0:
        return remaining_keys

    for message_text in get_last_n_messages_from_channel(channel_id, timestamp, count):
        remaining_keys -= get_jira_keys_excluding_code_snippets(message_text)
        if len(remaining_keys) == 0:
            break
    if keys != remaining_keys:
        print('Removed {0} because they were mentioned in the previous {1} messages'.format(','.join(keys - remaining_keys), count))

    return remaining_keys

def attachment_for_jira_issue(key):
    issue = get_jira_issue(key)
    if issue:
        return {
            'text': '<https://{0}/browse/{1}|{1}> - `{2}`\n{3}'.format(JIRA_SITE_URL, key, issue['fields']['status']['name'], issue['fields']['summary']),
            'color': '#7CD197',
            'mrkdwn_in': ['text'],
            'fallback': 'https://{0}/browse/{1}'.format(JIRA_SITE_URL, key)
        }
    else:
        return None

def attachments_for_jira_issues(keys):
    attachments = []
    for key in keys:
        attachment = attachment_for_jira_issue(key)
        if attachment:
            attachments.append(attachment)
        else:
            print('No JIRA issue found for key {0}'.format(key))

    return attachments

def handle_message_event(event):
    if event.get('subtype') is not None:
        print('Ignoring non-standard message type {0}'.format(event.get('subtype')))
        return respond(status_code='204')

    keys = get_jira_keys_excluding_code_snippets(event['text'])
    if len(keys) > 0:
        print('Message contains JIRA Keys {0}'.format(','.join(keys)))
        keys = exclude_keys_mentioned_in_the_last_n_messages(event['channel'], event['ts'], SILENCE_FOR_N_MESSAGES, keys)
        if len(keys) > 0:
            attachments = attachments_for_jira_issues(keys)
            if len(attachments) > 0:
                post_slack_message_with_attachments(event['channel'], event.get('thread_ts'), attachments)
    else:
        print('Message does not contain a JIRA key, ignoring')

    return respond(status_code='204')

def handle_event(request):
    event = json.loads(request.get('body'))
    if event['token'] != SLACK_VERIFICATION_TOKEN:
        return respond(status_code='403')
    type = event['type']

    if type == 'event_callback' and event['event']['type'] == 'message':
        # ignore retry messages, we likely took longer than 3 seconds to respond
        # and are still processing the first message
        retry_num = request['headers'].get('X-Slack-Retry-Num')
        if retry_num and int(retry_num) > 0:
            return respond()
        else:
            return handle_message_event(event['event'])
    elif type == 'url_verification':
        return handle_verification_event(event)
    else:
        return respond_json(status_code='400')

def handle_install(request):
    host = request['headers']['Host']
    response_body = '''
        <html><body>
            <h2>Install JIRA Linker:</h2>
            <a href="https://slack.com/oauth/authorize?scope=chat:write:bot,channels:history,groups:history,im:history,mpim:history&client_id={0}&redirect_uri={1}">
                <img alt="Add to Slack" height="40" width="139" src="https://platform.slack-edge.com/img/add_to_slack.png" srcset="https://platform.slack-edge.com/img/add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x" />
            </a>
        </body></html>'''.format(SLACK_CLIENT_ID, OAUTH_URL.format(host))
    return respond(body=response_body, content_type='text/html')

def handle_oauth(request):
    host = request['headers']['Host']

    api_request_body = {
        'client_id': SLACK_CLIENT_ID,
        'client_secret': SLACK_CLIENT_SECRET,
        'code': request['queryStringParameters']['code'],
        'redirect_uri': OAUTH_URL.format(host)
    }

    success, api_response_body = post_slack_api_request('oauth.access', api_request_body)
    if success:
        response_body = '''
            <html><body>
                <h4>Access Token:</h4>
                <p>{0}</p>
                Copy this into the ENCRYPTED_SLACK_OAUTH_TOKEN environment variable in the Lambda function
            </body></html>'''.format(api_response_body['access_token'])
    else:
        response_body = '''
            <html><body>
                <h4>Failed to Get Access Token:</h4>
                <p>{0}</p>
            </body></html>'''.format(api_response_body['error'])

    return respond(body=response_body, content_type='text/html')

def lambda_handler(request, context):
    #print(json.dumps(request))
    path = (request.get('pathParameters') or {}).get('path')
    if path == 'event':
        return handle_event(request)
    elif path == 'install':
        return handle_install(request)
    elif path == 'oauth':
        return handle_oauth(request)
    else:
        return respond_json(status_code='404')
