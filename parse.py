#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from mako.template import Template

class SyntaxError(Exception):
    def __init__(self, expression, line_number, error):
        self.expression = expression
        self.line_number = line_number
        self.error = error

class ChordText():
    def __init__(self, chord, text):
        self.chord = chord
        self.text = text

class ChoProLine():
    def __init__(self, type):
        self.type = type

class MetadataLine(ChoProLine):
    def __init__(self, key, value):
        super().__init__('metadata')
        self.key = key
        self.value = value

    def __str__(self):
        return '{%s: %s}\n' % (self.key, self.value)

class HiddenComment(ChoProLine):
    def __init__(self, text):
        super().__init__('hidden_comment')
        self.text = text

    def __str__(self):
        return '#%s\n' % (self.text)

class Comment(ChoProLine):
    def __init__(self, text, comment_type=''):
        super().__init__("comment")
        self.text = text
        self.comment_type = comment_type
        
    def __str__(self):
        if self.comment_type == '':
            comment_directive = 'comment'
        elif self.comment_type == 'highlight':
            comment_directive = 'highlight'
        else:
            comment_directive = 'comment_' + self.comment_type
        
        return '{%s: %s}\n' % (comment_directive, self.text)


class ChordTextLine(ChoProLine):
    def __init__(self, chord_texts=None):
        super().__init__("chordtext")
        self.chord_texts = chord_texts if chord_texts is not None else []

    def __str__(self):
        string = ""
        for chord_text in self.chord_texts:
            if len(chord_text.chord) > 0:
                string = string + "[%s]" % (chord_text.chord)
            string = string + chord_text.text
        return string

class Section():
    def __init__(self, name=None, lines=None):
        self.name = name
        if lines:
            self.lines = lines
        else:
            self.lines = []
    
    def __str__(self):
        string = ""
        if self.name:
            string = string + '{start_of_%s}\n' % (self.name)
        for line in self.lines:
            string = string + "%s\n" % (str(line))
        if self.name:
            string = string + '{end_of_%s}\n' % (self.name)
        return string

class Song():
    def __init__(self, sections=None, metadata=None):
        if sections:
            self.sections = sections
        else:
            self.sections = []
        
        if metadata:
            self.metadata = metadata
        else:
            self.metadata = {}
    
    def __str__(self):
        string = ''
        # for key, value in self.metadata.items():
        #     string = string + "{%s:%s}\n" % (key, value)
        for section in self.sections:
            string = string + "%s\n" % (str(section))
        return string
            


_chopro_directives_preamble = ['new_song', 'ns']
_chopro_directives_metadata = [ 'title',
                       't',
                       'subtitle',
                       'artist',
                       'composer',
                       'lyricist',
                       'copyright',
                       'album',
                       'year',
                       'key',
                       'time',
                       'tempo',
                       'duration',
                       'capo',
                       'meta',
                     ]
_chopro_directives_formatting = ['comment',
                            'comment_italic',
                            'comment_box',
                            'image',
                            ]

def read_chopro(stream):
    section_stack = []
    song = Song()
    section = Section(name='')

    line_number = 0
    for raw_line in stream:
        line_number = line_number + 1
        logging.debug("Parsing line number %d" % (line_number))
        # strip whitespace and newline characters from the right as we're not interested in those
        raw_line = raw_line.rstrip(" \n\r")
        logging.debug('Raw line: %s' % (raw_line))
        if(len(raw_line) == 0):
            logging.debug("Found an empty line")
            section.lines.append(ChordTextLine())
            continue
        if raw_line[0]=='#':
            logging.debug("Found an inline comment")
            section.lines.append(HiddenComment(raw_line[1:]))
        elif raw_line[0]=='{':
            logging.debug("Found a directive")
            # line is a directive
            if not raw_line[-1:] == '}':
                # a directive has to end with a '}' character
                raise SyntaxError(raw_line, line_number, "Missing '}'")
            raw_directive = raw_line[1:-1]
            logging.debug("Raw directive: %s" % (raw_directive))
            tokens = raw_directive.split(":", 1)
            if len(tokens) == 1:
                tokens.append(None)
            if tokens[0] in _chopro_directives_metadata:
                logging.debug('Found a metadata directive. Key="%s" Value="%s"' % (tokens[0], tokens[1]))
                song.metadata[tokens[0]] = tokens[1]
                section.lines.append(MetadataLine(tokens[0], tokens[1]))
            elif tokens[0] in _chopro_directives_formatting:
                logging.debug("Found a formatting directive")
                if tokens[0] in ['comment', 'c']:
                    logging.debug("Found a comment")
                    section.lines.append(Comment(tokens[1]))
                elif tokens[1] in ['comment_italic', 'ci']:
                    logging.debug("Found an italic comment")
                    section.lines.append(Comment(tokens[1], comment_type='italic'))
                elif tokens[1] in ['comment_box', 'cb']:
                    logging.debug("Found a box comment")
                    section.lines.append(Comment(tokens[1], comment_type='box'))
                elif tokens[1] == 'highlight':
                    logging.debug("Found a highlight comment")
                    section.lines.append(Comment(tokens[1], comment_type='highlight'))
            elif tokens[0].startswith('start_of_'):
                section_name = tokens[0][9:]
                logging.debug('Found a new section start with name "%s"' % (section_name))
                section_stack.append(section_name)
                logging.debug("Append last section to song")
                song.sections.append(section)
                logging.debug("Create a new section object")
                section = Section(name=section_name)
                foo = Section(name=section_name)
            elif tokens[0].startswith('end_of_'):
                section_name = tokens[0][7:]
                logging.debug('Found a section end with name "%s"' % (section_name))
                if not section_name == section_stack.pop():
                    raise SyntaxError(raw_line, line_number, "Trying to end section which hasn't started")
                section = Section()
            else:
                logging.warning('Unhandled directive "%s"' % (tokens[0]))
        else:               # line is not special, look for chords
            logging.debug("Found a regular chord-text line")
            chord_text_line = ChordTextLine(chord_texts=[])
            text = ''
            chord = ''
            in_chord = False
            for char in raw_line:
                if not in_chord:
                    if char == '[':
                        logging.debug("Found start of chord")
                        in_chord = True
                        if len(chord) > 0 or len(text) > 0:
                            logging.debug("Add last ChordText object to line.")
                            chord_text_line.chord_texts.append(ChordText(chord=chord, text=text))
                            text = ''
                            chord = ''
                    else:
                        text = text + char
                else:
                    if char == ']':
                        logging.debug("Found end of chord")
                        in_chord = False
                    else:
                        chord = chord + char
            chord_text_line.chord_texts.append(ChordText(chord=chord, text=text))                    
            if in_chord:
                raise SyntaxError(raw_line, line_number, "Unclosed chord")
            logging.debug("Append ChordTextLine to current section")
            section.lines.append(chord_text_line)
    logging.debug("Append last section to song")
    song.sections.append(section)
    return song


def main():
    logging.basicConfig(level=logging.DEBUG)
    with open('example.cho') as file:
        song = read_chopro(file)
    template = Template(filename='chopro.template')
    text = template.render(song=song)
    print(text)
    #print (song)


if __name__ == "__main__":
    main()
