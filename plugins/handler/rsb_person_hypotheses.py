###################################################################
#                                                                 #
# Copyright (C) 2018 Viktor Richter                               #
#                                                                 #
# File   : plugins/handler/rsb_person_hypotheses/__init__.py      #
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
import json
from rstsandbox.hri.PersonHypotheses_pb2 import PersonHypotheses
from ang.rsbhelpers import RstBaseHandler

__author__ = 'Viktor Richter'

logger = logging.getLogger(__name__)


class Handler(RstBaseHandler):
    def __init__(self, config):
        RstBaseHandler.__init__(self, PersonHypotheses)
        self.__config = config
        self.__tier = config.get('tier')

    def add_event(self, event):
        data, time = self.read_event(event)
        persons = []
        for person in data.persons:
            persons.append(dict(id=person.tracking_info.id,
                                location=dict(
                                    x=person.body.location.x,
                                    y=person.body.location.y,
                                    z=person.body.location.z,
                                    frame_id = person.body.location.frame_id
                                )))
        self.add_entry(self.__tier, dict(start=time, label=json.dumps(persons)))

    def validate_setup(self):
        if self.__config is None:
            raise Exception(__name__ + ' needs a valid config. Config: {}'.format(self.__config))

    def finish(self):
        return self.entries()


def create(base_config, local_config):
    return Handler(local_config)
