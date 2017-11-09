from unittest import TestCase, mock

import logging
from jira.resources import Issue
from nose2_contrib.jira.callbacks import apply_jira_transition, register_transition
from nose2_contrib.jira.jira_plugin import JiraRegistry


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
        self.jira_plugin.logger = logging.getLogger(__name__)

    def test_warn_regression(self):
        callback = JiraRegistry.get('warn_regression')
        issue = Issue({}, None)
        issue.id = 'JIRA-42'
        callback(self.jira_plugin, issue, self, "a message")
        self.jira_plugin.jira_client.add_comment.assert_called_once_with(issue, mock.ANY)
        self.assertEqual(1, len(self.jira_plugin.regressions))
        self.assertEqual(self.jira_plugin.regressions[0].issue_id, issue.id)

    def test_send_success_message(self):
        callback = JiraRegistry.get('write_success_comment')
        issue = Issue({}, None)
        issue.id = 'JIRA-42'
        callback(self.jira_plugin, issue, self, "a message")
        self.jira_plugin.jira_client.add_comment.assert_called_once_with(issue, mock.ANY)
        self.assertEqual(0, len(self.jira_plugin.regressions))

    def test_apply_jira_transition(self):
        register_transition('write_failure_and_back_in_dev', 'Set as To Do', 'test={test} message={message}')
        callback = JiraRegistry.get('write_failure_and_back_in_dev')
        issue = Issue({}, None)
        issue.id = 'JIRA-42'
        callback(self.jira_plugin, issue, self, "a message")
        self.jira_plugin.jira_client.add_comment.assert_called_once_with(issue,
                                                                         'test={test} message={message}'.format(
                                                                             message='a message',
                                                                             test=self
                                                                         ))
        self.jira_plugin.jira_client.find_transitionid_by_name\
            .assert_called_once_with(issue, 'Set as To Do')
        self.jira_plugin.jira_client.transition_issue\
            .assert_called_once_with(issue, 1)
        self.assertEqual(0, len(self.jira_plugin.regressions))


class TestRegistry(TestCase):
    def setUp(self):

        JiraRegistry.register(self.id(), False)(lambda *args: args)
        self.base_function = JiraRegistry.get(self.id())

    def test_get_non_existing(self):
        self.assertRaises(KeyError, JiraRegistry.get, 'non_existing_callback')

    def test_try_to_add_existing(self):
        def add():
            def new_do_nothing(*_):
                pass

            return JiraRegistry.register(self.id(), False)(new_do_nothing)
        self.assertRaises(ValueError, add)
        self.assertEqual(self.base_function, JiraRegistry.get(self.id()))

    def test_override_existing(self):
        def add():
            def new_do_nothing(*_):
                pass

            return JiraRegistry.register(self.id(), True)(new_do_nothing)

        callback = add()
        self.assertEqual(callback, JiraRegistry.get(self.id()))
