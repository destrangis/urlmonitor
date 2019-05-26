## UrlMonitor

This program is intended to be run periodically from cron or a systemd ``.timer`` service on GNU/Linux, a Periodic Task on Windows, or whatever you are using.

When run, the program will check the URLs from its list, and, if they have changed since the last time they were checked, will run a series of actions as a result.

The list of URLs and actions to be run if changed are specified in a YAML file (by default called ``urllist.yml``). This file consist on a LIST of OBJECTS, each containing the fields name with a descriptive string, url with the url to be checked, and actions, which is a LIST of OBJECTS, where the key is the action name and the value are the arguments, which can be a STRING or a LIST of strings.

An example of urllist.yml file:

```yaml
---
- name: Check for new versions of my favourite software
  url: https://www.coolproject.org/download/files
  actions:
    - email_notify:
        - joe@domain.com
        - jill@somewhere.else.com

- name: Get latest version of the software
  url: https://www.coolproject.org/latest
  actions:
    - re_match:
        - '[Ss]ource [Tt]arball.*<a href=\"([^"]+)'
    - run_script: download_and_build https://www.coolproject.org/{re_match[1]}
```

As you can see on the last line, the arguments to the actions are expanded with the variables from previous actions, the url, the contents, the HTTP status code obtained while fetching the URL, etc.

### Installation

Just run the provided ``setup.py`` program:

```
$ python3 setup.py install
```

### Running

You can call the program with ``--help`` for the program options::


    $ urlmonitor --help
    usage: urlmonitor [-h] [--config FILE] [--persist-file FILE]
                      [ymlfile [ymlfile ...]]

    positional arguments:
      ymlfile               Url check specification.

    optional arguments:
      -h, --help            show this help message and exit
      --config FILE, -c FILE
                            Configuration file.
      --persist-file FILE, -p FILE
                            Persistence file to store URL status. Default
                            ./persistence.sqlite


* The ``yml`` file(s) contain the URLs to check, as discussed above.
* The ``--persist-file`` is a database that will be created in order to track whether the URLs have changed and when.
* The ``--config`` file is a YAML file that specifies where the options are located. It is discussed on the next section.

### Configuration

UrlMonitor is configured using a YAML file containing an OBJECT with the different sections where you can specify:

