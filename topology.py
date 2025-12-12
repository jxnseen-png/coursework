from mininet.topo import Topo
from mininet.node import Node
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info


# -----------------------------------------------------------------------------
# ROUTER CLASS (Standard Setup)
# -----------------------------------------------------------------------------

class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl -w net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl -w net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


# -----------------------------------------------------------------------------
# MY TOPOLOGY CODE
# -----------------------------------------------------------------------------

class courseworkTopo(Topo):

    def build(self):

        # -------------------------------------------------------
        # ROUTERS (each gets only its LAN-facing IP)
        # -------------------------------------------------------

        r1 = self.addNode("r1", cls=LinuxRouter)
        r2 = self.addNode("r2", cls=LinuxRouter)
        r3 = self.addNode("r3", cls=LinuxRouter)


        # -------------------------------------------------------
        # HOSTS
        # -------------------------------------------------------

        h1 = self.addHost("host1", ip="192.168.0.2/24", defaultRoute="via 192.168.0.1")
        h2 = self.addHost("host2", ip="192.168.0.3/24", defaultRoute="via 192.168.0.1")

        h3 = self.addHost("host3", ip="192.168.2.2/24", defaultRoute="via 192.168.2.1")
        h4 = self.addHost("host4", ip="192.168.2.3/24", defaultRoute="via 192.168.2.1")

        h5 = self.addHost("host5", ip="192.168.3.2/24", defaultRoute="via 192.168.3.1")

        # -------------------------------------------------------
        # SWITCHES
        # -------------------------------------------------------

        s1 = self.addSwitch("switch1")
        s2 = self.addSwitch("switch2")
        s3 = self.addSwitch("switch3")

        # -------------------------------------------------------
        # SUBNET LINKS
        # -------------------------------------------------------

        # Subnet 192.168.0.x  (hosts 1 & 2)
        self.addLink(h1, s1, bw=100, delay="1ms")
        self.addLink(h2, s1, bw=100, delay="1ms")

        # Connect LAN switch ↔ r1
        self.addLink(
            s1, r1,
            intfName2="r1-eth1",
            params2={"ip": "192.168.0.1/24"},
            bw=100, delay="1ms"
        )

        # Subnet 192.168.2.x  (hosts 3 & 4)
        self.addLink(h3, s2, bw=100, delay="1ms")
        self.addLink(h4, s2, bw=100, delay="1ms")

        self.addLink(
            s2, r2,
            intfName2="r2-eth1",
            params2={"ip": "192.168.2.1/24"},
            bw=100, delay="1ms"
        )

        # Subnet 192.168.3.x  (host 5)
        self.addLink(h5, s3, bw=100, delay="1ms")

        # IMPORTANT FIX: remove conflicting r3-eth0 override
        self.addLink(
            s3, r3,
            intfName2="r3-eth1",
            params2={"ip": "192.168.3.1/24"},
            bw=100, delay="1ms"
        )

        # -------------------------------------------------------
        # CORE LINKS (router <-> router)
        # -------------------------------------------------------

        # r1 ↔ r2
        self.addLink(
            r1, r2,
            intfName1="r1-eth2", params1={"ip": "10.10.0.2/24"},
            intfName2="r2-eth2", params2={"ip": "10.10.0.1/24"},
            bw=50, delay="5ms"
        )

        # r1 ↔ r3
        self.addLink(
            r1, r3,
            intfName1="r1-eth3", params1={"ip": "10.10.1.1/24"},
            intfName2="r3-eth2", params2={"ip": "10.10.1.2/24"},
            bw=50, delay="5ms"
        )


# -----------------------------------------------------------------------------
# RUNTIME ROUTING SETUP
# -----------------------------------------------------------------------------

def run():
    topo = courseworkTopo()
    net = Mininet(topo=topo, link=TCLink, controller=None)
    net.start()

    print("\nSetting up static routes...\n")

    # Router 1
    net["r1"].cmd("ip route add 192.168.2.0/24 via 10.10.0.1")
    net["r1"].cmd("ip route add 192.168.3.0/24 via 10.10.1.2")

    # Router 2
    net["r2"].cmd("ip route add 192.168.0.0/24 via 10.10.0.2")
    net["r2"].cmd("ip route add 192.168.3.0/24 via 10.10.0.2")

    # Router 3
    net["r3"].cmd("ip route add 192.168.0.0/24 via 10.10.1.1")
    net["r3"].cmd("ip route add 192.168.2.0/24 via 10.10.1.1")

    CLI(net)
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    run()
