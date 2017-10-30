"""
This module gathers by default callbacks that can be called to handle test outcome.
A basic callback take three arguments : ``jira_plugin``, ``jira_issue``, ``test`` and  ``message``.

To add your own callback to the registry add them to your main file and decorate them with
``JiraRegistry.register(name, override_existing)``
"""


class JiraRegistry:
    registry = {}

    @classmethod
    def register(cls, name, override_existing=False):
        if name in cls.registry and not override_existing:
            raise ValueError('{} is already registered, cannot override it.'.format(name))

        def register_wrapper(func):
            cls.registry[name] = func
            return func

        return register_wrapper

    @classmethod
    def get(cls, name):
        if name not in cls.registry:
            raise KeyError("{} does not exist, please register it.".format(name))
        return cls.registry[name]


def write_success_comment(jira_plugin, jira_issue, test, message):
    """
    Write comment to notify test success.

    :param jira_issue: the jira issue object
    :param test: the test case
    :param message: the success message
    """
    if not jira_plugin.connected:
        return
    jira_plugin.jira_client.add_comment(jira_issue, message)
    jira_plugin.logger.info("Success comment sent to {jira_issue.id} for {test}".format(jira_issue=jira_issue, test=test))


def write_failure_and_back_in_dev(jira_plugin, jira_issue, test, message):
    """
    report a failure to jira and send back to dev.

    :param jira_issue: the jira issue object
    :type jira_issue: jira.resources.Issue
    :param test: the testcase object
    :param message: the message to send to jira
    """
    if not jira_plugin.connected:
        return
    jira_plugin.jira_client.add_comment(jira_issue, "Automated tests {} failed with messages :\n {}".format(test, message))
    jira_plugin.logger.info("Failure comment sent to {jira_issue.id} for {test}".format(jira_issue=jira_issue, test=test))
    transition_id = jira_plugin.jira_client.find_transitionid_by_name(jira_issue, 'Set as To Do')
    jira_plugin.jira_client.transition_issue(jira_issue, transition_id)


def do_nothing(jira_plugin, jira_issue, test, *_):
    """
    explicitly does nothing. It logs the date. This callback is usefull for debug purpose.

    :param jira_issue: the jira issue object
    :param test: the test case
    """
    jira_plugin.logger.info("did nothing for %(jira_issue)s and test %(test)s", jira_issue=jira_issue.id, test=test)


@JiraRegistry.register('warn_regression', False)
def warn_regression(jira_plugin, jira_issue, test, message):
    """
    Send a message to mark a regression.

    :param jira_issue: the jira issue object
    :param test: test case
    :type test: unittest.TestCase
    :param message: the message to send
    """
    from nose2_contrib.jira.jira_plugin import JiraRegression
    if not jira_plugin.connected:
        return
    jira_plugin.jira_client.add_comment(jira_issue, "Automated tests {} found "
                                        "regression with messages :\n {}".format(test, message))
    jira_plugin.regressions.append(JiraRegression(jira_issue.id, test, message))
