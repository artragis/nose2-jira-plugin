================
Customize plugin
================

Callback registration
---------------------

.. autoclass:: nose2_contrib.jira.jira_plugin.JiraRegistry
    :members:

Default callbacks
-----------------

.. automodule:: nose2_contrib.jira.callbacks

Create and use your own callbacks
---------------------------------

You can add your own set of callbacks to the plugin. As an example, let's imagine you want to "reopen" an issue when
a regression is found.

Basically the ``nose2_contrib.jira.callbacks`` provides you two function that you have to compose to perform this :

``warn_regression`` and ``apply_jira_transition``.

Assuming you configured your Jira with the "reopen" action called ``Reopen`` your custom callback can look like:

.. sourcecode:: python

    from nose2_contrib.jira.callbacks import warn_regression, apply_jira_transition
    from nose2_contrib.jira.jira_plugin import JiraRegistry

    @JiraRegistry.register('reopen_on_regression')
    def reopen_jira_issue_on_regression(jira_plugin, jira_issue, test, message):
        regression_message = 'A regression was found by {test}.\n\nSee details:\n\t {message}'
        warn_regression(jira_plugin, jira_issue, test, message, message_format=regression_message)
        apply_transition(jira_plugin, jira_issue, test, message, message_format=None, jira_transition='Reopen')

You now just have to put this code on the ``__init__.py`` file of your test package and add a this configuration statements
in your ``unittest.cfg`` file

.. sourcecode::

    [jira]
    actions = failed,Closed,reopen_on_regression
              error,Closed,reopen_on_regression
    always-on = True
    auth = basic
    mnemonics =
    password = password
    regression_file = jira_regression.md
    reporting_threads = 1
    server = https://jira.com
    user = user