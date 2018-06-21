###################################################################
#                                                                 #
# Copyright (C) 2018 Viktor Richter                               #
#                                                                 #
# File   : ang/rsbhelpers/__init__.py                             #
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
from datetime import timedelta
from rsb import Event

__author__ = 'Viktor Richter'

logger = logging.getLogger(__name__)


class BaseHandler(object):
    def __init__(self):
        self.__data = {}

    def add_entry(self, tier_name, entry, combine_repeated=True, override_last_end=True):
        if tier_name not in self.__data:
            self.__data[tier_name] = [entry]
        else:
            tier_data = self.__data[tier_name]
            if override_last_end:
                tier_data[-1]['end'] = entry['start']
            if (not combine_repeated) or (tier_data[-1]['label'] != entry['label']):
                tier_data.append(entry)

    def entries(self):
        return self.__data


class Deserializer(object):
    def __init__(self, typeobject):
        self.__typename = '.'+typeobject.DESCRIPTOR.full_name
        self.__typeobject = typeobject

    def deserialize(self, event):
        data_type, data_bytearray = event.getData()
        if data_type != self.__typename:
            Exception(__name__ + ' works ' + self.__typename + '. Got ', data_type)
        data = self.__typeobject()
        data.ParseFromString(data_bytearray)
        return data


class RstBaseHandler(BaseHandler):
    def __init__(self, typeobject):
        BaseHandler.__init__(self)
        self.__deserializer = Deserializer(typeobject=typeobject)

    def read_event(self, event):
        if not isinstance(event, Event):
            Exception(__name__ + ' works on rsb.Events. Got ', type(event))
        return self.__deserializer.deserialize(event), \
               timedelta(seconds=event.getMetaData().userTimes['rsbag:original_receive'])



