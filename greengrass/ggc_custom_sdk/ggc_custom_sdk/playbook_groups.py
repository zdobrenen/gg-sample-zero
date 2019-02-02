import os
import sys
import shutil

from collections import namedtuple

from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase

import ansible.constants as C


Options = namedtuple(
    'Options',
    [
        'connection',
        'module_path',
        'forks',
        'remote_user',
        'private_key_file',
        'ssh_common_args',
        'ssh_extra_args',
        'sftp_extra_args',
        'scp_extra_args',
        'become',
        'become_method',
        'become_user',
        'verbosity',
        'check',
        'diff'
    ]
)

options = Options(
    connection='ssh',
    module_path=['/to/mymodules'],
    forks=10,
    remote_user='pi',
    private_key_file=None,
    ssh_common_args=None,
    ssh_extra_args=None,
    sftp_extra_args=None,
    scp_extra_args=None,
    become=None,
    become_method='sudo',
    become_user='root',
    verbosity=None,
    check=False,
    diff=False
)


def exec_playbook(host_list, username, password, group_name):

    loader = DataLoader()
    passwords = dict()

    inventory_manager = InventoryManager(loader=loader, sources=','.join(host_list))
    variable_manager  = VariableManager(loader=loader, inventory=inventory_manager)

    variable_manager.extra_vars = {
        'ansible_ssh_user': username,
        'ansible_ssh_pass': password
    }

    play_source =  dict(
        name = 'Greengrass Group Playbook',
        hosts = 'all',
        remote_user=username,
        gather_facts = 'yes',
        tasks = [
            dict(
                name='Set Playbook Facts',
                action=dict(
                    module='set_fact',
                    args=dict(
                        group_name=group_name
                    )
                )
            ),
            dict(
                name='Stop Greengrass Core',
                become=True,
                action=dict(
                    module='systemd',
                    args=dict(
                        name='greengrass',
                        state='stopped'
                    )
                )
            ),
            dict(
                name='Copy Greengrass Config',
                become=True,
                action=dict(
                    module='copy',
                    args=dict(
                        src='.gg/config/',
                        dest='/greengrass/config/'
                    )
                )
            ),
            dict(
                name='Copy Greengrass Root Certs',
                become=True,
                action=dict(
                    module='copy',
                    args=dict(
                        src='{{ item }}',
                        dest='/greengrass/certs/'
                    )
                ),
                with_fileglob=[
                    '.gg/certs/root.*'
                ]
            ),
            dict(
                name='Copy Greengrass Core Certs',
                become=True,
                action=dict(
                    module='copy',
                    args=dict(
                        src='{{ item }}',
                        dest='/greengrass/certs'
                    )
                ),
                with_fileglob=[
                    '.gg/certs/{{ groups_name }}*'
                ]
            ),
            dict(
                name='Start Greengrass Core',
                become=True,
                action=dict(
                    module='greengrass',
                    args=dict(
                        name='greengrass',
                        enabled=True,
                        state='started'
                    )
                )
            )
        ]
    )


    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    tqm = None
    try:
        tqm = TaskQueueManager(
            inventory=inventory_manager,
            variable_manager=variable_manager,
            loader=loader,
            options=options,
            passwords=passwords,
        )
        result = tqm.run(play)

    finally:

        if tqm is not None:
            tqm.cleanup()

        shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)
