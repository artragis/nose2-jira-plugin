class JiraKnownIssueException(Exception):
    def __init__(self, issue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.issue = issue


def feed_from_string(mnemonics, *, description, **_):
    """
    Iter through string such as test docstring and extract all included jira issues.

    :param mnemonics: list of acceptable mnemonics
    :type mnemonics: iterable[str]
    :param description: string with extractable jira issues
    :return: iterable[str]
    """
    for mnemonic in mnemonics:
        if mnemonic + "-" in description:
            issue_key = mnemonic + '-'
            start_index = description.index(mnemonic) + len(mnemonic + '-')
            for i, current_char in enumerate(description[start_index:]):
                if not current_char.isdigit():
                    for other_issue in feed_from_string(mnemonics, description=description[start_index + i:]):
                        yield other_issue
                    break
                issue_key += current_char
            if issue_key[-1].isdigit():
                yield issue_key


def feed_from_exec_info(mnemonics, *, exec_info, **_):
    """
    extract jira issues from exception found in ``exec_info``. If this exception is instance of \
    ``JiraKnownIssueException`` or simply has a ``issue`` attribute, this will try to find all issues maching mnemonics.

    :param mnemonics: jira mnemonic key
    :param exec_info: the ``sys.exec_info()`` that test runner joined to the result when an error appears
    :return: iterable[str]
    """
    if exec_info and isinstance(exec_info, (list, tuple)) and len(exec_info) > 1:
        exception = exec_info[1]  # exception instance
        for issue_key in feed_from_string(mnemonics, description=getattr(exception, 'issue', '')):
            yield issue_key
