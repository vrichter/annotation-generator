#!/usr/bin/env python

###################################################################
#                                                                 #
# Copyright (C) 2017 Viktor Richter                               #
#                                                                 #
# File   : extract_elan.py                                        #
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

import sys
import argparse
import rsbag
import logging
import re
from rsb.converter import SchemaAndByteArrayConverter, PredicateConverterList
import pympi

__author__ = 'Viktor Richter'

def createChannel(event):
    return str(event.scope.toString()) + ':' + str(event.data[0])

class ElanAnnotation(object):
    def __init__(self, tier, start_time, end_time, data):
        self.tier = tier
        self.start_time = start_time
        self.end_time = end_time
        self.data = data

class ElanOutput(object):
    def __init__(self):
        self.__document = pympi.Eaf()

    def addAnnotation(self,elan_annotation):
        def as_elan_time(timestamp):
            return int(round(timestamp * 1000))
        tier = elan_annotation.tier
        if tier is None:
            tier = 'default'
        if tier not in self.__document.get_tier_names():
            self.__document.add_tier(tier)
        print 'adding annotation',elan_annotation
        self.__document.add_annotation(tier,
                                       as_elan_time(elan_annotation.start_time),
                                       as_elan_time(elan_annotation.end_time),
                                       elan_annotation.data[0])

    def write(self,file_path):
        self.__document.to_file(file_path,True)


class HandlerRepository(object):
    def __init__(self):
        self.__cache = {}
        self.__noncache = {}
        self.__handles = []

    def addHandle(self, channel, handle):
        self.__handles.append({ 'c': re.compile(channel), 'h': handle })

    def matchHandle(self, channel):
        result = None
        cache = self.__noncache
        for handle in self.__handles:
            if handle['c'].search(channel):
                self.__cache[channel] = handle['h']
                result = handle['h']
                cache = self.__cache
                break
        cache[channel] = result
        if result is None:
            print 'Could not find a handler for',channel
        return result

    def getHandle(self, channel):
        try: # lookup in handler cache
            return self.__cache[channel]
        except KeyError:
            pass
        try: # lookup in not-found cache
            return self.__noncache[channel]
        except KeyError:
            pass
        # initial lookup should happen once per channel
        return self.matchHandle(channel)

class ConsecutiveCreationTimeHandler(object):
    def __init__(self,tier=None):
        self.__tier = tier
        self.__lastEvent = None

    def handle(self,event):
        def getEventTime(event):
            return event.metaData.userTimes['rsbag:original_send']
        result = None
        if self.__lastEvent is not None:
            print event.metaData
            start = getEventTime(self.__lastEvent)
            end = getEventTime(event)
            data = self.__lastEvent.data
            result = ElanAnnotation(self.__tier,start,end,data)
        self.__lastEvent = event
        return result

def registerHandlers(repository):
    personHandler = ConsecutiveCreationTimeHandler()
    facesHandler = ConsecutiveCreationTimeHandler()
    repository.addHandle('PersonHypotheses$',personHandler.handle)
    repository.addHandle('Faces$',facesHandler.handle)

def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def main(arguments):
    parser = argparse.ArgumentParser(description='Read tide files and generate ELAN annotations.')
    parser.add_argument('input', metavar='INPUT', type=str, help='A input tide file')
    parser.add_argument('output', metavar='OUTPUT', type=str, help='The output file to generate.')
    parser.add_argument('-c','--channel', type=str, nargs="+", help="Channel expressions to match.")
    parser.add_argument('-n','--number-events', type=int, help="Stop after number of events.")
    parser.add_argument('--rsbag-executable', type=str, default='rsbag', help="Can be used to changed the used rsbag executable.")
    args = parser.parse_args(arguments)

    # check if rsbag exists
    rsbag_ex = which(args.rsbag_executable)
    if rsbag_ex is None:
        error = 'Rsbag executable "{}" does not exist or is not executable.'.format(args.rsbag_executable)
        raise Exception(error)


    handlers = HandlerRepository()
    registerHandlers(handlers)

    converter = SchemaAndByteArrayConverter()
    converters = PredicateConverterList(bytearray)
    converters.addConverter(converter, lambda x: True)

    # read annotations from file
    annotations = ElanOutput()
    with rsbag.openBag(args.input, channels = args.channel, rsbag=rsbag_ex, converters=converters) as bag:
        sum = len(bag.events)
        number = 0
        print 'Processing',sum,' events from',args.input[0],'. Matching channels',args.channel
        for e in bag.events:
            number+=1
            channel = createChannel(e)
            handler = handlers.getHandle(channel)
            if handler is not None:
                data = handler(e)
                if data is not None:
                    annotations.addAnnotation(data)
                print '\r>> processed event {} of {} on {}'.format(number,sum,channel),
                sys.stdout.flush()
            if args.number_events is not None and number >= args.number_events:
                break
    annotations.write(args.output)



if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    sys.exit(main(sys.argv[1:]))

def handleFaces(event):
    return event

def registerHandlers(repository):
    personHandler = PersonHypothesesHandler()
    repository.addHandle('PersonHypotheses$',personHandler.handle)
    repository.addHandle('Faces$',handleFaces)

def main(arguments):
    parser = argparse.ArgumentParser(description='Read tide files and generate ELAN annotations.')
    parser.add_argument('input', metavar='FILE', type=str, nargs=1, help='A input tide file')
    parser.add_argument('-c','--channel', type=str, nargs="+", help="Channel expressions to match.")
    args = parser.parse_args(arguments)

    handlers = HandlerRepository()
    registerHandlers(handlers)

    converter = SchemaAndByteArrayConverter()
    converters = PredicateConverterList(bytearray)
    converters.addConverter(converter, lambda x: True)

    with rsbag.openBag(args.input[0], channels= args.channel, rsbag='./rsbag', converters=converters) as bag:
        sum = len(bag.events)
        number = 0
        print 'Processing',sum,' events from',args.input[0],'. Matching channels',args.channel
        for e in bag.events:
            number+=1
            channel = createChannel(e)
            handler = handlers.getHandle(channel)
            if handler is not None:
                data = handler(e)
                print '\r>> processed event {} of {} on {}'.format(number,sum,channel),
                sys.stdout.flush()


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    sys.exit(main(sys.argv[1:]))
