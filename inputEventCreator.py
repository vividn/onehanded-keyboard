import time
from evdev import UInput, ecodes as e
import config
from operator import itemgetter
from keymaps import modKeys, sModKeys, outputMap, inputMap
import warnings

# Create an event source that can write input events to the system
ui = UInput()

# Create an inputQueue where input events (with key coordinates) are stored
inputQueue = []

# Turn off numlock (program starts with numlock on automatically)
ui.write(e.EV_KEY, e.KEY_NUMLOCK, 1)
ui.write(e.EV_KEY, e.KEY_NUMLOCK, 0)
ui.syn()

def add_input_to_queue(evdevEvent):
    # Input from the key device is grabbed as evdev events
    # Process this event into a dictionary that
    keycode = evdevEvent.code
    coord = inputMap[keycode]
    # TODO: Put warning if no match for the keycode exists
    eventTime = evdevEvent.timestamp()
    keyState = evdevEvent.value



    inputQueue.append({'coord': coord, 'time': eventTime, 'state': keyState, 'keycode': keycode})


def process_queue():
    # Sort the queue by time of events
    global inputQueue
    inputQueue = sorted(inputQueue, key=itemgetter('time'))

    (coord_list, indices_to_delete, mark_used) = process_queue_helper(inputQueue)
    write_from_coords(coord_list)

    for i in mark_used:
        inputQueue[i]['used'] = True

    for i in sorted(indices_to_delete, reverse=True):
        del inputQueue[i]


def process_queue_helper(queue):

    nKeys = len(queue)

    # By default send nothing, delete nothing, and mark nothing unless explicitly stated
    coord_list = ()
    indices_to_delete = ()
    mark_used = ()

    # Return if input queue is empty
    if nKeys == 0:
        return (),(),()

    # If the top event on the queue is a key release action, just delete the entry.
    if queue[0]['state'] == 0:
        return (),(0,),()

    # Get which type of key the first key is
    if queue[0]['coord'] in sModKeys.values():
        keyType = 'SMOD'
    elif queue[0]['coord'] in modKeys.values():
        keyType = 'MOD'
    else:
        keyType = 'NORMAL'

    if nKeys == 1:
        # Only one event in queue

        # Output the key if it is NORMAL and sufficient time waiting for key chords has passed
        if keyType == 'NORMAL' and time.time() - queue[0]['time'] > 2 * config.chordTime:
            coord_list = (queue[0]['coord'],)
            indices_to_delete = (0,)

        # Otherwise, just wait for more key presses to come in

    else:  # More than 1 event in the queue

        # Do different things depending on which kind of key this is
        if keyType == 'NORMAL':
            # If the key type is NORMAL, then one of two things can happen, either the key is by itself or
            # part of a chord

            # If the second event is just releasing the button (no chord has occurred)
            if queue[1]['coord'] == queue[0]['coord']:
                # Return just key
                coord_list = (queue[0]['coord'],)
                indices_to_delete = (0,1)

            else: # The event is some other key
                # This is a key chord if the second press is a key press (not release) and occurs within the key chord time
                if queue[1]['state'] == 1 and queue[1]['time'] - queue[0]['time'] <= config.chordTime:
                    # Call process_queue_helper recursively to allow for arbitrarily big key chords
                    [sub_coords, sub_inds, sub_marks] = process_queue_helper(queue[1:])

                    # Only send the key chord if the recursive call returns anything
                    if sub_coords:
                        coord_list = (queue[0]['coord'],) + sub_coords
                        indices_to_delete = (0,) + tuple(i + 1 for i in sub_inds)

                    else:
                        # Just delete what the subroutine says to
                        indices_to_delete = tuple(i + 1 for i in sub_inds)

                # Otherwise, just return the first key
                else:
                    coord_list = (queue[0]['coord'],)
                    indices_to_delete = (0,)


        elif keyType == 'MOD':
            # MOD keys must be pressed and held for them to stay active

            # If the next key is just the mod key being released, then send the MOD key by itself
            # That is, unless it has been used with some other keys first
            if queue[1]['coord'] == queue[0]['coord']:

                # If the MOD key has been used in conjunction with other keys, just delete the key down and up events
                if 'used' in queue[0] and queue[0]['used']:
                    indices_to_delete = (0,1)

                # Otherwise play the MOD key
                else:
                    coord_list = (queue[0]['coord'],)
                    indices_to_delete = (0,1)

            # Recursively call the this process_queue_helper function to process key coords that occur with the MOD key attached
            else:
                [sub_coords, sub_inds, sub_marks] = process_queue_helper(queue[1:])

                # Only send key input if the recursive call returns anything
                if sub_coords:
                    coord_list = (queue[0]['coord'],) + sub_coords
                    # Mark the mod key as used so it won't return its own input later
                    mark_used = (0,)

                indices_to_delete = tuple(i + 1 for i in sub_inds)
                mark_used = mark_used + tuple(i + 1 for i in sub_marks)


        elif keyType == 'SMOD':

            # If the SMOD key is pressed and released, it acts like it sticks
            # allowing another key or key chord to be pressed afterwards for smodStickTime
            if queue[1]['coord'] == queue[0]['coord']:

                # If the SMOD key has already been used in conjunction with other (i.e. not in a sticky way),
                # just delete the key down and up events
                if 'used' in queue[0] and queue[0]['used']:
                    indices_to_delete = (0, 1)

                elif time.time() - queue[0]['time'] <= config.smodStickTime:
                    # Recursively call the this process_queue_helper function to process the first key or key chord that occurs after the SMOD key
                    [sub_coords, sub_inds, sub_marks] = process_queue_helper(queue[2:])

                    if sub_coords:
                        coord_list = (queue[0]['coord'],) + sub_coords
                        indices_to_delete = (0,1) + tuple(i + 2 for i in sub_inds)
                    else:
                        indices_to_delete = tuple(i + 2 for i in sub_inds)

                    mark_used = tuple(i + 2 for i in sub_marks)

                else: # Time has expired, just play the SMOD key by itself
                    coord_list = (queue[0]['coord'],)
                    indices_to_delete = (0,1)


            else: # SMOD key is being held and acts just like a MOD key
                [sub_coords, sub_inds, sub_marks] = process_queue_helper(queue[1:])

                # Only send key input if the recursive call returns anything
                if sub_coords:
                    coord_list = (queue[0]['coord'],) + sub_coords
                    # Mark the SMOD key as used so it won't act sticky or return its own input later
                    mark_used = (0,)

                indices_to_delete = tuple(i + 1 for i in sub_inds)
                mark_used = mark_used + tuple(i + 1 for i in sub_marks)


    return coord_list, indices_to_delete, mark_used


