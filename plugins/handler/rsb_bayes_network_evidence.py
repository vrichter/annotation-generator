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
from rst.bayesnetwork.BayesNetworkEvidence_pb2 import BayesNetworkEvidence
from ang.rsbhelpers import RstBaseHandler

__author__ = 'Viktor Richter'

logger = logging.getLogger(__name__)


class Handler(RstBaseHandler):
    def __init__(self, config):
        RstBaseHandler.__init__(self, BayesNetworkEvidence)
        self.__config = config
        self.__tier = config.get('tier')
        self.__warned_ignored = []

    def add_event(self, event):
        data, time = self.read_event(event)
        # iterate bayesnetworkevidence::variables and set the tier their value
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
            self.add_entry(tier, entry)

    def validate_setup(self):
        if self.__config is None:
            raise Exception(__name__ + ' needs a map variable -> tier as config. Config: {}'.format(self.__config))

    def finish(self):
        return self.entries()


def create(base_config, local_config):
    return Handler(local_config)
