from mininet.topo import Topo
from mininet.node import Node
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info

# -----------------------------------------------------------------------------
# ROUTER CLASS
# -----------------------------------------------------------------------------
class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

# -----------------------------------------------------------------------------
# MY CHANGES/CODE
# -----------------------------------------------------------------------------
class courseworkTopo(Topo):

    def build(self):
        # 1. Define Routers (with their main subnet gateway IPs)
        router1 = self.addNode('r1', cls=LinuxRouter, ip="192.168.0.1/24")
        router2 = self.addNode('r2', cls=LinuxRouter, ip="192.168.2.1/24")
        router3 = self.addNode('r3', cls=LinuxRouter, ip="192.168.3.1/24")

        # 2. Define Hosts (pointing to the correct Gateway Router)
        host1 = self.addHost('host1', ip="192.168.0.2/24", defaultRoute='via 192.168.0.1')
        host2 = self.addHost('host2', ip="192.168.0.3/24", defaultRoute='via 192.168.0.1')
        
        host3 = self.addHost('host3', ip="192.168.2.2/24", defaultRoute='via 192.168.2.1')
        host4 = self.addHost('host4', ip="192.168.2.3/24", defaultRoute='via 192.168.2.1')
        
        host5 = self.addHost('host5', ip="192.168.3.2/24", defaultRoute='via 192.168.3.1')

        # 3. Define Switches
        switch1 = self.addSwitch('switch1')
        switch2 = self.addSwitch('switch2')
        switch3 = self.addSwitch('switch3')

        # 4. Connect Hosts -> Switches
        self.addLink(host1, switch1, bw=100, delay='1ms')
        self.addLink(host2, switch1, bw=100, delay='1ms')
        
        self.addLink(host3, switch2, bw=100, delay='1ms')
        self.addLink(host4, switch2, bw=100, delay='1ms')
        
        self.addLink(host5, switch3, bw=100, delay='1ms')

        # 5. Connect Switches -> Routers
        # name the router interface (intfName2) and give it the gateway IP
        self.addLink(switch1, router1, intfName2='r1-eth1', params2={'ip': '192.168.0.1/24'}, bw=100, delay='1ms')
        self.addLink(switch2, router2, intfName2='r2-eth1', params2={'ip': '192.168.2.1/24'}, bw=100, delay='1ms')
        self.addLink(switch3, router3, intfName2='r3-eth0', params2={'ip': '192.168.3.1/24'}, bw=100, delay='1ms')

        # 6. Connect Routers -> Routers (The Backbone)
        
        
        # Link R1 <-> R2 (Using 10.10.0.x)
        self.addLink(router1, router2, 
                     intfName1='r1-eth2', params1={'ip': '10.10.0.2/24'},
                     intfName2='r2-eth2', params2={'ip': '10.10.0.1/24'},
                     bw=50, delay='5ms')
        
        # Link R1 <-> R3 (Using 10.10.1.x)
        self.addLink(router1, router3, 
                     intfName1='r1-eth3', params1={'ip': '10.10.1.1/24'},
                     intfName2='r3-eth2', params2={'ip': '10.10.1.2/24'},
                     bw=50, delay='5ms')


def run():
    topo = courseworkTopo()
    net = Mininet(topo=topo, link=TCLink, controller=None)
    net.start()

    print("--- Setting up Static Routes ---")

    # Router 1: Needs to know how to reach Subnet 2 (192.168.2.x) and Subnet 3 (192.168.3.x)
    # We tell it: "Send packets for 192.168.2.x to R2's interface (10.10.0.1)"
    net['r1'].cmd('ip route add 192.168.2.0/24 via 10.10.0.1')
    net['r1'].cmd('ip route add 192.168.3.0/24 via 10.10.1.2')

    # Router 2: Needs to know how to reach Subnet 1 (192.168.0.x)
    #it tells it: "Send packets for 192.168.0.x to R1's interface (10.10.0.2)"
    net['r2'].cmd('ip route add 192.168.0.0/24 via 10.10.0.2')
    # Also tell it how to reach Subnet 3 (via R1)
    net['r2'].cmd('ip route add 192.168.3.0/24 via 10.10.0.2')

    # Router 3: Needs to know how to reach Subnet 1 and 2
    net['r3'].cmd('ip route add 192.168.0.0/24 via 10.10.1.1')
    net['r3'].cmd('ip route add 192.168.2.0/24 via 10.10.1.1')

    print("--- Network Ready ---")
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
