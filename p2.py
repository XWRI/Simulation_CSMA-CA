from p1 import generate_event
from queue import PriorityQueue
import random

DIFS = 10  # 10^-5 sec
SIFS = 5  # 10^-5 sec
WIRELESS_CHANNEL_CAP = 11 * pow(10,1)
CONTENTION_WINDOW = 10
ACK_TRANS_TIME = (64 * 8) / WIRELESS_CHANNEL_CAP # 10^-5 sec
TIMEOUT = 20000 # 10^-5 sec


class Frame(object):
    def __init__(self, time, trans_time, sender, receiver, type, ack, id):
        self.time = time
        self.trans_time = trans_time
        self.sender = sender
        self.receiver = receiver
        self.backoff = 0
        self.num_collision = 0
        self.type = type
        self.ack = ack
        self.id = id
    def __lt__(self, other):
        return self.time < other.time

class Delay(object):
    def __init__(self, id, start):
        self.id = id
        self.start = start

def exp_backoff(num_collision):
    bkoff = int(random.random() * CONTENTION_WINDOW)
    exponential = int(random.random() * pow(2, num_collision))
    backoff_val = bkoff * exponential
    return backoff_val


def generate_frame_length(rate):
    ratio = generate_event(rate)
    while ratio > 1:
        ratio = generate_event(rate)
    return 1544 * ratio


