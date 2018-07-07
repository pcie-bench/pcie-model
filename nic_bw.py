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

"""A script to generate performance estimates for NICs"""

import sys

from model import pcie, eth, mem_bw, simple_nic, niantic

# pylint: disable=bad-whitespace
# pylint: disable=too-many-locals

def main():
    """main"""
    cfg = pcie.Cfg(version='gen3',
                   lanes='x8',
                   addr=64,
                   ecrc=0,
                   mps=256,
                   mrrs=512,
                   rcb=64)

    ethcfg = eth.Cfg('40GigE')
    tlp_bw = cfg.TLP_bw
    bw_spec = pcie.BW_Spec(tlp_bw, tlp_bw, pcie.BW_Spec.BW_RAW)

    dat = open("nic_bw.dat", "w")
    dat.write("\"Packet Size(Bytes)\" "
              "\"Max. Write Bandwidth\" "
              "\"Max. R/W Bandwidth\" "

              "\"40Gb/s Line Rate (- FCS)\" "

              "\"Simplistic NIC Bi-directional\" "
              "\"Simplistic NIC TX only\" "
              "\"Simplistic NIC RX only\" "

              "\"kernel NIC Bi-directional\" "
              "\"kernel NIC TX only\" "
              "\"kernel NIC RX only\" "

              "\"DPDK NIC Bi-directional\" "
              "\"DPDK NIC TX only\" "
              "\"DPDK NIC RX only\" "
              "\n")

    max_val = 0
    for size in xrange(64, 1500):

        w_bw = mem_bw.write(cfg, bw_spec, size - 4)
        rw_bw = mem_bw.read(cfg, bw_spec, size - 4)

        # Work out Ethernet bandwidth. Typically do not transfer the FCS
        eth_bw = ethcfg.bps_ex(size - 4) / (1000 * 1000 * 1000.0)

        # Remember NIC RX is DIR_TX
        simple_nic_bi = simple_nic.bw(cfg, bw_spec, pcie.DIR_BOTH, size - 4)
        simple_nic_tx = simple_nic.bw(cfg, bw_spec, pcie.DIR_RX, size - 4)
        simple_nic_rx = simple_nic.bw(cfg, bw_spec, pcie.DIR_TX, size - 4)

        kernel_nic_bi = niantic.bw(cfg, bw_spec, pcie.DIR_BOTH, size - 4)
        kernel_nic_tx = niantic.bw(cfg, bw_spec, pcie.DIR_RX, size - 4)
        kernel_nic_rx = niantic.bw(cfg, bw_spec, pcie.DIR_TX, size - 4)

        pmd_nic_bi = niantic.bw(cfg, bw_spec, pcie.DIR_BOTH, size - 4, h_opt="PMD")
        pmd_nic_tx = niantic.bw(cfg, bw_spec, pcie.DIR_RX, size - 4, h_opt="PMD")
        pmd_nic_rx = niantic.bw(cfg, bw_spec, pcie.DIR_TX, size - 4, h_opt="PMD")

        max_val = max(max_val, rw_bw.rx_eff, eth_bw,
                      simple_nic_bi.tx_eff, simple_nic_tx.rx_eff, simple_nic_rx.tx_eff,
                      kernel_nic_bi.tx_eff, kernel_nic_tx.rx_eff, kernel_nic_rx.tx_eff,
                      pmd_nic_bi.tx_eff,    pmd_nic_tx.rx_eff,    pmd_nic_rx.tx_eff)

        dat.write("%d %.2f %.2f   %.2f   %.2f %.2f %.2f   %.2f %.2f %.2f   %.2f %.2f %.2f\n" %
                  (size, w_bw.tx_eff, rw_bw.rx_eff,
                   eth_bw,
                   simple_nic_bi.tx_eff, simple_nic_tx.rx_eff, simple_nic_rx.tx_eff,
                   kernel_nic_bi.tx_eff, kernel_nic_tx.rx_eff, kernel_nic_rx.tx_eff,
                   pmd_nic_bi.tx_eff,    pmd_nic_tx.rx_eff,    pmd_nic_rx.tx_eff
                  ))

    dat.close()

if __name__ == '__main__':
    sys.exit(main())
