#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
AgendaList module for Inky-Calendar Project
Copyright by aceisace + priv-kweihmann
"""

from inkycal.modules.template import inkycal_module
from inkycal.custom import *
from inkycal.modules.ical_parser import iCalendar

import calendar as cal
import arrow

filename = os.path.basename(__file__).split('.py')[0]
logger = logging.getLogger(filename)

class AgendaList(inkycal_module):
  """AgendaList class
  Create agenda and show events from given icalendars
  """

  name = "AgendaList - Display upcoming events from given iCalendars"

  requires = {
    "ical_urls" : {
      "label":"iCalendar URL/s, separate multiple ones with a comma",
      },

    }

  optional = {
    "ical_files" : {
      "label":"iCalendar filepaths, separated with a comma",
      },

    "dt_format":{
      "label":"Use an arrow-supported token for custom date formatting "+
      "see https://arrow.readthedocs.io/en/stable/#supported-tokens, e.g. ddd D MMM",
      "default": "ddd D MMM HH:mm",
      },
    "maxevents": {
      "label": "Limit to max events",
      "default": "999"
    },
    "calname": {
      "label": "Agenda name",
      "default": ""
    },
    "timeindent": {
      "label": "Indent of the time in pixel",
      "default": "20"
    },
    "eventindent": {
      "label": "Indent of the eventindent in pixel",
      "default": "20"
    }
    }

  def __init__(self, config):
    """Initialize inkycal_agenda module"""

    super().__init__(config)

    config = config['config']

    # Check if all required parameters are present
    for param in self.requires:
      if not param in config:
        raise Exception(f'config is missing {param}')
        logger.exception(f'config is missing "{param}"')

    # module specific parameters
    self.dt_format = config['dt_format']
    self.language = config['language']
    self.maxevents = config.get('maxevents', 999)
    self.calname = config.get('calname', '')
    self.timeindent = config.get('timeindent', 20)
    self.eventindent = config.get('eventident', 20)

    # Check if ical_files is an empty string
    if config['ical_urls'] and isinstance(config['ical_urls'], str):
      self.ical_urls = config['ical_urls'].split(',')
    else:
      self.ical_urls = config['ical_urls']

    # Check if ical_files is an empty string
    if config['ical_files'] and isinstance(config['ical_files'], str):
      self.ical_files = config['ical_files'].split(',')
    else:
      self.ical_files = config['ical_files']

    # Additional config
    self.timezone = get_system_tz()

    # give an OK message
    print(f'{filename} loaded')

  def generate_image(self):
    """Generate image for this module"""

    # Define new image size with respect to padding
    im_width = int(self.width - (2 * self.padding_left))
    im_height = int(self.height - (2 * self.padding_top))
    im_size = im_width, im_height

    logger.info(f'Image size: {im_size}')

    # Create an image for black pixels and one for coloured pixels
    im_black = Image.new('RGB', size = im_size, color = 'white')
    im_colour = Image.new('RGB', size = im_size, color = 'white')

    # Calculate the max number of lines that can fit on the image
    line_spacing = 1
    line_height = int(self.font.getsize('hg')[1]) + line_spacing
    line_width = im_width
    max_lines = im_height // line_height
    logger.debug(f'max lines: {max_lines}')

    # Create timeline for agenda
    now = arrow.now()
    today = now.floor('day')

    # Load icalendar from config
    self.ical = iCalendar()
    parser = self.ical

    if self.ical_urls:
      parser.load_url(self.ical_urls)

    if self.ical_files:
      parser.load_from_file(self.ical_files)

    # Load events from all icalendar in timerange
    upcoming_events = parser.get_events(today, today.shift(weeks=+52),
                                        self.timezone)
    if upcoming_events:
      upcoming_events = upcoming_events[0:self.maxevents]

    # Sort events by beginning time
    parser.sort()
    #parser.show_events()

    # Set the width for date, time and event titles
    date_width = int(self.font.getsize(today.format(self.dt_format, locale=self.language))[0] * 1.2)

    logger.debug(f'date_width: {date_width}')

    # Calculate positions for each line
    line_pos = [(0, int(line * line_height)) for line in range(max_lines)]
    logger.debug(f'line_pos: {line_pos}')


    cursor = 0

    if self.calname:
      write(im_black, line_pos[cursor], (date_width, line_height),
          self.calname, font = self.font, alignment='left')
      cursor += 1

    # Check if any events were filtered
    if upcoming_events:
      logger.info('Managed to parse events from urls')

      # Find out how much space the event times take
      time_width = int(max([self.font.getsize(
          events['begin'].format(self.dt_format, locale=self.language))[0]
          for events in upcoming_events]) * 1.2)
      logger.debug(f'time_width: {time_width}')

      # Calculate x-pos for time
      x_time = self.timeindent
      logger.debug(f'x-time: {x_time}')

      # Find out how much space is left for event titles
      event_width = im_width - time_width
      logger.debug(f'width for events: {event_width}')

      # Calculate x-pos for event titles
      x_event = time_width + self.eventindent
      logger.debug(f'x-event: {x_event}')

      # Sort the combined list in chronological order of dates
      by_date = lambda event: event['begin']
      upcoming_events.sort(key = by_date)

      for _ in upcoming_events:
        title = _['title']

        ImageDraw.Draw(im_colour).line(
          (0, line_pos[cursor][1], im_width, line_pos[cursor][1]),
        fill = 'black')

        # Check if item is a date
        if not 'end' in _:
          write(im_black, line_pos[cursor], (date_width, line_height),
              title, font = self.font, alignment='left')

          cursor += 1

        # Check if item is an event
        if 'end' in _:
          time = _['begin'].format(self.dt_format, locale=self.language)

          # Check if event is all day, if not, add the time
          if parser.all_day(_) == False:
            write(im_black, (x_time, line_pos[cursor][1]),
                (time_width, line_height), time,
                font = self.font, alignment='left')

          write(im_black, (x_event, line_pos[cursor][1]),
                (event_width, line_height),
                '• '+title, font = self.font, alignment='left')
          cursor += 1

    # If no events were found, write only dates and lines
    else:
      logger.info('no events found')

    # return the images ready for the display
    return im_black, im_colour

if __name__ == '__main__':
  print(f'running {filename} in standalone mode')
