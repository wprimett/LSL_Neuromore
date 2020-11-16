#Code base taken from: https://github.com/ViacheslavBobrov/LSL_Neuromore
#Adapted for OpenSignals->LSL->OSC
from pylsl import StreamInlet, resolve_byprop
from pythonosc import udp_client
from threading import Thread
from time import sleep

import json

class LslToOscStreamer:

    def __init__(self, host, port, stream_channels):
        self.client = udp_client.SimpleUDPClient(host, port)
        self.inlet = None
        self.stream_channels = stream_channels
        self.is_streaming = False

    def connect(self, prop='type', value='INSERT_MAC_ADDRESS'):
        streams = resolve_byprop(prop, value, timeout=5)
        self.inlet = StreamInlet(streams[0], max_chunklen=12)
        return self.inlet is not None

    def stream_data(self):
        if self.inlet is None:
            raise Exception("LSL stream is not connected")
        self.is_streaming = True
        streaming_thread = Thread(target=self._stream_handler)
        streaming_thread.setDaemon(True)
        streaming_thread.start()

    def _stream_handler(self):
        while self.is_streaming:
            eeg_sample, _ = self.inlet.pull_sample()
            for channel_idx, channel in enumerate(self.stream_channels):
                self.client.send_message(channel, eeg_sample[channel_idx])

    def close_stream(self):
        self.is_streaming = False
        self.inlet.close_stream()


if __name__ == "__main__":
    try:
        device_file_path = "device_list.json"
        # device_file_path = "~/Documents/OpenSignals\\(r)evolution/configurations/device_list.json"
        with open(device_file_path, "r") as read_file:
            device_list = json.load(read_file)
        default_device = device_list[list(device_list.keys())[0]]
        mac_addr = default_device['mac']
    except Exception as e:
        print(e)
        print("unable to read device_list.json file")
        print("Please copy configuration from OpenSignals (r)evolution directory")
        exit()

    host = "127.0.0.1"
    port = 4545
    stream_time_sec = 3600
    bitalino_channels = ["/bitalino/nSeq"]
    for channel_idx, channel in enumerate(default_device["activeChannels"]):
        if channel != 0:
            bitalino_channels.append("/bitalino/" + default_device["labelChannels"][channel_idx])

    streamer = LslToOscStreamer(host, port, bitalino_channels)
    streamer.connect(value = mac_addr)

    print("Start streaming data to {}:{} for {} seconds".format(host, port, stream_time_sec))
    streamer.stream_data()
    sleep(stream_time_sec)
    streamer.close_stream()
    print("Stopped streaming. Exiting program...")
