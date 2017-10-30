from unittest import TestCase, mock

from jira.resources import Issue
from nose2_contrib.jira.callbacks import JiraRegistry


class TestCallbacks(TestCase):
    def setUp(self):
        self.jira_plugin = mock.patch('nose2_contrib.jira_plugin.JiraMappingPlugin')
        self.jira_plugin.jira_client = mock.patch('jira.JIRA')
        self.jira_plugin.jira_client.add_comment = mock.MagicMock()
        self.jira_plugin.jira_client.find_transitionid_by_name = mock.MagicMock()
        self.jira_plugin.jira_client.find_transitionid_by_name.return_value = 1
        self.jira_plugin.jira_client.transition_issue = mock.MagicMock()
        self.jira_plugin.regressions = []
        self.jira_plugin.connected = True

    def test_warn_regression(self):
        callback = JiraRegistry.get('warn_regression')
        issue = Issue({}, None)
        issue.id = 'JIRA-42'
        callback(self.jira_plugin, issue, self, "a message")
        self.jira_plugin.jira_client.add_comment.assert_called_once_with(issue, mock.ANY)
        self.assertEqual(1, len(self.jira_plugin.regressions))
        self.assertEqual(self.jira_plugin.regressions[0].issue_id, issue.id)
