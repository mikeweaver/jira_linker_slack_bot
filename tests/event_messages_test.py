from context import *
from jira_linker_slack_bot import lambda_handler
from StringIO import StringIO
import time
import urllib2

class TestEventMessages(unittest.TestCase):

    def get_fixture(self, fixture_name):
        with open('./tests/fixtures/{0}.json'.format(fixture_name)) as json_data:
            return json.load(json_data)

    def assert_empty_response(self, response):
        self.assertIsNone(response['body'])
        self.assertEqual(response['statusCode'], '204')

    def test_event_message(self):
        slack_get_history_response = StringIO(json.dumps(self.get_fixture('slack_get_history_response')))
        jira_issue_response = StringIO(json.dumps(self.get_fixture('jira_get_issue_response')))
        slack_post_message_response = StringIO(json.dumps(self.get_fixture('slack_post_message_response')))
        flexmock(urllib2).should_receive('urlopen').and_return(slack_get_history_response).and_return(jira_issue_response).and_return(slack_post_message_response)

        request = self.get_fixture('slack_event_message_request')
        response = lambda_handler(request, None)
        self.assert_empty_response(response)
