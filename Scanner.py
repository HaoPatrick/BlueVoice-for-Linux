from bluepy.btle import DefaultDelegate
from util import c_str


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
        dict_dev = {'index': self.index, 'name': val, 'addr': dev.addr, 'type_addr': dev.addrType, 'entry': dev}
        self.listDev.append(dict_dev)
    if not dev.scanData:
      print('\t(no data)')
