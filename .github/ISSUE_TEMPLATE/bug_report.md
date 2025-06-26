---
name: Bug report
about: Create a report to help us improve
title: ''
labels: bug
assignees: ''

---

<!--

Thank you for using python-oracledb.

See https://www.oracle.com/corporate/security-practices/assurance/vulnerability/reporting.html for how to report security issues

Please answer these questions so we can help you.

Use Markdown syntax, see https://docs.github.com/github/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax

-->

1. What versions are you using?

<!--

Give your Oracle Database version, e.g.:

    print(connection.version)

Give your Oracle Client version (if you are using Thick mode):

    print(oracledb.clientversion())

Also run Python and show the output of:

    import sys
    import platform

    print("platform.platform:", platform.platform())
    print("sys.maxsize > 2**32:", sys.maxsize > 2**32)
    print("platform.python_version:", platform.python_version())

And:

    print("oracledb.__version__:", oracledb.__version__)

-->

2. Is it an error or a hang or a crash?

3. What error(s) or behavior you are seeing?

<!--

Cut and paste text showing the command you ran.  No screenshots.

Use a gist for long screen output and logs: see https://gist.github.com/

-->

4. Does your application call init_oracle_client()?

<!--

This tells us whether you are using the python-oracledb Thin or Thick mode.

-->

5. Include a runnable Python script that shows the problem.

<!--

Include all SQL needed to create the database schema.

Format code by using three backticks on a line before and after code snippets, for example:

```
import oracledb
```

-->
