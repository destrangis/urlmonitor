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

UrlMonitor is configured using a YAML file containing a LIST of sections where you can specify:

* Global variables (``set_vars``): available to all the actions.
* Actions (``actions``): Each additional action individually, specifying its name, the Python module where it is located, and perhaps a set of configuration parameters.
* Action directories (``action_dir``): Specify a directory containing Python files. Each Python file contains an action named like the file.
* Action configurations (``action_config``): Contains an OBJECT whose entries are the names of the actions and the values are the configuration parameters for that action. Any action can be configured in this way, whether it has been specified using ``action`` or an ``action_dir``. Some predefined actions also need to be configured this way, for example the ``email_notify`` predefined action needs the parameter ``smtp_server`` to be set.

An example of the configuration follows::

~~~yaml
---

# define global variables for all the actions
- set_vars:
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
- action_dir: /path/to/dir1

- action_dir:
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

- actions_config:
        # configuration objects for actions defined on action_dir
        # as opposed to actions defined in actions:
        action_in_dir1:
            update_url: https://www.someserver.com
            something_or_another: 34

        some_action_in_dir3:
            parameter: value
            another_parameter: another_value


- actions:
    # always a list containing mappings of actions and configuration values

                # should always have a name and module
    - name: send_by_email:
      module: /path/to/module.py
                # ad_hoc configuration parameters, defined and expected by
                # each particular action
      smtpserver: mail.pepe.com
      port: 25
      SSL: yes

    - name: another_action:
      module: /the/path/to/another_action.py
      foo: bar
~~~

### License

This software is released under the **MIT License**
