from mininet.topo import Topo
from mininet.node import Node
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import OVSBridge

print("using my topo file")

# ----------------------------------------------------------------------------------------------------------
#                           ROUTER CLASS
# ----------------------------------------------------------------------------------------------------------
class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # FIX: Added '-w' to ensure forwarding is actually enabled
        self.cmd('sysctl -w net.ipv4.ip_forward=1')

    def terminate(self):
        # FIX: Added '-w' here too for consistency
        self.cmd('sysctl -w net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


# -----------------------------------------------------------------------------------------------------
#                           MY CHANGES/CODE
# -----------------------------------------------------------------------------------------------------
class courseworkTopo(Topo):

    def build(self):
        # 1. Define Routers w out ips
        router1 = self.addNode('router1', cls=LinuxRouter, ip=None)
        router2 = self.addNode('router2', cls=LinuxRouter, ip=None)
        router3 = self.addNode('router3', cls=LinuxRouter, ip=None)

        # 2. Define Switches
        switch1 = self.addSwitch('switch1')
        switch2 = self.addSwitch('switch2')

        # 3. Define Hosts (pointing to the Gateway Router)
        host1 = self.addHost('host1', ip="192.168.0.2/24", defaultRoute='via 192.168.0.1')
        host2 = self.addHost('host2', ip="192.168.0.3/24", defaultRoute='via 192.168.0.1')

        host3 = self.addHost('host3', ip="192.168.2.2/24", defaultRoute='via 192.168.2.1')
        host4 = self.addHost('host4', ip="192.168.2.3/24", defaultRoute='via 192.168.2.1')

        # FIX: Fixed syntax error (quote mismatch)
        host5 = self.addHost('host5', ip="192.168.3.2/24", defaultRoute='via 192.168.3.1')

        # 4. Connect Hosts -> Switches
        self.addLink(host1, switch1)
        self.addLink(host2, switch1)

        self.addLink(host3, switch2)
        self.addLink(host4, switch2)

        # 5. host 5 has its own lan connection to router3
        self.addLink(host5, router3,
                     intfName2='router3-eth0',
                     params2={'ip': '192.168.3.1/24'})

        # 6. Connect Routers -> Switches (LAN interfaces)
        self.addLink(switch1, router1,
                     intfName2='router1-eth1',
                     params2={'ip': '192.168.0.1/24'})

        self.addLink(switch2, router2,
                     intfName2='router2-eth1',
                     params2={'ip': '192.168.2.1/24'})

        # ---------------------------------------------------------------------------------------
        #                           ROUTER CORE LINKS
        # ---------------------------------------------------------------------------------------

        # router1-eth2 <-> router2-eth2  (10ms + 1% loss)
        self.addLink(router1, router2,
                     intfName1='router1-eth2',
                     intfName2='router2-eth2',
                     params1={'ip': '10.10.0.2/24'},
                     params2={'ip': '10.10.0.1/24'},
                     delay='10ms',
                     loss=1)

        # router1-eth3 <-> router3-eth2 (100Mbps 100ms)
        self.addLink(router1, router3,
                     intfName1='router1-eth3',
                     intfName2='router3-eth2',
                     params1={'ip': '10.10.1.1/24'},
                     params2={'ip': '10.10.1.2/24'},
                     bw=100,
                     delay='100ms',
                     loss=0)


def run():
    topo = courseworkTopo()
    # Ensure TCLink is used for delay/loss to work
    net = Mininet(topo=topo, link=TCLink,switch=OVSBridge, controller=None)
    net.start()

    router1 = net.get('router1')
    router2 = net.get('router2')
    router3 = net.get('router3')

    print("--- Setting up Static Routes ---")

    # router1
    router1.cmd("ip route add 192.168.2.0/24 via 10.10.0.1")
    router1.cmd("ip route add 192.168.3.0/24 via 10.10.1.2")

    # router2
    router2.cmd("ip route add 192.168.0.0/24 via 10.10.0.2")
    router2.cmd("ip route add 10.10.1.0/24 via 10.10.0.2")
    router2.cmd("ip route add 192.168.3.0/24 via 10.10.0.2")

    # router3
    router3.cmd("ip route add 192.168.0.0/24 via 10.10.1.1")
    router3.cmd("ip route add 10.10.0.0/24 via 10.10.1.1")
    router3.cmd("ip route add 192.168.2.0/24 via 10.10.1.1")

    print("--- Network Ready ---")

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()

    topos = {'courseworkTopo': courseworkTopo}

