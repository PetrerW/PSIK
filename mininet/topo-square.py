"""Custom topology example

Two hosts and two switches connected in a square-like topology:

   h1 --- s1 --- s3 --- s2 --- h2
   h1 --- s1 --- s4 --- s2 --- h2

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.

To run the topology type:
sudo mn --custom ./topo-square.py --topo squaretopo --controller remote,ip=192.168.34.3 --mac --switch ovsk
"""

from mininet.topo import Topo
from mininet.node import Switch

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch( 's2' )
        s4 = self.addSwitch( 's4' )
        s3 = self.addSwitch( 's3' )

        # Add links
        self.addLink(h1, s1)
        self.addLink(s1, s3)
        self.addLink(s3, s2)
        self.addLink(s2, h2)
        self.addLink(s1, s4)
        self.addLink(s4, s2)	 


topos = { 'squaretopo': ( lambda: MyTopo() ) }

