from Scanner import ScanPrint as ScanPrintDelegate

from bluepy.btle import Scanner
from util import c_str

scanner = Scanner().withDelegate(ScanPrintDelegate())
devices = scanner.scan(3)
for dev in devices:
  print(c_str('asdf', 'CYAN'), "Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
  for (adtype, desc, value) in dev.getScanData():
    print("  (ad: %s)%s = %s" % (adtype, desc, value))
