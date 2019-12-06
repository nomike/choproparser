#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# choproparser - A parser which reads ChordPro files and converts them
# into different formats using templates.
# Copyright (C) 2019  nomike <nomike@nomike.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Usage:
chordproparser.py [-v|--verbose] [--template=<template>] <chordprofile>...
chordproparser.py -h | --help | --version
"""



from choproparser import parser
import logging
from docopt import docopt
from mako.template import Template

def main():
    arguments = docopt(__doc__, version='0.1.0')
    if arguments['-v'] or arguments['--verbose']:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("main")
    template_file = arguments['--template'] if not arguments['--template'] == None else 'templates/__str__.template'
    logger.debug("Selected template: %s" % (template_file))
    songbook = parser.Songbook()
    for chordprofile in arguments['<chordprofile>']:
        logger.info("Parsing file %s" % (chordprofile))
        with open(chordprofile) as file:
            songbook.songs.extend(parser.read_chopro(file).songs)
    template = Template(filename=template_file)
    text = template.render(songbook=songbook)
    print(text)
    #print(song)

if __name__ == "__main__":
    main()
