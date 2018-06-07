#!/usr/bin/env python

###################################################################
#                                                                 #
# Copyright (C) 2017 Viktor Richter                               #
#                                                                 #
# File   : ang/AnnotationGenerator.py                             #
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

import copy
import sys
import re
import datetime
from pluginbase import PluginBase
from ang import HandlerRepository
import logging

__author__ = 'Viktor Richter'

logger = logging.getLogger(__name__)

class Plugin(object):
    def __init__(self, name, module, config):
        self.__name = name
        self.__plugin = module
        self.__config = config

    def name(self):
        return self.__name

    def plugin(self):
        return self.__plugin

    def config(self):
        return self.__config

    def validate_setup(self):
        #TODO: check if all required functions exist in plugin
        return self.plugin().validate_setup()


class Input(Plugin):
    def __init__(self, name, plugin, config):
        super(Input, self).__init__(name, plugin, config)


class Output(Plugin):
    def __init__(self, name, plugin, config):
        super(Output, self).__init__(name, plugin, config)

    def process(self, data):
        if data is None or len(data) == 0:
            logger.warn('Generated data is none or empty. Skipping output processing for {}'.format(self.name()))
            return
        try:
            return self.plugin().process(data)
        except Exception as e:
            logger.exception('Output "{}" fails processing data. Error: "{}"'.format(self.name(), str(e)))


class Handle(Plugin):
    def __init__(self, channel, plugin, config):
        super(Handle, self).__init__(config.get('name','unnamed'), plugin, config)
        self.__channel = channel
        self.__channel_pattern = re.compile(channel)

    def match(self, channel):
        if self.__channel_pattern.search(channel):
            return True
        else:
            return False

    def channel(self):
        return self.__channel

    def finish(self):
        try:
            return self.plugin().finish()
        except Exception as e:
            logger.exception('Hander "{}" on channel "{}" does not want to finish. Error: "{}"'.format(self.name(), self.channel(), str(e)))

    def add_event(self, event):
        try:
            return self.plugin().add_event(event)
        except Exception as e:
            logger.exception('Hander "{}" on channel "{}" throws while adding event "{}". Error: "{}"'.format(self.name(), self.channel(), str(event),  str(e)))


def init_data_provider(plugin_source, config):
    try:
        input_plugin = plugin_source.load_plugin(config.input())
        return Input(config.input(), input_plugin.create(config), config)
    except ImportError as error:
        logger.warning('Could not find plugin named "' + config.input() + '" in plugin path.\n' \
              'Input plugins search path: ' + str(config.plugin_path_input()))
        raise


def init_data_handlers(plugin_source, config, handler_repository=HandlerRepository.HandlerRepository()):
    for key, value in config.handler().iteritems():
        if 'name' not in value:
            raise ImportError('Cannot import plugin without name field: '+str(value))
        if 'channel' not in value:
            raise ImportError('Cannot import plugin without channel field: '+str(value))
        try:
            handler = plugin_source.load_plugin(value['name'])
            handler_repository.add_handle(Handle(value['channel'], handler.create(config, value), value))
        except ImportError as error:
            logger.warning('Could not find handler plugin named "' + value['name'] + '" in plugin path.\n' \
                  'Handler plugins search path: ' + str(config.plugin_path_handler()))
            raise

    return handler_repository


def init_outputs(plugin_source, config):
    outputs = []
    for key, value in config.output().iteritems():
        try:
            outputs.append(Output(value['name'], plugin_source.load_plugin(value['name']).create(config, value), value))
        except ImportError as error:
            logger.warning('Could not find output plugin named "' + value['name'] + '" in plugin path.\n' \
                  'Output plugins search path: ' + str(config.plugin_path_output()))
            raise
    return outputs


def update_callback_pass(message):
    pass


def update_callback_print(message):
    logger.info('\r>> ' + message)
    sys.stdout.flush()


