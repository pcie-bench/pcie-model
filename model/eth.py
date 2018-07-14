## Copyright (C) 2015-2018 Rolf Neugebauer.  All rights reserved.
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

"""Some general function and data to calculate rates for Ethernet"""

# pylint: disable=bad-whitespace
# pylint: disable=invalid-name
# pylint: disable=too-many-instance-attributes

# Configuration options
Variants = ['40GigE', '10GigE', 'GigE']


# Various fields on the wire, all in Bytes
Pre =              7  # Preamble
SOF =              1  # Start of Frame indicator
Hdr =             14  # Header
Hdr_VLAN =        18  # Header including 802.18 Tag
MinPayLoad =      46  # Minimum Payload size
MinPayLoad_VLAN = 42  # Minimum Payload size
CRC =              4  # Checksum
IFG =             12  # Interframe Gap
IFG_GigE =         8  # Optionally reduce IFG for 1GigE
IFG_10GigE =       5  # Optionally reduce IFG for 10GigE
IFG_40GigE =       5  # Optionally reduce IFG for 40GigE


class Cfg(object):
    """A class representing an Ethernet link. Allows to get
    various metrics based on a specific configuration"""

    def __init__(self, variant='40GigE', vlan=True, ifg_min=False):
        """Instantiate a Ethernet config.

        - variant: One of the Variants
        - vlan: Should the frames contain a VLAN tag
        - ifg_min: minimum allowed interframe gap or standard
        """
        if variant not in Variants:
            raise Exception("Unsupported ethernet variant: %s" % variant)
        self.variant = variant
        self.vlan = vlan
        self.ifg_min = ifg_min

        if variant == '40GigE':
            self.rate = long(40 * 1000 * 1000 * 1000)
        elif variant == '10GigE':
            self.rate = long(10 * 1000 * 1000 * 1000)
        elif variant == 'GigE':
            self.rate = long(1000 * 1000 * 1000)

        self.pre_sz = Pre + SOF

        if vlan:
            self.hdr_sz = Hdr_VLAN
            self.min_pay = MinPayLoad_VLAN
        else:
            self.hdr_sz = Hdr
            self.min_pay = MinPayLoad

        if ifg_min:
            if variant == '40GigE':
                self.trail_sz = IFG_40GigE
            elif variant == '10GigE':
                self.trail_sz = IFG_10GigE
            elif variant == 'GigE':
                self.trail_sz = IFG_GigE
        else:
            self.trail_sz = IFG

        self.crc_sz = CRC


    def pps(self, payload):
        """Return the rate of packets for a given payload"""
        if payload < self.min_pay:
            p_sz = self.min_pay
        else:
            p_sz = payload
        s = self.pre_sz + self.hdr_sz + p_sz + self.crc_sz + self.trail_sz
        return long(self.rate / float(s * 8))


    def bps(self, payload):
        "Bits per second of payload bits"
        p = self.pps(payload)
        return long(p * payload * 8)


    def pps_ex(self, frame_sz):
        """Return the rate of packets for a given payload. Assume
        @frame_sz includes ethernet header and CRC"""
        s = frame_sz - self.hdr_sz - self.crc_sz
        return self.pps(s)


    def bps_ex(self, frame_sz):
        """Bits per second of payload bits for a given payload. Assume
        @frame_sz includes ethernet header and CRC"""
        p = self.pps_ex(frame_sz)
        return long(p * frame_sz * 8)


    def us_ex(self, frame_sz):
        """Calculate how long (in us) it takes to transmit a frame
        of a given size.  Assume @frame_sz includes ethernet header and CRC."""
        s = (frame_sz + self.pre_sz + self.trail_sz)
        return (float(s * 8)/self.rate) * 1000 * 1000


if __name__ == '__main__':
    # not much of a test
    e = Cfg()

    print "%4s %9s %11s" % ("sz", "pps", "bps")
    for size in [64, 128, 256, 512, 1024, 1518]:
        print "%4d %9d %11d" % (size, e.pps_ex(size), e.bps_ex(size))


    dat = open("eth.dat", "w")
    dat.write("\"Frame Size(Bytes)\" "
              "\"Packets/s\" "
              "\"Bits/s\" "
              "\"Gb/s\" "
              "\"Time (us)\" "
              "\n")

    for sz in xrange(64, 1519):
        _pps = e.pps_ex(sz)
        bw = e.bps_ex(sz)
        gbs = float(bw) / (1000 * 1000 * 1000)
        us = e.us_ex(sz)
        dat.write("%d %f %f %f %f\n" % (sz, _pps, bw, gbs, us))
