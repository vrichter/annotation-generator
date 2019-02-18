#!/usr/bin/env python

###################################################################
#                                                                 #
# Copyright (C) 2017 Viktor Richter                               #
#                                                                 #
# File   : plugins/output/generate-ass-persons.py                 #
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
import pympi
import os
import datetime
import json

__author__ = 'Viktor Richter'

logger = logging.getLogger(__name__)


def as_timestamp(td):
    return int(round((td.microseconds / 10**3) + ((td.seconds + (td.days * 24 * 3600)) * 1000)))


def validate(data):
    if not isinstance(data, dict):
        raise Exception(__name__ + ' expects a each data point to be a dict but got :', type(data))
    if 'start' not in data:
        raise Exception(__name__ + ' expects a each data point to have a "start" element.')
    if 'end' not in data:
        raise Exception(__name__ + ' expects a each data point to have an "end" element.')
    if 'label' not in data:
        raise Exception(__name__ + ' expects a each data point to have a "label" element.')
    start = data['start']
    end = data['end']
    if end <= start:
        raise Exception(__name__ + ' expects a start times to be smaller than end times. Got {} >= {}'
                        .format(start, end))


class AssOutput(object):
    def __init__(self, filename, config):
        self.__document = []
        self.__filename = filename
        self.__overwrite = bool(config.get('overwrite-output', False))

    def process(self, tiers):
        if not isinstance(tiers, dict):
            raise Exception('ElanOutput expects a dict of tiers but got :', type(tiers))
        for tier_name, annotations in tiers.iteritems():
            num = 0
            for annotation in annotations:
                num +=1
                try:
                    validate(annotation)
                    self.__document.append({ 'start': as_timestamp(annotation['start']),
                                             'end': as_timestamp(annotation['end']),
                                             tier_name: annotation['label']})
                except Exception as e:
                    logger.warning('Cannot add annotation {} from tier {}: {}'.format(num, tier_name, e))
        with open(self.__filename, 'w') as outfile:
            json.dump(self.__document, outfile, sort_keys=True, indent=4, separators=(',', ': '))
        return {}

    def validate_setup(self):
        if self.__filename is None or len(self.__filename) == 0:
            raise Exception('filename is None or empty')
        if os.path.exists(self.__filename) and not self.__overwrite:
            raise Exception('file {} already exists'.format(self.__filename))
        with open(self.__filename, 'w'):
            pass


def create(base_config, local_config):
    return AssOutput(base_config.output_file(),local_config)
