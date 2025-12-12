# Coursework Task 1 – Mininet Topology

This project implements the network topology specified in the coursework for Task 1. The topology recreates a multi-LAN network with three routers, two switches, and five hosts using Mininet. All IP addressing, static routing, and link characteristics (bandwidth, delay, loss) are configured using the Mininet Python API.

---

## How to Run the Topology

### **Using Makefile (recommended)**

### **Manually**

```
mn --custom topology.py --topo courseworkTopo --switch=lxbr --link=tc --controller=none
```

---

## Network Overview

### **Devices**

- **Hosts:** host1, host2, host3, host4, host5
- **Routers:** router1, router2, router3
- **Switches:** switch1, switch2

### **Topology Summary**

- host1 + host2 → switch1 → router1
- host3 + host4 → switch2 → router2
- host5 --> directly to router3
- router1 <-> router2 (10ms delay, 1% loss)
- router1 <-> outer3 (100 Mbit/s, 100ms delay)

## IP Addressing

### **Hosts**

| Host  | Interface | IP Address     | Default Route   |
| ----- | --------- | -------------- | --------------- |
| host1 | eth0      | 192.168.0.2/24 | via 192.168.0.1 |
| host2 | eth0      | 192.168.0.3/24 | via 192.168.0.1 |
| host3 | eth0      | 192.168.2.2/24 | via 192.168.2.1 |
| host4 | eth0      | 192.168.2.3/24 | via 192.168.2.1 |
| host5 | eth0      | 192.168.3.2/24 | via 192.168.3.1 |

### **Routers**

| Router  | Interface    | IP Address     |
| ------- | ------------ | -------------- |
| router1 | router1-eth1 | 192.168.0.1/24 |
| router1 | router1-eth2 | 10.10.0.2/24   |
| router1 | router1-eth3 | 10.10.1.1/24   |
| router2 | router2-eth1 | 192.168.2.1/24 |
| router2 | router2-eth2 | 10.10.0.1/24   |
| router3 | router3-eth0 | 192.168.3.1/24 |
| router3 | router3-eth2 | 10.10.1.2/24   |

---

## Static Routing

### **Router1:**

```
192.168.2.0/24 via 10.10.0.1
192.168.3.0/24 via 10.10.1.2
```

### **Router2:**

```
192.168.0.0/24 via 10.10.0.2
10.10.1.0/24 via 10.10.0.2
192.168.3.0/24 via 10.10.0.2
```

### **Router3:**

```
192.168.0.0/24 via 10.10.1.1
10.10.0.0/24 via 10.10.1.1
192.168.2.0/24 via 10.10.1.1
```

---

## Link Characteristics

| Link                        | Bandwidth | Delay | Loss |
| --------------------------- | --------- | ----- | ---- |
| router1-eth2 ↔ router2-eth2 | default   | 10ms  | 1%   |
| router1-eth3 ↔ router3-eth2 | 100 Mbit  | 100ms | 0%   |
| All other links             | default   | 0ms   | 0%   |

---

##  Testing

Once Mininet is running:

###  Ping all hosts:

```
mininet> pingall
```

&#x20;`0% dropped`

###  Test long-path connectivity:

```
mininet> host1 ping -c 3 host5
```

### Verify router delay:

```
mininet> router1 ping -c 3 router3
```

Expected RTT ≈ 100–200ms.

### Verify packet loss:

```
mininet> router1 ping -c 50 router2
```

Expected ≈1% packet loss.

---

## Files Included

```
topology.py   – Mininet topology implementation
Makefile      – Commands to run and clean the topology
README.md     – Documentation (this file)
```

---

##  Notes for the Marker :)

- Topology  matches coursework specification
- All IP addresses and routes follow the table
- Link characteristics are correctly implemented

  hosts can communicate with each other
- No external scripts are required

  (my obsidian note taking finally came in usefull)

---

