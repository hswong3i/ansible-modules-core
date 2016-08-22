#!/usr/bin/python
#coding: utf-8 -*-

# (c) 2013-2014, Christian Berendt <berendt@b1-systems.de>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: php_module
version_added: 2.2
author: "Wong Hoi Sing Edison (@hswong3i)"
short_description: enables/disables a module of the PHP
description:
   - Enables or disables a specified module of the PHP.
options:
   name:
     description:
        - name of the module to enable/disable
     required: true
   state:
     description:
        - indicate the desired state of the resource
     choices: ['present', 'absent']
     default: present

requirements: ["phpenmod","phpdismod"]
'''

EXAMPLES = '''
# enables the PHP module "gd"
- php_module: state=present name=gd

# disables the PHP module "gd"
- php_module: state=absent name=gd
'''

RETURN = '''
'''

import re

def _run_threaded(module):
    control_binary = _get_ctl_binary(module)

    result, stdout, stderr = module.run_command("%s -V" % control_binary)

    if re.search(r'^[0-9]\.[0-9]$', stdout):
        return True
    else:
        return False

def _get_ctl_binary(module):
    ctl_binary = module.get_bin_path('phpquery')
    if ctl_binary is not None:
        return ctl_binary

    module.fail_json(
      msg="No phpquery found which is necessary for PHP module management.")

def _module_is_enabled(module):
    control_binary = _get_ctl_binary(module)
    name = module.params['name']

    result, stdout, stderr = module.run_command("%s -M" % control_binary)

    if result != 0:
        module.fail_json(msg="Error executing %s: %s" % (control_binary, stderr))

    if re.search(r' ' + name + r'_module', stdout):
        return True
    else:
        return False

def _set_state(module, state):
    name = module.params['name']

    want_enabled = state == 'present'
    state_string = {'present': 'enabled', 'absent': 'disabled'}[state]
    phpmod_binary = {'present': 'phpenmod', 'absent': 'phpdismod'}[state]
    success_msg = "Module %s %s" % (name, state_string)

    if _module_is_enabled(module) != want_enabled:
        if module.check_mode:
            module.exit_json(changed = True, result = success_msg)

        phpmod_binary = module.get_bin_path(phpmod_binary)
        if phpmod_binary is None:
            module.fail_json(msg="%s not found. Perhaps this system does not use %s to manage php" % (phpmod_binary, phpmod_binary))

        result, stdout, stderr = module.run_command("%s %s" % (phpmod_binary, name))

        if _module_is_enabled(module) == want_enabled:
            module.exit_json(changed = True, result = success_msg)
        else:
            module.fail_json(msg="Failed to set module %s to %s: %s" % (name, state_string, stdout), rc=result, stdout=stdout, stderr=stderr)
    else:
        module.exit_json(changed = False, result = success_msg)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name  = dict(required=True),
            state = dict(default='present', choices=['absent', 'present'])
        ),
        supports_check_mode = True,
    )

    name = module.params['name']
    if name == 'cgi' and _run_threaded(module):
        module.fail_json(msg="Your MPM seems to be threaded. No automatic actions on module %s possible." % name)

    if module.params['state'] in ['present', 'absent']:
        _set_state(module, module.params['state'])

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
