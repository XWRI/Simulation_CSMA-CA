from p1 import generate_event
from queue import PriorityQueue
import random

N = 10
DIFS = 0.1  #msec
SIFS = 0.05  #msec
ARRIVAL_RATE = 0.1
WIRELESS_CHANNEL_CAP = 11
ACK_TRANS_TIME = (64 * 8) / (WIRELESS_CHANNEL_CAP * pow(10, 6))
TIMEOUT = 2 #msec


class Frame(object):
    def __init__(self, time, trans_time, send, receiver, type, ack, id):
        self.time = time
        self.trans_time = trans_time
        self.receiver = receiver
        self.backoff = 0
        self.num_collision = 0
        self.type = type
        self.ack = ack
        self.id = id
    def __lt__(self, other):
        return self.time < other.time

def exp_backoff(num_collision):
    bkoff = int(random.random() * 100)
    exponential = int(random.random() * pow(2, num_collision))
    backoff_val = bkoff * exponential
    return backoff_val


def generate_frame_length():
    return 1544 * generate_event(ARRIVAL_RATE)


def simulation():
    channel_busy = False
    channel_idle = True
    countdown = False
    pre_countdonwtime = 0
    amount_countdown = 0

    frame_list = PriorityQueue()
    backed_off_list = []
    sent_list = []


    for i in range(10000):

        # Generate a new frame
        new_frame = i + generate_event(ARRIVAL_RATE)
        frame_length = generate_frame_length()
        new_frame_trans_time = (frame_length * 8) / (WIRELESS_CHANNEL_CAP * pow(10,6))

        sender = int(random.random() * N)
        receiver = int(random.random() * N)
        while sender == receiver:
            receiver = int(random.random() * N)

        frame_list.put(Frame(new_frame, new_frame_trans_time, sender, receiver, 'S', False, i))

        # Get the closest frame from the list
        cur_frame = frame_list.get()

        # frame1 : 3 already sent, finish at 6
        # frame2 : 5 + 2
        # frame3 : 10
        # i == 3
        # i == 7, channel idle

        # t = 8: frame2 : backoff = 0

        # If the current frame is to be sent, we check the scheduled time
        # of transmission
        if cur_frame.type == 'S':

            # If the frame is scheduled to be sent now, we check if the channel
            # is busy
            if cur_frame.time == i:

                # If the channel is busy
                if channel_busy == True:
                    bk_val = exp_backoff(cur_frame.num_collision)
                    cur_frame.num_collision += 1
                    cur_frame.backoff = bk_val
                    backed_off_list.append(cur_frame)

                # If the channel is idle
                if channel_idle == True:
                    receive_time = DIFS + cur_frame.trans_time + i
                    sent_list.append(cur_frame)
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
                frame_list.put(cur_frame)

                # If previously we are decrementing the backoff value
                if countdown == True:
                    amount_countdown = i - pre_countdonwtime

                    # Find if there is a frame that, after decrementing the
                    # back value, has a backoff value of 0
                    frame_to_be_sent = -1
                    # Counting down the backoff value
                    for i in range(len(backed_off_list)):
                        backed_off_list[i].backoff -= amount_countdown
                        if backed_off_list[i].backoff == 0:
                            frame_to_be_sent = i

                    # If we find a frame with backoff value 0, we transmit
                    # the frame
                    if frame_to_be_sent == -1:
                        pre_countdonwtime = i
                    else:
                        receive_time = DIFS + backed_off_list[i].trans_time + i
                        # Update the frame scheduled transmission time to the
                        # actual transmission time
                        sent_list.append(Frame(i,
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
                for i in range(len(sent_list)):
                    if sent_list[i].id == cur_frame.id:
                        sent_list.pop(i)
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

        if channel_busy == True:
            for frame in backed_off_list:
                bk_val = exp_backoff(frame.num_collision)
                frame.num_collision += 1
                frame.backoff = bk_val

        # If there is a timeout and need fo retransmission
        for frame in sent_list:
            if i - frame.time > TIMEOUT:
                frame_list.put(frame)
