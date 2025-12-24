#!/usr/bin/env python3
# -*- encoding=utf8 -*-

########################################################################
# Created time: 2024-08-27 18:03:44
# Author: Jason Young (杨郑鑫).
# E-Mail: AI.Jason.Young@outlook.com
# Last Modified by: Jason Young (杨郑鑫)
# Last Modified time: 2024-12-09 09:28:08
# Copyright (c) 2024 Yangs.AI
# 
# This source code is licensed under the Apache License 2.0 found in the
# LICENSE file in the root directory of this source tree.
########################################################################


import click
import traceback

from importlib.metadata import entry_points


def install_plugin_click_group(click_group_name: str, entry_point_group: str, entry_point_name: str):
    def decorator(click_group):
        assert isinstance(click_group, click.Group), TypeError("Plugins Can Only Be Attached to An Instance of click.Group()")
        try:
            all_entry_points = list(entry_points(group=entry_point_group, name=entry_point_name))
            assert len(all_entry_points) != 0, f"No entry point found for {entry_point_group}:{entry_point_name}"
            entry_point = all_entry_points[0]
            plugin_click_group = entry_point.load()
            assert isinstance(plugin_click_group, click.Group)
            for name, cmd in plugin_click_group.commands.items():
                click_group.add_command(cmd, name=name)
        except Exception as exception:
            # print(f'Warning: Failed to load plugin "{entry_point_group}:{entry_point_name}" for click group "{click_group_name}".\nException: {exception}')
            click_group.add_command(MissingCommand(click_group_name, entry_point_group, entry_point_name), name=entry_point_name)

        return click_group
    return decorator


class MissingCommand(click.Command):
    def __init__(self, click_group_name: str, entry_point_group: str, entry_point_name: str):
        plugin = entry_point_group.replace('.', '-') + '-' + entry_point_name
        module = entry_point_group.replace('younger.', '') + '-' + entry_point_name
        click.Command.__init__(self, entry_point_name)

        self.help = (
            f'\n'
            f'\u2020\U0001F4A9 Warning: The sub-module "{plugin}" is missing or incompatible. '
            f'To install it, run: '
            f'    \"pip install younger[{module}]\" or \"pip install {plugin}\" '
            f'\n\n\b\n'
            f'{traceback.format_exc()}'
        )
        self.short_help = (
            f'\n'
            f'\u2020\U0001F4A9 Warning: The sub-module "{plugin}" is missing or incompatible. '
            f'To fix it, run: \"pip install younger[{module}]\" or \"pip install {plugin}\"'
            f'\n\n\b\n'
        )

    def invoke(self, ctx):
        click.echo(self.help, color=ctx.color)
        ctx.exit(1)
