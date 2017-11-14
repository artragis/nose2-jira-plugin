"""
This plugin connects to your jira bugtracker. Once a test outcomes a result, it tries to find out a jira issue.
If it's found, it takes advantage of ``asyncio`` facility to dial with Jira.

.. mermaid::

    sequenceDiagram
        participant runner
        participant testcase
        participant jira plugin
        participant event loop
        participant jira server
        runner->jira plugin: Instanciate
        loop test run
            runner->testcase: test
            testcase->runner: outcome result
            runner->jira plugin: here is the result
            jira plugin->testcase: give me your associated jira issue
            jira plugin-->event loop: process action on jira server
            event loo --> jira server: start dialing
        end
        runner->jira plugin: test run has ended
        jira plugin->event loop: finish all working report

"""
import concurrent
import json
import logging
from collections import namedtuple
from concurrent.futures.thread import ThreadPoolExecutor
from functools import wraps
from textwrap import dedent

import sys
from traceback import format_tb

from jira import JIRA
from pathlib import Path

from nose2.events import Plugin


class JiraAndResultAssociation(namedtuple('JiraAndResultAssociation', ['jira_status', 'test_result'])):
    """
    Maps the test run result (``nose2.result.FAIL``, ``nose2.result.PASS``, ``nose2.result.ERROR``,
    ``nose2.result.SKIP``) and jira ticket possible status (depending on your workflow) to the action the plugin must
    perform when those two statuses are given.

    To associate a "*NOOP*"" action with statuses just use `do_nothing` as callback to say it explicitely or just
    do not create an association
    """


class JiraRegression(namedtuple('JiraRegression', ['issue_id', 'test', 'failure_message'])):
    """
    Respesents a regression as found by the plugin. This allows to dump messages about resgressions into md file.
    """


class JiraMappingPlugin(Plugin):
    """
    :param regressions: a list of regressions (i.e the issues that the test run found and were already marked as fixed).
    :param jira_client: the active jira connection
    :param is_connected: if ``True`` marks the ``jira_client`` as currently active.
    """
    configSection = 'jira'
    alwaysOn = True
    connected = False

    def __init__(self):
        jira_server = self.config.as_str("server", "https://jira.com")
        jira_auth_method = self.config.as_str("auth", "basic")
        self.logger = logging.getLogger(__name__)

        if jira_auth_method.lower().strip() == "basic":
            auth_tuple = (self.config.as_str("user", "user"), self.config.as_str("password", "password"))
            self._connect(jira_server, basic_tuple=auth_tuple)
        else:
            cert_key_path = Path(self.config.as_str("key_file", "cert.key"))
            try:
                with cert_key_path.open(encoding="utf-8") as f:
                    key_value = f.read()
            except OSError:
                key_value = ""

            auth_dict = {

                'access_token': self.config.as_str("oauth_token", ""),
                'access_token_secret': self.config.as_str("oauth_secret", ""),
                'consumer_key': self.config.as_str("consumer_key", ""),
                'cert_key': key_value,
            }
            self._connect(jira_server, oauth_dict=auth_dict)
        status_association_list = self.config.as_list('actions', [])
        self.jira_status_result_callbacks = {}
        for status_association in status_association_list:
            try:
                test_status, jira_status, callback_name = status_association.strip().split(',', 2)
                callback = JiraRegistry.get(callback_name.strip(), False)
                self.jira_status_result_callbacks[JiraAndResultAssociation(jira_status, test_status)] = callback
            except AttributeError as e:
                print('Action does not exist on line {}. Error detail : {}'.format(status_association, e))
                exit(1)
            except KeyError as e:
                print(e)  # Key error is only for registry
                exit(1)
            except ValueError:
                print("Not enough argument in line {}. Expected test_status,jira_status,callback_name")
                exit(1)
        self.executor = ThreadPoolExecutor(max_workers=self.config.as_int("reporting_threads", 1))
        self.tasks = []
        self.mnemonics = self.config.as_list("mnemonics", [])
        self.regressions = []
        self.regression_report_path = self.config.as_str('regression_file', 'jira_regression.md')

    def _connect(self, jira_server, basic_tuple=None, oauth_dict=None):
        try:
            self.jira_client = JIRA(jira_server, oauth=oauth_dict, basic_auth=basic_tuple)
        except json.decoder.JSONDecodeError:
            sys.stderr.write('ERROR: Jira server {} is not available'.format(jira_server))
        else:
            self.connected = True

    def iter_jira_issues(self, doc):
        """
        Iter test documentation and extract all included jira issues.

        :param doc: test documentation
        :return: iterable[str]
        """
        for mnemonic in self.mnemonics:
            if mnemonic + "-" in doc:
                issue_key = mnemonic + '-'
                for current_char in doc[doc.index(mnemonic) + len(mnemonic + '-'):]:
                    if not current_char.isdigit():
                        break
                    issue_key += current_char
                yield issue_key

    def report(self, test, status, doc, message):
        """
        report the test to jira

        :param test: the executed test
        :param status: the result status taken in PASS or FAILURE
        :param doc: the doc/description
        :param message: the execution message
        """

        if doc and doc.strip():
            for jira_issue_key in self.iter_jira_issues(doc):

                issue = self.jira_client.issue(jira_issue_key, "status")
                type_of_report = JiraAndResultAssociation(issue.fields.status.name, status)
                if type_of_report not in self.jira_status_result_callbacks:
                    type_of_report = JiraAndResultAssociation('In Developpement', status)
                callback = self.jira_status_result_callbacks.get(type_of_report, JiraRegistry.get('do_nothing'))
                self.tasks.append(self.executor.submit(callback, self, issue, test, message))

    def testOutcome(self, event):
        """
        report test result to jira.

        :param event: the success event
        :type event: nose2.events.TestOutcomeEvent
        """
        message = """
        execution information : 
        {open}code{close}
        {exc_info}
        {open}code{close}
        stack trace 
        {open}code{close}
        {traceback}
        {open}code{close}
        
        """
        description = event.test._testMethodDoc or event.test.id()
        exc_inf = event.exc_info[1] if event.exc_info else ''
        _traceback = format_tb(event.exc_info[2]) if event.exc_info else ''
        self.report(event.test, event.outcome, description, message.format(exc_info=exc_inf,
                                                                           traceback=_traceback,
                                                                           open='{', close='}'))

    def afterSummaryReport(self, event):
        """
        ends the reporting to jira (blocking asyncio call).

        :param event: the report event
        :type event: nose2.events.ReportSummaryEvent
        """
        for future in concurrent.futures.as_completed(self.tasks):
            result = future.result()
            if result and "error" in result:
                logging.error("error=%s event=%s", result, event)
            else:
                logging.debug("reported %s", result)
        if self.regressions:
            with Path(self.regression_report_path).open('w', encoding='utf-8') as regression_file:
                for regression in self.regressions:
                    regression_md = dedent("""
                    # {issue}
                    
                    Regression was found by `{{test}}`. Debug info are : 
                    
                    ```
                    {message}
                    ```
                    
                    """.format(issue=regression.issue_id, test=regression.test, message=regression.failure_message))
                    regression_file.write(regression_md)


