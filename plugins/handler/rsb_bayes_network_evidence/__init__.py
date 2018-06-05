###################################################################
#                                                                 #
# Copyright (C) 2018 Viktor Richter                               #
#                                                                 #
# File   : plugins/handler/bayes_network_evidence/__init__.py     #
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
from rst.bayesnetwork.BayesNetworkEvidence_pb2 import BayesNetworkEvidence

__author__ = 'Viktor Richter'

logger = logging.getLogger(__name__)


class Handler(object):
    def __init__(self, config):
        self.__config = config
        self.__tier = config.get('tier')
        self.__data = {}
        self.__warned_ignored = []

    def add_event(self, event):
        if not isinstance(event, Event):
            Exception(__name__ + ' works on rsb.Events. Got ', type(event))
        data_type, data_bytearray = event.getData()
        if data_type != '.rst.bayesnetwork.BayesNetworkEvidence':
            Exception(__name__ + ' works on BayesNetworkEvidence. Got ', data_type)
        data = BayesNetworkEvidence()
        data.ParseFromString(data_bytearray)
        if data.HasField('time'):
            time = data.time.time
        else:
            time = event.getMetaData().createTime
        for variable_state in data.observations:
            variable = variable_state.variable
            state = variable_state.state
            if variable not in self.__config['variables']:
                if variable not in self.__warned_ignored:
                    logger.info('ignoring variable {}'.format(variable))
                    self.__warned_ignored.append(variable)
                continue
            tier = self.__config['variables'][variable]
            entry = dict(start=time, label=state)
            if tier not in self.__data:
                self.__data[tier] = [entry]
            else:
                tier_data = self.__data[tier]
                if state != tier_data[-1]['label']:
                    tier_data[-1]['end'] = time
                    tier_data.append(entry)

    def validate_setup(self):
        if self.__config is None:
            raise Exception(__name__ + ' needs a map variable -> tier as config. Config: {}'.format(self.__config))

    def finish(self):
        return self.__data


def create(base_config, local_config):
    return Handler(local_config)
