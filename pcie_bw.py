#! /usr/bin/env python
#
## Copyright (C) 2015 Rolf Neugebauer.  All rights reserved.
## Copyright (C) 2015 Netronome Systems, Inc.  All rights reserved.
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

"""A simple script to generate data for PCIe and ethernet bandwidth estimates"""

import sys
from optparse import OptionParser

from model import pcie, eth, mem_bw

# pylint: disable=too-many-locals

OUT_FILE = "pcie_bw.dat"

def main():
    """Main"""
    usage = """usage: %prog [options]"""

    parser = OptionParser(usage)
    parser.add_option('--mps', dest='MPS', type="int", action='store',
                      default=256,
                      help='Set the maximum payload size of the link')
    parser.add_option('--mrrs', dest='MRRS', type="int", action='store',
                      default=512,
                      help='Set the maximum read request size of the link')
    parser.add_option('--rcb', dest='RCB', type="int", action='store',
                      default=64,
                      help='Set the read completion boundary of the link')
    parser.add_option('--lanes', dest='lanes', type="string", action='store',
                      default='x8',
                      help='Set num lanes (x2, x4, x8, or x16)')
    parser.add_option('--gen', dest='gen', type="string", action='store',
                      default='gen3',
                      help='Set PCIe version (gen1, gen2, or gen3)')
    parser.add_option('--addr', dest='addr', type="int", action='store',
                      default=64,
                      help='Set the number of address bits (32 or 64)')
    parser.add_option('--ecrc', dest='ecrc', type="int", action='store',
                      default=0,
                      help='Use ECRC (0 or 1)')
    parser.add_option('-o', '--outfile', dest='FILE',
                      default=OUT_FILE, action='store',
                      help='File where to write the data to')

    (options, _) = parser.parse_args()

    pciecfg = pcie.Cfg(version=options.gen,
                       lanes=options.lanes,
                       addr=options.addr,
                       ecrc=options.ecrc,
                       mps=options.MPS,
                       mrrs=options.MRRS,
                       rcb=options.RCB)

    print "PCIe Config:"
    pciecfg.pp()

    ethcfg = eth.Cfg('40GigE')

    tlp_bw = pciecfg.TLP_bw
    bw_spec = pcie.BW_Spec(tlp_bw, tlp_bw, pcie.BW_Spec.BW_RAW)

    dat = open(options.FILE, "w")
    dat.write("\"Payload(Bytes)\" "
              "\"PCIe Write BW\" "
              "\"PCIe Write Trans/s\" "
              "\"PCIe Read BW\" "
              "\"PCIe Read Trans/s\" "
              "\"PCIe Read/Write BW\" "
              "\"PCIe Read/Write Trans/s\" "
              "\"40G Ethernet BW\" "
              "\"40G Ethernet PPS\" "
              "\"40G Ethernet Frame time (ns)\" "
              "\n")

    for size in xrange(1, 1500 + 1):
        wr_bw = mem_bw.write(pciecfg, bw_spec, size)
        rd_bw = mem_bw.read(pciecfg, bw_spec, size)
        rdwr_bw = mem_bw.read_write(pciecfg, bw_spec, size)

        wr_trans = (wr_bw.tx_eff * 1000 * 1000 * 1000 / 8) / size
        rd_trans = (rd_bw.rx_eff * 1000 * 1000 * 1000 / 8) / size
        rdwr_trans = (rdwr_bw.tx_eff * 1000 * 1000 * 1000 / 8) / size

        if size >= 64:
            eth_bw = ethcfg.bps_ex(size) / (1000 * 1000 * 1000.0)
            eth_pps = ethcfg.pps_ex(size)
            eth_lat = 1.0 * 1000 * 1000 * 1000 / eth_pps
            dat.write("%d %.2f %.1f %.2f %.1f %.2f %.1f %.2f %d %.2f\n" %
                      (size,
                       wr_bw.tx_eff, wr_trans,
                       rd_bw.rx_eff, rd_trans,
                       rdwr_bw.tx_eff, rdwr_trans,
                       eth_bw, eth_pps, eth_lat))
        else:
            dat.write("%d %.2f %.1f %.2f %.1f %.2f %.1f\n" %
                      (size,
                       wr_bw.tx_eff, wr_trans,
                       rd_bw.rx_eff, rd_trans,
                       rdwr_bw.tx_eff, rdwr_trans))

    dat.close()

if __name__ == '__main__':
    sys.exit(main())