def write_from_coords(coord_list):
    # Output the key stroke events to the computer

    # Only do this if the coord_list is not empty
    if coord_list:
        # Turn the coordinates into their appropriate list of key names to be outputted
        ecode_list = get_ecode_list(coord_list)

        # Get the integer key value for each key name (e.g., KEY_A -> 30)
        ecodes = [e.ecodes[str] for str in ecode_list if str]

        # First press down each key sequentially
        for ecode in ecodes:
            ui.write(e.EV_KEY, ecode, 1)

        # Then release each key sequentially
        for ecode in ecodes:
            ui.write(e.EV_KEY, ecode, 0)

        # Now send these writes to the system
        ui.syn()





def get_ecode_list(coord_list):
    # Return [] if coord_list is empty
    if not coord_list:
        return []

    # Catch Key Errors, if some key has an undefined output
    try:
        # Searches through the keymap for the given chord
        if coord_list in outputMap:
            return outputMap[coord_list]

        else:
            # If not directly in the keymap test the use of any of the keys as modifiers and then pull them out front
            for key_coord in coord_list:
                if key_coord in modKeys.values() or key_coord in sModKeys.values():
                    coord_list = tuple(coord for coord in coord_list if coord != key_coord)
                    return outputMap[(key_coord,)] + get_ecode_list(coord_list)

            # Otherwise, just return the each key independently
                return tuple(outputMap[(coord,)] for coord in coord_list)

    except KeyError:
        warnings.warn('Some undefined key has been used')
        return ()
        pass






