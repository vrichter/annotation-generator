###################################################################
#                                                                 #
# Copyright (C) 2017 Viktor Richter                               #
#                                                                 #
# File   : plugins/input/rsb/__init__.py                          #
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

import os
import rsbag
from rsb.converter import SchemaAndByteArrayConverter, PredicateConverterList

__author__ = 'Viktor Richter'


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


class RsbagInput(object):
    def __init__(self, filename, channel, executable):
        print "will filter for following channels",
        rsbag_ex = which(executable)
        if not os.path.isfile(filename):
            error = 'Input file "{}" does not exist or is not a regular file.'.format(filename)
            raise Exception(error)
        if rsbag_ex is None:
            error = 'Rsbag executable "{}" does not exist or is not executable.'.format(executable)
            raise Exception(error)
        converter = PredicateConverterList(bytearray)
        converter.addConverter(SchemaAndByteArrayConverter(), wireSchemaPredicate=(lambda x: 5))
        self.__bag = None
        self.__bag = rsbag.openBag(filename, channels=channel, rsbag=rsbag_ex, converters=converter)

    def events(self):
        return self.__bag.events

    def channel(self, event):
        return (event.scope.toString(), event.data[0])

    def __enter__(self):
        self.__bag.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__bag.__exit__(exc_type, exc_val, exc_tb)

    def validate_setup(self):
        print('validate')
        pass


def create(config):
    return RsbagInput(
        config.get('base', 'input-file'),
        config.get_eval('base', 'channel'),
        config.get('rsb', 'executable'))