def get_event_time(event):
    return datetime.timedelta(seconds=event.getMetaData().userTimes['rsbag:original_receive'])


def add_handler_channels(config, handles):
    channels = config.get_eval('base', 'channel')
    if channels is None:
        channels = []
    for handle in handles:
        if handle.channel() not in channels:
            channels.append(handle.channel())
    if len(channels) == 0:
        channels = None
    config.set('base', 'channel', str(channels))


def adapt_times(tiers, config):
    delta = datetime.timedelta(milliseconds=float(config.get('base', 'start-time-ms')))
    for tier, value in tiers.iteritems():
        for elem in value:
            elem['start'] = elem['start']-delta
            elem['end'] = elem['end']-delta


class AnnotationGenerator(object):
    # setup data provider and handlers
    def __init__(self, config):
        self.__config = config
        self.__plugin_base_input = PluginBase(package='ang.input')
        self.__plugin_source_input = self.__plugin_base_input.make_plugin_source(searchpath=config.plugin_path_input())
        self.__plugin_base_handler = PluginBase(package='ang.handler')
        self.__plugin_source_handler = self.__plugin_base_handler.make_plugin_source(searchpath=config.plugin_path_handler())
        self.__plugin_base_output = PluginBase(package='ang.output')
        self.__plugin_source_output = self.__plugin_base_output.make_plugin_source(searchpath=config.plugin_path_output())
        # init handlers
        self.__handlers_repo = init_data_handlers(self.__plugin_source_handler, config)
        # add handler channels to data provider before initialization
        add_handler_channels(config, self.__handlers_repo.get_all_handles())
        self.__provider = init_data_provider(self.__plugin_source_input, config)
        self.__outputs = init_outputs(self.__plugin_source_output, config)
        self.__max_events = config.get('base', 'number-events')
        if self.__max_events is None:
            self.__max_events = -1
        else:
            self.__max_events = int(self.__max_events)

    def validate_setup(self):
        errors = []

        def try_validate(plugin):
            try:
                plugin.validate_setup()
            except Exception as error:
                errors.append((type(plugin), plugin.config(), error))

        try_validate(self.__provider)
        for handle in self.__handlers_repo.get_all_handles():
            try_validate(handle)
        for output in self.__outputs:
            try_validate(output)
        if len(errors) > 0:
            for error in errors:
                logger.error('Error while validating plugin configuration:'
                      '\nType: {}\nConfig: {}\nError: {}'.format(error[0], error[1], error[2]))
            raise Exception('could not validate plugin configuration')

    # read annotations from file
    def read_all_data(self, update_callback=update_callback_pass):
        with self.__provider.plugin() as prov:
            events = prov.events()
            sum_events = len(events)
            current_event_number = 0
            last_event_time =None
            for event in events:
                last_event_time = get_event_time(event)
                current_event_number += 1
                ch = prov.channel(event)
                channel = ':'.join(prov.channel(event))
                handlers = self.__handlers_repo.get_handle(channel)
                if handlers is not None:
                    for handler in handlers:
                        handler.add_event(event)
                        update_callback('processed event {} of {} on {}'.format(current_event_number, sum_events, channel))
                if 0 < self.__max_events <= current_event_number:
                    break
        # compact data
        tiers = {}
        for handler in self.__handlers_repo.get_all_handles():
            update_callback('finish handler {} on channels {}'.format(handler.name(), handler.channel()))
            data = handler.finish() or {}
            for tier, values in data.iteritems():
                # skip empty tiers
                if len(values) == 0:
                    logger.warn('tier {} is empty'.format(tier))
                    continue
                # set start/end times for edge events
                if 'end' not in values[-1]:
                    values[-1]['end'] = last_event_time
                if tier in tiers:
                    tiers[tier].extend(values)
                else:
                    tiers[tier] = values
        adapt_times(tiers, self.__config)
        return tiers

    # do post processing
    def process_data(self, data):
        for process in self.__outputs:
            data = process.process(data)
        return data
