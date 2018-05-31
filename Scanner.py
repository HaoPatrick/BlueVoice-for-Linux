from bluepy.btle import DefaultDelegate
import os
from util import c_str

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


class ScanPrint(DefaultDelegate):
  
  def __init__(self, opts=0):
    DefaultDelegate.__init__(self)
    self.opts = opts
    self.index = 0
    self.listDev = []
  
  @property
  def devices(self):
    return self.listDev
  
  def handleDiscovery(self, dev, is_new_device, is_new_data):
    if dev.rssi < -128:
      return
    if not dev.connectable:
      return
    for (sdid, desc, val) in dev.getScanData():
      if sdid in [8, 9]:
        self.index += 1
        print('{index}) {val} --> [{addr}]({addr_type}) rssi: {rssi}'.format(index=self.index,
                                                                             val=c_str(val, 'CYAN'),
                                                                             addr=dev.addr,
                                                                             addr_type=dev.addrType,
                                                                             rssi=dev.rssi))
        dict_dev = {'index': self.index, 'name': val, 'addr': dev.addr, 'type_addr': dev.addrType}
        self.listDev.append(dict_dev)
    if not dev.scanData:
      print('\t(no data)')
