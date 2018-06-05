#!/usr/bin/env python

###################################################################
#                                                                 #
# Copyright (C) 2017 Viktor Richter                               #
#                                                                 #
# File   : ang/__init__.py                                        #
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

__author__ = 'Viktor Richter'


class HandlerRepository(object):
    def __init__(self):
        self.__cache = {}
        self.__handles = []

    def add_handle(self, handle):
        logging.debug('adding handle address "{}" name "{}" channel "{}" '.format(handle, handle.name(), handle.channel()))
        self.__handles.append(handle)
        self.__cache = {}

    def match_handle(self, channel):
        result = []
        for handle in self.__handles:
            if handle.match(channel):
                result.append(handle)
        self.__cache[channel] = result
        logging.debug('handles matching channel "{}" found: {} '.format(channel, result))
        return result

    def get_handle(self, channel):
        # lookup in handler cache
        result = self.__cache.get(channel)
        if result is not None:
            return result
        else:
            # initial lookup should happen once per channel
            return self.match_handle(channel)

    def get_all_handles(self):
        return self.__handles

