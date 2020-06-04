import queue
from queue import PriorityQueue
from random import random
from math import log


class Event(object):
    def __init__(self, type, time, service_time):
        self.type = type
        self.time = time
        self.service_time = service_time
    def __lt__(self, other):
        return self.time < other.time


arriving_rate = 0.90
MAX_BUFFER = inf

def generate_event (rate):
     u = random()
     return ((-1/rate)*log(1-u))

def simulation():
    global_event_list = PriorityQueue()
    buffer = []
    cur_time = 0

    prev_time_server = 0
    server_busy = False
    server_busy_time = 0

    total_num_packets = 0
    prev_time_packets = 0
    total_num_dropped = 0

    first_event = generate_event(arriving_rate)
    event_service_time = generate_event(transmission_rate)
    global_event_list.put(Event('A', first_event + cur_time, event_service_time))

    for i in range(100000):
        if global_event_list.empty() == True:
            break

        cur_event = global_event_list.get()
        cur_time = cur_event.time

        if cur_event.type == 'A':
            next_arrival_event = generate_event(arriving_rate) + cur_time
            event_service_time = generate_event(transmission_rate)
            global_event_list.put(Event('A', next_arrival_event, event_service_time))

            if server_busy == False:
                next_depart_event = cur_event.service_time + cur_time
                global_event_list.put(Event('D', next_depart_event, 0))
                server_busy = True
                prev_time_server = cur_time
            else:
                if len(buffer) < MAX_BUFFER:
                    if len(buffer) != 0:
                        total_num_packets += (len(buffer) + 1) * (cur_time - prev_time_packets)
                    buffer.append(cur_event)
                    prev_time_packets = cur_time
                else:
                    total_num_dropped += 1
        else:
            if len(buffer) != 0:
                new_event = buffer[0]

                total_num_packets += (len(buffer) + 1) * (cur_time - prev_time_packets)
                buffer = tail(buffer)
                prev_time_packets = cur_time

                next_depart_event = new_event.service_time + cur_time
                global_event_list.put(Event('D', next_depart_event, 0))
            else:
                server_busy = False
                server_busy_time += cur_time - prev_time_server

    utilization = server_busy_time / cur_time
    mean_queue_length = total_num_packets / cur_time
    print("utilization")
    print(utilization)
    print("mean queue length")
    print(mean_queue_length)
    print("number of packets dropped")
    print(total_num_dropped)


def tail(lst):
    return lst[1:]
