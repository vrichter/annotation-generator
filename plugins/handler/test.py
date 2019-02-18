###################################################################
#                                                                 #
# Copyright (C) 2018 Viktor Richter                               #
#                                                                 #
# File   : plugins/handler/test/__init__.py                       #
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


import logging
from rsb import Event

__author__ = 'Viktor Richter'

logger = logging.getLogger(__name__)


def event_to_data(event):
    if not isinstance(event, Event):
        Exception('TestHandler works on rsb.Events. Got ', type(event))
    data = {}
    data['scope'] = event.getScope().toString()
    data['time'] = event.getMetaData().getCreateTime()
    data['label'] = event.getData()[0]
    return data


class TestHandler(object):
    def __init__(self, config):
        self.__config = config
        self.__tier = config.get('tier')
        self.__data = []

    def add_event(self, event):
        data = event_to_data(event)
        logger.debug('event added ' + str(data))
        self.__data.append(data)

    def validate_setup(self):
        if self.__tier is None:
            raise Exception('Testhandler config needs a tier configured. Config: {}'.format(self.__config))

    def finish(self):
        processed = []
        for data in self.__data:
            if len(processed) > 0:
                processed[-1]['end'] = data['time']
            processed.append({'label': data['label'], 'start': data['time']})
        return {self.__tier: processed}


def create(base_config, local_config):
    return TestHandler(local_config)
