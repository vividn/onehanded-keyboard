import evdev
import time
from evdev import ecodes
from select import select
from inputEventCreator import add_input_to_queue, process_queue
import asyncio

deviceName = "DaKai 2.4G RX"

kbds = []
# Load all the relevant devices
allDevices = [evdev.InputDevice(dv) for dv in evdev.list_devices()]
for dev in allDevices:
    if deviceName in dev.name:
        kbds.append(dev)

        # Make this program the exclusive handler of this device
        dev.grab()

# Define an asynchronous event handler
async def add_events(device):
    async for event in device.async_read_loop():
        if event.type == 1 and event.value < 2:
            add_input_to_queue(event)

async def procQ():
    while True:
        process_queue()
        await asyncio.sleep(0.1)

for dev in kbds:
    asyncio.ensure_future(add_events(dev))

asyncio.ensure_future(procQ())

loop = asyncio.get_event_loop()
loop.run_forever()


