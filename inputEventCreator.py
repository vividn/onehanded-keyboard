import time
from evdev import UInput, ecodes as e
import config
from operator import itemgetter
from keymaps import modKeys, sModKeys, outputMap, inputMap

# Create an event source that can write input events to the system
ui = UInput()

# Create an inputQueue where input events (with key coordinates) are stored
inputQueue = []



def add_input_to_queue(evdevEvent):
    ## Input from the key device is grabbed as evdev events
    # Process this event into a dictionary that
    keycode = evdevEvent.code
    coord = inputMap[keycode]
    eventTime = evdevEvent.sec
    keyState = evdevEvent.value



    inputQueue.append({'coord': coord, 'time': eventTime, 'state': keyState, 'keycode': keycode})


def process_queue():
    # Sort the queue by time of events
    global inputQueue
    inputQueue = sorted(inputQueue, key=itemgetter('time'))

    while len(inputQueue) > 0:
        (coord_list, indices_to_delete) = process_queue_helper(inputQueue)
        write_from_coords(coord_list)

        for i in sorted(indices_to_delete, reverse=True):
            del inputQueue[i]


def process_queue_helper(queue):

    nKeys = len(queue)

    # Return if input queue is empty
    if nKeys == 0:
        return (),()

    # If the top event on the queue is a key release action, just delete the entry.
    if queue[0]['state'] == 0:
        return (),(0,)

    # Get which type of key the first key is
    if queue[0]['coord'] in sModKeys:
        keyType = 'SMOD'
    elif queue[0]['coord'] in modKeys:
        keyType = 'MOD'
    else:
        keyType = 'NORMAL'

    if nKeys >= 2:

        # If the second event is just releasing the button (no chord has occurred)
        if queue[1]['coord'] == queue[0]['coord']:

            if keyType == 'SMOD' and time.time() - queue[0]['time'] <= smodStickTime:
                # Wait for more input if a sticky modifier is pressed
                coord_list = ()
                indices_to_delete = ()

            else:
                # Return just key otherwise
                coord_list = (queue[0]['coord'],)
                indices_to_delete = (0,1)

        # If the next key occurs quickly or first key is a modifier, treat the input as a key chord
        elif queue[1]['time'] - queue[0]['time'] <= config.chordTime or keyType != 'NORMAL':
            # Call process_queue_helper recursively to allow for arbitrarily big key chords
            [sub_coords, sub_inds] = process_queue_helper(queue[1:-1])

            coord_list = (queue[0]['coord'],) + sub_coords
            indices_to_delete = (0,) + (i + 1 for i in sub_coords)

        # Otherwise, just output the key by itself
        else:
            coord_list = (queue[0]['coord'],)
            indices_to_delete = (0,)

    else:
        # Only one event in queue

        # Output the key if NORMAL key and the time for key chords has passed
        if keyType == 'NORMAL' and time.time() - queue[0]['time'] > config.chordTime:
            coord_list = (queue[0]['coord'],)
            indices_to_delete = (0,)

        else:
            # Otherwise, just wait for more key presses to come in
            coord_list = ()
            indices_to_delete = ()

    return coord_list, indices_to_delete


def write_from_coords(coord_list):
    # Output the key stroke events to the computer

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
    if coord_list in outputMap:
        return keymap[coord_list]

    else:
        # If not directly in the keymap test the use of the first key as a modifier
        if coord_list[0] in modKeys.values():
            return keymap[coord_list[0]] + get_ecode_list(coord_list[1:])







