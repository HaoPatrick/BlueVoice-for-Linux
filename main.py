import Node as stl
import Scanner as scr
from bluepy.btle import UUID, Scanner, BTLEException
from collections import deque
from threading import Thread
import os
import argparse
from util import c_str
from subprocess import call
import signal
from signal import SIGPIPE, SIG_DFL

signal.signal(SIGPIPE, SIG_DFL)

T_COLOR = {} if os.getenv('C', '1') == '0' else {
  'RED': '\033[31m',
  'GREEN': '\033[32m',
  'YELLOW': '\033[33m',
  'CYAN': '\033[36m',
  'WHITE': '\033[37m',
  'OFF': '\033[0m'
}
if os.getenv('C', '1') == '0':
  ANSI_RED = ''
  ANSI_GREEN = ''
  ANSI_YELLOW = ''
  ANSI_CYAN = ''
  ANSI_WHITE = ''
  ANSI_OFF = ''
else:
  ANSI_CSI = "\033["
  ANSI_RED = ANSI_CSI + '31m'
  ANSI_GREEN = ANSI_CSI + '32m'
  ANSI_YELLOW = ANSI_CSI + '33m'
  ANSI_CYAN = ANSI_CSI + '36m'
  ANSI_WHITE = ANSI_CSI + '37m'
  ANSI_OFF = ANSI_CSI + '0m'

queue_audio = deque()


def back_up_config(freq: int) -> None:
  # make a backup of original configuration files
  call(["cp", "/home/pi/.asoundrc", "/home/pi/.asoundrc_bkp"])
  call(["scp", "/etc/asound.conf", "/etc/asound_bkp.conf"])
  if freq == 16000:
    call(["cp", "./asoundrc_template_16KHz", "/home/pi/.asoundrc"])
    call(["scp", "./asoundrc_template_16KHz", "/etc/asound.conf"])
  else:
    call(["cp", "./asoundrc_template_8KHz", "/home/pi/.asoundrc"])
    call(["scp", "./asoundrc_template_8KHz", "/etc/asound.conf"])


def init_audio(d_out, frq):
  global stream
  
  back_up_config(frq)
  
  import sounddevice as sd
  sd.default.channels = 1
  sd.default.dtype = 'int16'
  dev_index = -1
  dev_freq = -1
  
  if d_out == "stl_capture":
    device_name = "STL_playback"
    dev_index = sd.query_devices().index(sd.query_devices(device=device_name))
    dev_freq = sd.query_devices(device="STL_playback")["default_samplerate"]
    print("DEVICE: {}  INDEX:  {}  RATE:  {}".format(device_name, dev_index, dev_freq))
    print("{}MIC DEVICE: {}  INDEX:  {}  RATE:  {}  CH:  {}".format(T_COLOR.get('CYAN', ''),
                                                                    "STL_capture",
                                                                    sd.query_devices().index(
                                                                      sd.query_devices(device="STL_capture")),
                                                                    dev_freq, sd.default.channels) + ANSI_OFF)
  elif d_out == "alsa_playback":
    dev_index = sd.query_devices().index(sd.query_devices(device="default"))
    dev_freq = sd.query_devices(device="STL_playback")["default_samplerate"]
    print("DEVICE: {}  INDEX:  {}  RATE:  {}".format(
      sd.query_devices(device="default")["name"], dev_index, dev_freq))
  
  sd.default.device = dev_index
  stream = sd.RawOutputStream(samplerate=dev_freq)


do_process = True


def audio_player():
  global stream
  while True:
    if len(queue_audio) >= 20:
      play = b''.join(queue_audio)
      queue_audio.clear()
      stream.write(play)
    if not do_process:
      break


def audio_getter():
  global brd
  while True:
    brd.mAudio.audio_stream(queue_audio)
    if not do_process:
      break


def signal_handler(signal, frame):
  print('You have pressed Ctrl+C!')
  call(["mv", "/home/pi/.asoundrc_bkp", "/home/pi/.asoundrc"])
  call(["scp", "/etc/asound_bkp.conf", "/etc/asound.conf"])
  call(["rm", "/etc/asound_bkp.conf"])
  global do_process
  do_process = False


def main():
  global brd
  global stream
  global ff
  timeout_sc = 2
  n_dev = -1
  
  # Instantiate the parser
  parser = argparse.ArgumentParser(description='BV_Link_rbpi3 application')
  # Required positional argument
  parser.add_argument('output_config', type=str,
                      help='[alsa_playback] to playback directly to the speaker.'
                           ' [stl_capture] to create a virtual microphone')
  parser.add_argument('freq_config', type=int, help='[16000] to set 16KHz frequency.[8000] to set 8KHz frequency')
  args = parser.parse_args()
  if args.output_config != "alsa_playback" and args.output_config != "stl_capture":
    parser.error("output_config required, type -h to get more information")
  
  if args.freq_config != 16000 and args.freq_config != 8000:
    parser.error("freq_config required, type -h to get more information")
  
  # scanning phase
  sc = scr.ScanPrint()
  print(c_str("Scanning for devices...", 'RED'))
  try:
    hci0 = 0
    Scanner(hci0).withDelegate(sc).scan(timeout_sc)
  except BTLEException as e:
    print("/dev/hci0 failed with {}, try /dev/hci1".format(e))
    hci0 = 1
    Scanner(hci0).withDelegate(sc).scan(timeout_sc)
  devices = sc.devices
  
  if len(devices) > 0:
    print("Type the index of device to connect (eg. " + str(devices[0].get('index')) +
          " for " + devices[0].get('name') + " device)...")
  else:
    print("no device found")
    exit()
  try:
    n_dev = int(input('Input:'))
  except ValueError:
    print(" Not a number")
    exit()
  
  if (n_dev in range(1, len(devices) + 1)) and n_dev > 0:
    print("Valid device")
  else:
    print(" Not valid device")
    exit()
  
  # connection
  device = devices[n_dev - 1]
  print('Connecting to {name}...', device.get('name'))
  brd = stl.Node(device.get('addr'), device.get('type_addr'))
  print("Connected")
  
  brd.syncAudio.enable()
  brd.syncAudio.enableNotification()
  
  brd.mAudio.enable()
  brd.mAudio.setSyncManager(brd.syncAudio)
  brd.mAudio.enableNotification()
  
  init_audio(args.output_config, args.freq_config)
  
  getter = Thread(target=audio_getter)
  getter.start()
  player = Thread(target=audio_player)
  player.start()
  print('double tap on SensorTile device (for BVLINK1 FW only) ')
  print('push SW2 button on BlueCoin device (for BVLINK1 FW only) ')
  print('Start_stream... ')
  print('Press Ctrl+C to exit')
  
  stream.start()
  signal.signal(signal.SIGINT, signal_handler)
  while True:
    if not do_process:
      break
    try:
      brd.waitForNotifications(1.0)
    except Exception as e:
      pass
  
  del brd


if __name__ == "__main__":
  try:
    main()
  except Exception as e:
    print("{}: {}".format(type(e).__name__, e))