def simulation():

    N = input("Enter the number of hosts: ")
    N = int(N)
    ARRIVAL_RATE = input("Enter the arrival rate: ")
    ARRIVAL_RATE = float(ARRIVAL_RATE)

    channel_busy = False
    channel_idle = True
    countdown = False
    pre_countdonwtime = 0
    amount_countdown = 0

    frame_list = PriorityQueue()
    backed_off_list = []
    wait_for_ack_list = []
    sent_list = []
    total_delay = 0
    trans_delays = []


    for i in range(100000):  #10^-5 sec

        # Generate a new frame
        queue_time = generate_event(ARRIVAL_RATE)
        new_frame = i + queue_time
        total_delay += queue_time
        frame_length = generate_frame_length(ARRIVAL_RATE)
        new_frame_trans_time = (frame_length * 8) / WIRELESS_CHANNEL_CAP #10^-5 sec

        sender = int(random.random() * N)
        receiver = int(random.random() * N)
        while sender == receiver:
            receiver = int(random.random() * N)

        frame_list.put(Frame(new_frame, new_frame_trans_time, sender, receiver, 'S', False, i))

        # Get the closest frame from the list
        cur_frame = frame_list.get()

        # If the current frame is to be sent, we check the scheduled time
        # of transmission
        if cur_frame.type == 'S':
            # If the frame is scheduled to be sent now, we check if the channel
            # is busy
            if int(cur_frame.time)== i:
                # If the channel is busy
                if channel_busy == True:
                    bk_val = exp_backoff(cur_frame.num_collision)
                    cur_frame.num_collision += 1
                    cur_frame.backoff = bk_val + DIFS
                    backed_off_list.append(cur_frame)
                    trans_delays.append(Delay(cur_frame.id, i))

                # If the channel is idle
                if channel_idle == True:
                    receive_time = DIFS + cur_frame.trans_time + i
                    wait_for_ack_list.append(cur_frame)
                    frame_list.put(Frame(receive_time,
                                         cur_frame.trans_time,
                                         cur_frame.sender,
                                         cur_frame.receiver,
                                         'R',
                                         False,
                                         cur_frame.id))
                    channel_busy = True
                    channel_idle = False

                    # If previously we are decrementing the backoff value
                    if countdown == True:
                        countdown = False
                        amount_countdown = i - pre_countdonwtime
                        for frame in backed_off_list:
                            frame.backoff -= amount_countdown

            # If the frame is scheduled to be sent later, we put it back to
            # the list
            else:
                if cur_frame.time < i:
                    bk_val = exp_backoff(cur_frame.num_collision)
                    cur_frame.num_collision += 1
                    cur_frame.backoff = bk_val + DIFS
                    backed_off_list.append(cur_frame)
                    trans_delays.append(Delay(cur_frame.id, i))
                else:
                    frame_list.put(cur_frame)

                # If previously we are decrementing the backoff value
                if countdown == True:
                    amount_countdown = i - pre_countdonwtime

                    # Find if there is a frame that, after decrementing the
                    # back value, has a backoff value of 0
                    frame_to_be_sent = -1
                    collision = False
                    frame_collide = -1
                    # Counting down the backoff value
                    for n in range(len(backed_off_list)):
                        backed_off_list[n].backoff -= amount_countdown
                        if frame_to_be_sent != -1 and backed_off_list[n].backoff == 0:
                            collision = True
                            frame_collide = n
                        if backed_off_list[n].backoff == 0:
                            frame_to_be_sent = n

                    if collision == True:
                        backed_off_list[frame_to_be_sent].num_collision = 0
                        backed_off_list[frame_to_be_sent].backoff_val = 0
                        backed_off_list[frame_collide].num_collision = 0
                        backed_off_list[frame_collide].backoff_val = 0
                    else:
                        # If we find a frame with backoff value 0, we transmit
                        # the frame
                        if frame_to_be_sent == -1:
                            pre_countdonwtime = i
                        else:
                            for delay in trans_delays:
                                if delay.id ==  backed_off_list[frame_to_be_sent].id:
                                    total_delay += i - delay.start
                                    break
                            receive_time = DIFS + backed_off_list[frame_to_be_sent].trans_time + i
                            # Update the frame scheduled transmission time to the
                            # actual transmission time
                            wait_for_ack_list.append(Frame(i,
                                                   backed_off_list[frame_to_be_sent].trans_time,
                                                   backed_off_list[frame_to_be_sent].sender,
                                                   backed_off_list[frame_to_be_sent].receiver,
                                                   'S',
                                                   False,
                                                   backed_off_list[frame_to_be_sent].id))
                            frame_list.put(Frame(receive_time,
                                                 backed_off_list[frame_to_be_sent].trans_time,
                                                 backed_off_list[frame_to_be_sent].sender,
                                                 backed_off_list[frame_to_be_sent].receiver,
                                                 'R',
                                                 False,
                                                 backed_off_list[frame_to_be_sent].id))
                            channel_busy = True
                            channel_idle = False
                            countdown = False

        # If the current frame is to be received
        if cur_frame.type == 'R':
            # If the received frame is an acknowledgement
            if cur_frame.ack == True:
                for m in range(len(wait_for_ack_list)):
                    if wait_for_ack_list[m].id == cur_frame.id:
                        sent_list.append(wait_for_ack_list.pop(m))
                channel_idle = True
            # We send an acknowledgement if the received frame is not
            else:
                frame_list.put(Frame(ACK_TRANS_TIME + SIFS,
                                     ACK_TRANS_TIME,
                                     cur_frame.sender,
                                     cur_frame.receiver,
                                     'R',
                                     True,
                                     cur_frame.id))

        # If the channel is idle, we start the count down of backoff value
        if channel_idle == True:
            countdown = True
            pre_countdonwtime = i

        # If there is a timeout and need fo retransmission
        for j in range(len(wait_for_ack_list)):
            if i - wait_for_ack_list[j].time > TIMEOUT:
                wait_for_ack_list[j].num_collision = 0
                wait_for_ack_list[j].backoff_val = 0
                backed_off_list.append(wait_for_ack_list[j])
                wait_for_ack_list.pop(j)


    print(len(sent_list))
    total_bytes_trans = 0
    for frame in sent_list:
        total_bytes_trans += frame.trans_time * WIRELESS_CHANNEL_CAP / 8
    print("throughput: ")
    print(total_bytes_trans)

    print("Average network delay: ")
    total_delay = total_delay / pow(10, 5)
    print(total_delay/len(sent_list))
