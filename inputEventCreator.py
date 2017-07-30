#!/usr/bin/python3

import evdev
from evdev import UInput, ecodes as e
import re
from ast import literal_eval as make_tuple
from itertools import permutations
import os

from keymaps import modKeys, sModKeys, outputMap, inputMap

# Create an event source that can write input events to the system
ui = UInput()

# Create an inputQueue where input events (with key coordinates) are stored
inputQueue = []



def add_input_to_queue(evdevEvent):
    ## Input from the key device is grabbed as evdev events
    # Process this event into a dictionary that
    keycode = evdevEvent.code
    coord = inputCodeMap[keycode]
    eventTime = evdevEvent.sec
    keyState = evdevEvent.value



    inputQueue.append({'coord': coord, 'time': eventTime, 'state': keyState, 'keycode': keycode})


def process_queue():
    # Sort the queue by time of events
    inputQueue = sorted(inputQueue, key=itemgetter('time'))

    while length(inputQueue) > 0:
        (coord_list, indices_to_delete) = process_queue_helper(inputQueue)
        write_from_coords(coord_list)

        for i in sorted(indices_to_delete, reverse=True):
            del inputQueue[i]


def process_queue_helper(queue):

    # If the top event on the queue is a key release action, just delete the entry.
    if queue[0]['state'] == 0:
        coord_list = []

    # S
    elif

    return (coord_list, indices_to_delete)


def write_from_coords(coord_list):
    ## Output the key stroke events to the computer

    # Turn the coordinates into their appropriate list of key names to be outputted
    ecode_list = get_ecode_list(coord_list)

    # Get the integer key value for each key name (e.g., KEY_A -> 30)
    ecodes = [e.ecodes[str] for str in ecode_list]

    # First press down each key sequentially
    for ecode in ecodes:
        ui.write(e.EV_KEY, ecode, 1)

    # Then release each key sequentially
    for ecode in ecodes:
        ui.write(e.EV_KEY, ecode, 0)



def get_ecode_list(coord_list):
    # Return [] if coord_list is empty
    if not coord_list:
        return []

    # Searches through the keymap for the given chord
    if coord_list in keymap:
        return keymap[coord_list]

    else:
        # If not directly in the keymap test the use of the first key as a modifier
        if coord_list[0] in modKeys.values():
            return keymap[coord_list[0]] + get_ecode_list(coord_list[1:])







