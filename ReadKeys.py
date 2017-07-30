import evdev
from evdev import ecodes
from select import select
from inputEventCreator import add_input_to_queue, process_queue

deviceName = "DaKai 2.4G RX"

kbds = []
# Load all the relevant devices
allDevices = [evdev.InputDevice(dv) for dv in evdev.list_devices()]
for dev in allDevices:
    if deviceName in dev.name:
        kbds.append(dev)

        # Make this program the exclusive handler of this device
        dev.grab()

# Create a dictionary that references the input device by its file descriptor
kbds = {dev.fd: dev for dev in kbds}

# Now continuously loop and read in input events
while True:
    r, w, x = select(kbds, [], [])
    for fd in r:
        for event in kbds[fd].read():
            if event.type == 1 and event.value < 2:
                add_input_to_queue(event)

    process_queue()