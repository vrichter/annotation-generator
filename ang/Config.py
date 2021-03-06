#!/usr/bin/env python

###################################################################
#                                                                 #
# Copyright (C) 2017 Viktor Richter                               #
#                                                                 #
# File   : ang/Config.py                                          #
# Authors: Viktor Richter                                         #
#                                                                 #
#                                                                 #
# GNU LESSER GENERAL PUBLIC LICENSE                               #
# This file may be used under the terms of the GNU Lesser General #
# Public License version 3.0 as published by the                  #
#                                                                 #
# Free Software Foundation and appearing in the file LICENSE.LGPL #
# included in the packaging of this file.  Please review the      #
# following information to ensure the license requirements will   #
# be met: http://www.gnu.org/licenses/lgpl-3.0.txt                #
#                                                                 #
###################################################################

import io
import ast
import ConfigParser

__author__ = 'Viktor Richter'


def add_comment(config, section, text):
    config.set(section, "# " + text)


def add_options_with_comments(config, section, options):
    if not config.has_section(section):
        config.add_section(section)
    for option in options:
        add_comment(config, section, option[2])
        config.set(section, option[0], option[1])


class Config(object):
    def __init__(self, filename=None):
        self.__config = ConfigParser.ConfigParser(allow_no_value=True)
        add_options_with_comments(self.__config, 'base', [
            ('input-file', None, 'input file to process.'),
            ('output-file', None, 'output file to generate.'),
            ('channel', [], 'only matching channels will be processed. channels from handlers will be appended.'),
            ('number-events', None, 'stop after a specific amount of processed events.'),
            ('start-time-ms', 0, 'the start time of the recording in milliseconds. will be subtracted from annotations'),
            ('input', 'rsb', 'input metadata provider plugin to load.'),
            ('plugin-path-input', ['./plugins/input'], 'search path for input plugins.'),
            ('plugin-path-handler', ['./plugins/handler'], 'search path for handler plugins.'),
            ('plugin-path-output', ['./plugins/output'], 'search path for output plugins.')
        ])
        if filename is not None:
            self.__config.read(filename)

    def set_if(self, section, option, value):
        if section is not None \
                and option is not None \
                and value is not None:
            self.__config.set(section, option, value)

    def set(self, section, option, value):
        self.__config.set(section, option, value)

    def get(self, section, option):
        return self.__config.get(section, option)

    def get_eval(self, section, option):
        return ast.literal_eval(self.get(section, option))

    def to_string(self):
        fp = io.BytesIO()
        self.__config.write(fp)
        return fp.getvalue()

    def input(self):
        return self.get('base', 'input')

    def handler(self):
        print(self.options('handler'))
        return self.options('handler')

    def output(self):
        print(self.options('output'))
        return self.options('output')

    def input_file(self):
        return self.get('base', 'input-file')

    def output_file(self):
        return self.get('base', 'output-file')

    def plugin_path_input(self):
        return self.get_eval('base', 'plugin-path-input')

    def plugin_path_handler(self):
        return self.get_eval('base', 'plugin-path-handler')

    def plugin_path_output(self):
        return self.get_eval('base', 'plugin-path-output')

    def options(self, section):
        result = {}
        for key, value in self.__config.items(section):
            if value is None:
                continue
            try:
                result[key] = ast.literal_eval(value)
            except ValueError as error:
                raise Exception(str(error) + '\nCould not parse value from "' + value + '"')

        return result

    def set_all(self, options):
        for option in options:
            self.set(option[0], option[1], option[2])

    def internal(self):
        return self.__config


def default_config():
    config = Config()
    add_options_with_comments(config.internal(), 'rsb', [
        ('executable', 'rsbag', 'sets the path to the rsbag application.')
    ])
    add_options_with_comments(config.internal(), 'handler', [
        ('test', "{ 'name': 'test', 'channel': '/test', 'tier': 'testtier' }",
         'handler option-names are ignored. The values must be dicts with at least a "name" defining the handler '
         'and a channel to filter events.')
    ])
    add_options_with_comments(config.internal(), 'output', [
        ('elan', "{ 'name': 'generate-elan', 'overwrite-output': 'True' }",
         'output processors are executed on the data generated by all handlers combined. The data is consecutively '
         'piped through all defined outputs')
    ])
    return config
