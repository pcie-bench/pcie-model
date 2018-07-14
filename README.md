# A PCIe model

This repository contains a model of PCI Express (PCIe). It allows
users to calculate PCIe bandwidth for different hardware
configurations e.g., PCIe generation, number of lanes, and negotiated
parameters, such as Maximum Payload Size (MPS), Maximum Read Request
Size (MRRS), etc.

The code in this repository also allows to model device/driver
interactions. This is typically done by adding up how many bytes are
transferred to and from the host for a given transaction (or batch of
transactions). For example, for a very simple NIC to transmit a packet
from the host, the device driver would perform a PCIe write to update
the queue pointer. The device would then DMA the TX descriptor and the
packet from the host. After the transmission the device would generate
a MSI and device driver would read the TX queue pointer. For the
receive path similar transactions would occur. The file
[`simple_nic.py`](./model/simple_nic.py) contains code to calculate the
achievable bandwidth by such a simple NIC.

More realistic/modern devices typically batch some transactions, for
example, they DMA groups of descriptors. The file
[`niantic.py`](./models/niantic.py) contains a model for such a device,
a Intel 10Gb/s NIC, code-named Niantic.

## Sample code

There are two sample program in the top-level directory (with
associated `gnuplot` files).

- [`pcie_bw.py`](./pcie_bw.py) prints out the bandwidth achievable at
  the TLP layer for a given PCIe configuration. It also generates
  bandwith data for Memory Read (MRd) and Memory Write (MWr) pcie
  transactions for different payload sizes. This uses the
  [`mem_bw.py`](./model/mem_bw.py) model.

- [`nic_bw.py`](./nic_bw.py) calculates the theoretically achievable
  bandwidth for a simple NIC and Intel Niantic style NIC using the
  models mentioned above.


## More information

For more information see our SIGCOMM 2018 paper "Understanding PCIe
Performance for End Host Networking".

TODO: Add link once available.
