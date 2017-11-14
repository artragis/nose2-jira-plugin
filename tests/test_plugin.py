from unittest import TestCase
from unittest.mock import MagicMock
import nose2
import sys
from nose2_contrib.jira.issue_feeders import JiraKnownIssueException
from nose2_contrib.jira.jira_plugin import JiraMappingPlugin


class TestPlugin(TestCase):
    def setUp(self):
        mocked_issue = MagicMock()
        mocked_issue.fields = MagicMock()
        mocked_issue.fields.status = MagicMock()
        mocked_issue.fields.status.name = 'JIR-42'

        self.plugin = JiraMappingPlugin()
        self.plugin.mnemonics = ['JIR']
        self.plugin.connected = True
        self.plugin.jira_client = MagicMock()
        self.plugin.jira_client.issue = MagicMock()
        self.plugin.jira_client.issue.return_value = mocked_issue

    def test_report(self):
        try:
            raise JiraKnownIssueException('JIR-42')
        except JiraKnownIssueException:
            event = nose2.events.TestOutcomeEvent(self, None, 'error',
                                                  exc_info=sys.exc_info())
        self.plugin.testOutcome(event)
        self.assertEqual(1, len(self.plugin.tasks))