* Global variables (``set_vars``): available to all the actions.
* Actions (``actions``): Each additional action individually, specifying its name, the Python module where it is located, and perhaps a set of configuration parameters.
* Action directories (``action_dir``): Specify a directory containing Python files. Each Python file contains an action named like the file.
* Action configurations (``action_config``): Contains an OBJECT whose entries are the names of the actions and the values are the configuration parameters for that action. Any action can be configured in this way, whether it has been specified using ``action`` or an ``action_dir``. Some predefined actions also need to be configured this way, for example the ``email_notify`` predefined action needs the parameter ``smtp_server`` to be set.
* Logging configuration (``logging_config``): Contains the settings needed to call `logging.config.dictConfig()` as per the [Python standard library documentation](https://docs.python.org/3/library/logging.config.html#logging-config-dictschema). The logger name that will be used is `URLMONITOR`. If this section is not present, sensible defaults will be used.

An example of the configuration follows::

~~~yaml
---

# define global variables for all the actions
set_vars:
    var1: 5.4
    var2:
        - list
        - of
        - "strings"
    var3:
        keys: of
        a: dict

# load all the actions in a directory
#   all the .py files in the directory will be loaded
#   if the module is action_name.py, the action name will be 'action_name'
#   and will be initialised with the objects in its entry in an
#   an 'actions_config' section
#
action_dir: /path/to/dir1

action_dir:
    # specify a list of paths
    - /path/to/dir2
    - /another/path/dir3

# actions and configuration objects:
# configuration objects are mappings that the actions need to initialise
# themselves, like the smtp host in a 'mail_send' action or a database name
# and connection parameters to look up/store stuff etc.
#
# The actions will be called (or not) at runtime with the url that's changed,
# the contents of that url, and the variables with their values at that point.

actions_config:
        # configuration objects for actions defined on action_dir
        # as opposed to actions defined in actions:
        action_in_dir1:
            update_url: https://www.someserver.com
            something_or_another: 34

        some_action_in_dir3:
            parameter: value
            another_parameter: another_value


actions:
    # always a list containing mappings of actions and configuration values

                # should always have a name and module
    - name: add_to_database
      module: /path/to/module.py
                # ad_hoc configuration parameters, defined and expected by
                # each particular action
      dbhost: host1.mynetwork
      dbname: documents
      dbuser: albert
      dbpassword: hello0011

    - name: another_action:
      module: /the/path/to/another_action.py
      foo: bar

logging_config:
     # the following is passed directly to logging.config.dictConfig()
     loggers:
        URLMONITOR:
            level: DEBUG
            handlers:
                - console
     handlers:
         console:
             class: logging.StreamHandler
             stream: ext://sys.stdout
             level: DEBUG
~~~

### Predefined Actions

The following actions are available out of the box:

#### set_vars
Set global variables. The variables defined using this action are global and can be used by all the URL objects and their actions.

Example:
```yaml
set_vars:
   value_1: 34
   list_var:
      - item 1
      - item 2
      - another item
```

#### list_vars
This action lists all the variables and their values to the log. The log level must be debug.

#### no_action
This is a dummy action. It does nothing.

#### re_match
Search the content of the URL using one or more regular expressions passed as arguments. The regular expressions are applied using ``re.MULTILINE`` (see [Python's ``re`` module documentation](https://docs.python.org/3/library/re.html#re.MULTILINE) ) i.e. '^' matches the beginning of every line and '$' matches every end of line.

As a result, it creates two variables:

* ``re_match``: A list of all the group matches in the first regular expression.
* ``re_match_all``: A list containing the list of all group matches of all the regular expressions in the argument list, in the same order as they appear.

Example:

```yaml
  - name: Get amount and code
    url: http://www.interesting.com/amounts_codes/
    actions:
       - re_match:
             - 'The amount is:\s*([0-9]+)'
             - 'Code\s*(\w+)'
       - set_vars:
            amount: {re_match[1]}
            code: {re_match_all[1][1]}
```

#### email_notify
Send an email with a notification of the URL change to the recipient email addresses specified in the argument list.

Example:
```yaml
- name: Check for new versions of my favourite software
  url: https://www.coolproject.org/download/files
  actions:
    - email_notify:
        - joe@domain.com
        - jill@somewhere.else.com
```

Before this action can be used it must be configured in the yaml configuration file with the following parameters:

Name            | Value                   | Default value
----------------|-------------------------|-------------
smtp_server     | server name             |
from_address    | email address           | urlmonitor@hostname
smtp_port       | port number             | 25 for SMTP, 587 for SSL
smtp_encryption | SSL or STARTTLS         | empty, no encryption
smtp_user       | username                | empty, no smtp authentication
smtp_password   | password base64 encoded |

Configuration example:

```yaml
- actions_config:
     email_notify:
         smtp_server: mailhost.server.com
         from_address: urlbot@mydomain.com
         smtp_encryption: STARTTLS
         smtp_port: 465
         smtp_user: phil
         smtp_password: aGVsbG8wMDExMjI=
```

#### run_script
This action runs a program whose command line is its argument list.

Example:

```yaml
- name: Download the new file
  url: https://www.filesite.net/targetfiles.html
  actions:
      - re_match: '<a href=\"(.*)\">The file'
      - run_script: wget {re_match[1]}
```
This action sets the following variables:

Variable    | Value
------------|-----------------------------------
return_code | The exit code of the program
error       | The error encountered, if any
stdout      | Whatever the program has written to its standard output
stderr      | Whatever the program has written to its error output


### Writing Custom Actions
You can write a custom action easily. You just need to write a Python module that exports a callable called ``action_object`` with the following signature:

```python
def action_object(name, arglst, url, content, variables, log):
    pass
```

Where the arguments are:

Argument  | Description
----------|--------
name      | The action name
arglst    | The list of arguments.
url       | The url that changed
content   | The content (possibly HTML) of the url
variables | A mapping containing the variables and their values
log       | A logging object

If the arguments in ``arglst`` will be expanded by the calling routine and should contain the final value.

If your action requires configuration parameters, you can create a class that has a ``__call__`` method and instantiate into ``action_object``. At configuration time, the program will call the ``initialise`` method with a dictionary containing the configuration parameters as argument.

In order to simplify the process, the module ``actionbase`` provides the class ``Action`` from which your action can inherit. This already provides an ``initialise`` method which will install the configuration parameters, which you can access as instance attributes of ``action_object``. In addition, you should provide a list of expected parameters and a default value for those that can have one in the class variables ``check_cfg_vars`` and ``default_vars``. An exception is raised if a parameter that has been specified in ``check_cfg_vars`` is not found and there is no default value.

As an example, you can check the code for the ``email_notify`` action.

```python
from urlmonitor.actionbase import Action

class _EmailAction(Action):

    check_cfg_vars = [ "smtp_server", "from_address", "smtp_encryption",
            "smtp_user", "smtp_password", "smtp_port"]
    default_vars = {
        "from_address": "urlmonitor@{}".format(_NODE),
        "smtp_encryption": None,
        "smtp_user": None,
        "smtp_password": "",
        "smtp_port": 0,
        }

    ...

    def __call__(self, name, arglst, url, content, variables, log):
        ...
        
action_object = _EmailAction()
```


### License

This software is released under the **MIT License**
