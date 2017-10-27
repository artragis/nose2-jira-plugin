# nose2-jira-plugin
A nose2 test runner plugin to deal with jira bugtracker

# Quick start

Just install it with pip
```bash
# for now, no release is registered
pip install git+https://github.com/artragis/nose2-jira-plugin
```

Then add this configuration to your `unittest.cfg` or `nose2.cfg`

```ini
[jira]
actions = failed,In Qualification,write_failure_and_back_in_dev
          passed,In Qualification,write_success_comment
always-on = True
auth = basic
mnemonics = PROJ
password = password
regression_file = jira_regression.md
reporting_threads = 1
server = https://jira.com
user = user
```
