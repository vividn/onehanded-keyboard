#!/usr/bin/python3

import evdev
from evdev import UInput, ecodes as e
import re
from ast import literal_eval as make_tuple
from itertools import permutations
import os

# Create an event source that can write input events to the system
ui = UInput()

# Create an inputQueue where input events (with key coordinates) are stored
inputQueue = []

# Create dictionary for modifiers
modKeys = {}
sModKeys = {}

# Create a dictionary for the final mapping of key-coordiantes to outputs
keymap = {}
# Load the keymap
with open("keymap.conf", "r") as keymapfile:
    for line in keymapfile:

        # Remove comments
        command = line.split("#")[0].strip()

        # Skip blank or comment-only lines
        if (not (command)): continue

        # If a key is designated as a modifer add it to the appropriate list
        p = re.compile('^(S?MOD)\[(\w+)\] (\([^\)]+\))')
        m = p.search(line)
        if m:
            # Extract the groups
            modType, modName, keyPos = m.groups()

            # Turn keyPos into a tuple
            keyPos = make_tuple(keyPos)

            # Sort into MOD and SMOD
            if modType == 'MOD':
                modKeys[modName] = keyPos
            elif modType == 'SMOD':
                sModKeys[modName] = keyPos
            else:
                raise Exception("Bad keymap, unknown modifier type")


        else:
            # Otherwise parse the line

            # Separate the key input from the key output and strip of whitespace
            lineparts = [part.strip() for part in line.split("=")]
            keyOutput = [part.strip() for part in lineparts[1].split("+")]

            # Now split up the input based on +'s and parse for modifiers
            unparsedInput = [part.strip() for part in lineparts[0].split("+")]
            keyInput = []

            for key in unparsedInput:
                # Test if of the form [ABC] which is a modifier
                p = re.compile('\[(\w+)\]')
                m = p.match(key)
                if m:
                    modName = m.groups()[0]
                    # Ensure that this modifier has been defined earlier
                    if modName in modKeys:
                        keyInput.append(modKeys[modName])
                    elif modName in sModKeys:
                        keyInput.append(sModKeys[modName])
                    else:
                        raise Exception("Bad keymap, modifier not defined. Line:\n{0}".format(line))

                else:
                    # Parse the input as a tuple
                    keyInput.append(make_tuple(key))

            # Now keyInput has a series of tuples that correspond to the key chord that needs to be pressed to activate the output
            # Permutate all the possible key combos and put them into the keymap dictionary
            for permute in permutations(keyInput):
                keymap[permute] = keyOutput

# Create a dictionaty for the mapping of keycodes to key-coordinates
inputCodeMap = {}
# Load the input key mapping
with open("Dakai_Map.conf", "r") as inputmapfile:
    for line in inputmapfile:

        # Remove comments
        command = line.split("#")[0].strip()

        # Skip blank or comment-only lines
        if (not (command)): continue

        # Separate the keycode from the key-coordinate and strip of whitespace
        lineparts = [part.strip() for part in line.split("=")]

        keycode = int(lineparts[0])
        coordinate = make_tuple(lineparts[1])

        # Add to the dictionary
        inputCodeMap[keycode] = coordinate


# Now that the files have been parsed define some functions for interpreting input and writing keys


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







