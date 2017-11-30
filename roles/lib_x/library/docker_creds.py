#!/usr/bin/env python
# pylint: disable=missing-docstring
#
# Copyright 2017 Red Hat, Inc. and/or its affiliates
# and other contributors as indicated by the @author tags.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


DOCUMENTATION = '''
---
module: docker_creds

short_description: Creates/updates a 'docker login' file in place of using 'docker login'

version_added: "2.4"

description:
    - This module creates a docker config.json file in the directory provided by 'path'
      on hosts that do not support 'docker login' but need the file present for
      registry authentication purposes of various other services.

options:
    path:
        description:
            - This is the message to send to the sample module
        required: true
    registry:
        description:
            - This is the registry the credentials are for.
        required: true
    username:
        description:
            - This is the username to authenticate to the registry with.
        required: true
    password:
        description:
            - This is the password to authenticate to the registry with.
        required: true

author:
    - "Michael Gugino <mgugino@redhat.com>"
'''

EXAMPLES = '''
# Pass in a message
- name: Place credentials in file
  docker_creds:
    path: /root/.docker
    registry: registry.example.com:443
    username: myuser
    password: mypassword
'''

import base64
import json
import os

from ansible.module_utils.basic import AnsibleModule

def check_dest_dir_exists(module, dest):
    '''Check if dest dir is present and is a directory'''
    dir_exists = os.path.exists(dest)
    if dir_exists:
        if not os.path.isdir(dest):
            msg = "{} exists but is not a directory".format(dest)
            result = {'failed': True,
                    'changed': False,
                    'msg': msg,
                    'state': 'unknown'}
            module.fail_json(**result)
        else:
            return 1
    else:
        return 0

def create_dest_dir(module, dest):
    try:
        os.makedirs(dest, mode=0o700)
    except Exception as e:
        result = {'failed': True,
                'changed': False,
                'msg': str(e),
                'state': 'unknown'}
        module.fail_json(**result)

def load_config_file(module, dest):
    '''load the config.json in directory dest'''
    conf_file_path = os.path.join(dest, 'config.json')
    if os.path.exists(conf_file_path):
        # Try to open the file
        try:
            with open(conf_file_path) as f:
                data = f.read()
        # Couldn't open the file, exit.
        except Exception as e:
            result = {'failed': True,
                    'changed': False,
                    'msg': str(e),
                    'state': 'unknown'}
            module.fail_json(**result)
        try:
            j = json.loads(data)
        # Invalid json data.
        except Exception as e:
            result = {'failed': True,
                    'changed': False,
                    'msg': str(e),
                    'state': 'unknown'}
            module.fail_json(**result)
        return j
    else:
        return {}

def update_config(docker_config, registry, username, password):
    '''Add our registry auth credentials into docker_config dict'''

    # Add anything that might be missing in our dictionary
    if 'auths' not in docker_config:
        docker_config['auths'] = {}
    if registry not in docker_config['auths']:
        docker_config['auths'][registry] = {}

    # base64 encode our username:password string
    encoded_data = base64.b64encode('{}:{}'.format(username, password))

    # check if the same value is already present for idempotency.
    if 'auth' in docker_config['auths'][registry]:
        existing_data = docker_config['auths'][registry]['auth']
        if existing_data == encoded_data:
            # No need to go further, everything is already set in file.
            return 0
    docker_config['auths'][registry]['auth'] = encoded_data
    return 1

def write_config(module, docker_config, dest):
    '''Write updated credentials into dest/config.json'''
    conf_file_path = os.path.join(dest, 'config.json')
    try:
        with open(conf_file_path, 'w') as f:
            json.dump(docker_config, f, indent=8)
    except Exception as e:
        result = {'failed': True,
                'changed': False,
                'msg': str(e),
                'state': 'unknown'}
        module.fail_json(**result)



def run_module():
    '''Run this module'''
    module_args = dict(
        path=dict(aliases=['dest', 'name'], required=True, type='path'),
        registry=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True)
    )


    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    # First, create our dest dir if necessary
    dest = module.params['path']
    registry = module.params['registry']
    username = module.params['username']
    password = module.params['password']


    if not check_dest_dir_exists(module, dest):
        create_dest_dir(module, dest)
        docker_config = {}
    else:
        # We want to scrape the contents of dest/config.json
        # in case there are other registries/settings already present.
        docker_config = load_config_file(module, dest)

    # Put the registry auth info into the config dict.
    changed = update_config(docker_config, registry, username, password)

    if changed:
        write_config(module, docker_config, dest)
        result = {'changed': True}
    else:
        result = {'changed': False}


    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
