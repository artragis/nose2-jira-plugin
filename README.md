[![Codacy Badge](https://api.codacy.com/project/badge/Grade/bf7ddfd842fa4ef3b2d50c4ea052ed56)](https://www.codacy.com/app/artragis/nose2-jira-plugin?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=artragis/nose2-jira-plugin&amp;utm_campaign=Badge_Grade)
[![Documentation Status](https://readthedocs.com/projects/artragis-nose2-jira-plugin/badge/?version=latest)](https://artragis-nose2-jira-plugin.readthedocs-hosted.com/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://travis-ci.org/artragis/nose2-jira-plugin.svg?branch=master)](https://travis-ci.org/artragis/nose2-jira-plugin)

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
