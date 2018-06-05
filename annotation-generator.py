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

import argparse
import logging
import sys
from ang.Config import Config
from ang.AnnotationGenerator import AnnotationGenerator
from ang.AnnotationGenerator import update_callback_print

__author__ = 'Viktor Richter'


def main(arguments):
    parser = argparse.ArgumentParser(description='Read metadata recordings and generate annotations.')
    parser.add_argument('-i', '--input', type=str,
                        help='An input file. Shortcut for "-v" "base" "input-file" "filename".')
    parser.add_argument('-o', '--output', type=str,
                        help='The output file to generate. Shortcut for "-v" "base" "output-file" "filename"')
    parser.add_argument('-c', '--config', type=str, default=None, help='Use provided config file.')
    parser.add_argument('-p', '--print-config', default=False, action='store_true',
                        help='Print an example config file.')
    parser.add_argument('-v', '--override-config', type=str, metavar=('SECTION', 'OPTION', 'VALUE'), nargs=3,
                        default=[], action='append', help='Override options from config.')
    args = parser.parse_args(arguments)

    config = Config(args.config)
    config.set_all(args.override_config)
    config.set_if('base', 'input-file', args.input)
    config.set_if('base', 'output-file', args.output)

    # print config if requested
    if args.print_config:
        print config.to_string()
        return

    generator = AnnotationGenerator(config)
    generator.validate_setup()
    data = generator.read_all_data(update_callback_print)
    generator.process_data(data)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    for logger in ['rsb.transport.socket.BusConnection']:
        logging.getLogger(logger).setLevel(logging.WARNING)
    sys.exit(main(sys.argv[1:]))
