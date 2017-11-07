"""
This module gathers by default callbacks that can be called to handle test outcome.
A basic callback take three arguments : ``jira_plugin``, ``jira_issue``, ``test`` and  ``message``.

To add your own callback to the registry add them to your main file and decorate them with
``JiraRegistry.register(name, override_existing)``
"""
from nose2_contrib.jira.jira_plugin import JiraRegistry


def add_comment(jira_plugin, jira_issue, test, message, *, message_format):
    """
    Write comment to notify test success.

    :param jira_issue: the jira issue object
    :param test: the test case
    :param message: the success message
    :param message_format: the message format. As of 1.0 we use ``str.format`` syntax and accepted keys are ``test``
    and ``message``
    """
    if not jira_plugin.connected:
        return
    jira_plugin.jira_client.add_comment(jira_issue, message_format.format(test=test, message=message))
    jira_plugin.logger.info("Success comment sent to {jira_issue.id} for {test}".format(jira_issue=jira_issue,
                                                                                        test=test))

JiraRegistry.register('write_success_comment', False,
                      message_format="{test} has successed.")(add_comment)


def apply_jira_transition(jira_plugin, jira_issue, test, message, *, jira_transition, message_format):
    """
    report a failure to jira and send back to dev.

    :param jira_issue: the jira issue object
    :type jira_issue: jira.resources.Issue
    :param test: the testcase object
    :param message: the message to send to jira
    :param jira_transition: The transition to apply
    :param message_format: the transition message format. As of 1.0 we use ``str.format`` syntax and accepted keys are
    ``test`` and ``message``. To bypass "transition message submission" give ``None``
    """
    if not jira_plugin.connected:
        return
    if message_format:
        add_comment(jira_plugin, jira_issue, test, message, message_format=message_format)
    transition_id = jira_plugin.jira_client.find_transitionid_by_name(jira_issue, jira_transition)
    jira_plugin.jira_client.transition_issue(jira_issue, transition_id)


def register_transition(registration_name, jira_transition, transition_message_format):
    """
    register a transition to support for your test. Example, To send back a ticket to development you can probably use

    .. sourcecode:: python

        register_transition('write_failure_and_back_in_dev', 'Set as To Do', 'A failure was found by {test}:'
                                                                             'details: {message}')

    :param registration_name: the callback name as used in the configuration file.
    :param jira_transition: The transition to apply
    :param transition_message_format: the transition message format. As of 1.0 we use ``str.format`` syntax and accepted keys are
    ``test`` and ``message``
    :return: the registered callback
    """
    return JiraRegistry.register(registration_name, False, jira_transition=jira_transition,
                                 message_format=transition_message_format)(apply_jira_transition)


@JiraRegistry.register('do_nothing', False)
def do_nothing(jira_plugin, jira_issue, test, *_):
    """
    explicitly does nothing. It logs the date. This callback is usefull for debug purpose.

    :param jira_issue: the jira issue object
    :param test: the test case
    """
    jira_plugin.logger.info("did nothing for %(jira_issue)s and test %(test)s", jira_issue=jira_issue.id, test=test)


def warn_regression(jira_plugin, jira_issue, test, message, *, message_format):
    """
    Send a message to mark a regression. And add it to the ``jira_plugin.regressions`` list.

    :param jira_issue: the jira issue object
    :param test: test case
    :type test: unittest.TestCase
    :param message: the message to send
    :param message_format: the message format. As of 1.0 we use ``str.format`` syntax and accepted keys are ``test``
    and ``message``
    """
    from nose2_contrib.jira.jira_plugin import JiraRegression
    if not jira_plugin.connected:
        return

    jira_plugin.jira_client.add_comment(jira_issue, message_format.format(test=test, message=message))
    jira_plugin.regressions.append(JiraRegression(jira_issue.id, test, message))


JiraRegistry.register('warn_regression', False, message_format="Automated tests {test} found regression. Details :"
                                                               "{message}")(warn_regression)
