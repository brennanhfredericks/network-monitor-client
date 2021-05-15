import sys
sys.path.insert(0, "../")

import base64

import asyncio

import os
import time
import collections
import aiofiles
import json

from aiologger import Logger

from network_monitor import (
    Service_Manager,
    Interface_Listener,
)

from network_monitor.protocols import (
    AF_Packet,
    Packet_802_3,
    TCP,
    UDP,
    IGMP,
    ICMP,
    ICMPv6,
    IPv4,
    IPv6,
    ARP,
    LLDP,
    CDP,
)
from network_monitor.filters import get_protocol, present_protocols

# write to tmp file and replace with os.replace



async def _log_raw(queue):
    start_time = int(time.time())
    log_dir="./test/data/raw/"
    report_interval= 5

    fname = f"raw2_protocols_{start_time}.lp"

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    tracker = collections.Counter()
    last_report_time = time.time()

    async with aiofiles.open(os.path.join(log_dir, fname), "w") as fout:
        while True:
            try:
                _,(raw_bytes, address) = await queue.get()
               
                af_packet = AF_Packet(address)

            
                if af_packet.Ethernet_Protocol_Number > 1500:
                    out_packet = Packet_802_3(raw_bytes)
                else:
                    out_packet = Packet_802_2(raw_bytes)
                
                await fout.write(json.dumps(af_packet.serialize()) + "\n")
                r_raw_bytes = base64.b64encode(raw_bytes).decode("utf-8")

                await fout.write(r_raw_bytes + "\n")

                queue.task_done()
            
                for identifier in present_protocols(out_packet):
                    tracker[identifier] += 1    

                now = time.time()
                if now - last_report_time > report_interval:
                    __tracker = {k: v for k, v in tracker.items()}
                    last_report_time = now
                    print("queue size: ",queue.qsize())
                    print("Tracker: ",__tracker)
            except asyncio.CancelledError as e:

                print("log service cancelled", e)

                raise e
            


async def log_packets_based_on_protocols(
    interfacename: str,

):
    
    raw_queue = asyncio.Queue()
 
    logger = Logger.with_default_handlers()


    # start network listener
    listener_service = Interface_Listener(interfacename, raw_queue)
    
    listener_service_task: Task = asyncio.create_task(
        listener_service.worker(logger), name="listener-service-task")

    log_task = asyncio.create_task(_log_raw(raw_queue))
    await asyncio.sleep(600)
    listener_service_task.cancel()
    print("listener task cancelled")
    await raw_queue.join()
    print("raw queue empty")
    await asyncio.sleep(2)
    log_task.cancel()
    print("log task cancelled")
    await asyncio.gather(listener_service_task,log_task,return_exceptions=True)


if __name__ == "__main__":

    asyncio.run(log_packets_based_on_protocols(
        "eth0"
    ))
