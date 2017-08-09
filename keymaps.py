import evdev
from evdev import UInput, ecodes as e
import re
from ast import literal_eval as make_tuple
from itertools import permutations
import os

# Create dictionary for modifiers
modKeys = {}
sModKeys = {}

# Create a dictionary for the final mapping of key-coordinates to outputs
outputMap = {}

# Load the keymap
with open("keymap.conf", "r") as keymapfile:
    for line in keymapfile:

        # Remove comments
        line = line.split("#")[0].strip()

        # Skip blank or comment-only lines
        if (not (line)): continue

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
                outputMap[permute] = keyOutput

# Create a dictionary for the mapping of keycodes to key-coordinates
inputMap = {}

# Load the input key mapping
with open("Dakai_Map.conf", "r") as inputmapfile:
    for line in inputmapfile:

        # Remove comments
        line = line.split("#")[0].strip()

        # Skip blank or comment-only lines
        if (not (line)): continue

        # Separate the keycode from the key-coordinate and strip of whitespace
        lineparts = [part.strip() for part in line.split("=")]

        keycode = int(lineparts[0])
        coordinate = make_tuple(lineparts[1])

        # Add to the dictionary
        inputMap[keycode] = coordinate
