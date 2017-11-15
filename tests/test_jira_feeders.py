from unittest import TestCase

from nose2_contrib.jira.issue_feeders import feed_from_string
from sys import exc_info
from nose2_contrib.jira.issue_feeders import JiraKnownIssueException, feed_from_exec_info


class TestFeeders(TestCase):

    def test_docstring(self):
        docstring = """
        JIR-42/JIRA-24/JIR-25
        """
        mnemonics = ('JIR',)
        result = list(feed_from_string(mnemonics, description=docstring))
        self.assertEqual(2, len(result))
        self.assertIn('JIR-42', result)
        self.assertIn('JIR-25', result)

    def test_exec_info_with_jira_known_issues(self):
        try:
            raise JiraKnownIssueException('JIR-42/JIRA-24/JIR-25')
        except JiraKnownIssueException:
            info = exc_info()
        result = list(feed_from_exec_info(['JIR'], exec_info=info))
        self.assertEqual(2, len(result))
        self.assertIn('JIR-42', result)
        self.assertIn('JIR-25', result)

    def test_exec_info_with_basic_exception(self):
        try:
            raise ValueError('JIR-42/JIRA-24/JIR-25')
        except ValueError:
            info = exc_info()
        result = list(feed_from_exec_info(['JIR'], exec_info=info))
        self.assertEqual(0, len(result))