class JiraRegistry:
    """
    Register all available callbacks to report test results linked to Jira
    """
    registry = {}

    @classmethod
    def register(cls, name, override_existing=False, **kwargs):
        """
        register the callback to the given name. This name is the one that will be used in your configuration file.

        There are two ways to register a function :

        .. sourcecode:: python

            @JiraRegistry.register('the_name_in_conf_file')
            def my_own_callback(jira_plugin, jira_issue, test, message):
                pass

        In this way, ``register`` is used as a decorator. It returns a method with the wanted contract \
        (``jira_plugin, jira_issue, test, message``). If your method needs more args, you need to use kewords args.

        .. sourcecode:: python

            @JiraRegistry.register('the_name_in_conf_file', other_arg='value')
            def my_own_callback(jira_plugin, jira_issue, test, message, *, other_arg):
                pass

            # is equivalent to
            def my_own_callback(jira_plugin, jira_issue, test, message, *, other_arg):
                pass
            JiraRegistry.register('the_name_in_conf_file', other_arg='value')(my_own_callback)

        :param name: the callback name as used in the configuration file.
        :param override_existing: if ``True`` this will overrides any callback mapped to ``name``. If ``False`` the \
        method rises ``ValueError`` if ``name`` already exists.

        :return: the registered wrapper
        """
        if name in cls.registry and not override_existing:
            raise ValueError('{} is already registered, cannot override it.'.format(name))

        def register_wrapper(func):

            @wraps(wrapped=func)
            def real_func(jira_plugin, jira_issue, test, message):
                return func(jira_plugin, jira_issue, test, message, **kwargs)
            cls.registry[name] = real_func
            return real_func

        return register_wrapper

    @classmethod
    def get(cls, name, raise_on_failure=True):
        if name not in cls.registry and raise_on_failure:
            raise KeyError("{} does not exist, please register it.".format(name))
        elif name not in cls.registry:
            print('{} is not yet registered, wrap arround "do_nothing" for now.'.format(name))
            from .callbacks import do_nothing
            cls.register(name)(do_nothing)
        return cls.registry[name]
