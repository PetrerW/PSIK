from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0

class L2Switch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]
    forwarding_table = {
        's1': {
            # out_port = 2
            'in_port=1': 2,
            'in_port=2': 1,
        },
        's2': {
            'in_port=2': 1,
            'in_port=1': 2,
        },
        's12u': {
            'in_port=1': 2,
            'in_port=2': 1,
        },
        's12d': {
            'in_port=1': 2,
            'in_port=2': 1,
        }
    }

    def __init__(self, *args, **kwargs):
        super(L2Switch, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg

        # Datapath ID of the switch that has sent the message
        packet_id = msg.buffer_id
        switch_id = msg.datapath.id
        print("I got a packetIn message (", packet_id, ") from switch: ", switch_id)

        # Input port of the packet
        in_port = msg.in_port

        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        port = self.choose_output_port(in_port, switch_id)

        actions = [ofp_parser.OFPActionOutput(port, 65535)]
        out = ofp_parser.OFPPacketOut(
            # datapath=dp, buffer_id=msg.buffer_id, in_port=msg.in_port, actions=actions)
            datapath=dp, buffer_id=switch_id, in_port=in_port, actions=actions)
        dp.send_msg(out)

    #
    # @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    # def packet_in_handler(self, ev):
    #     msg = ev.msg
    #
    #     # Datapath ID of the switch that has sent the message
    #     switch_id = msg.buffer_id
    #
    #     # Input port of the packet
    #     in_port = msg.in_port
    #
    #     dp = msg.datapath
    #     ofp = dp.ofproto
    #     ofp_parser = dp.ofproto_parser
    #
    #
    #     actions = [ofp_parser.OFPActionOutput(1, 65535)]
    #     out = ofp_parser.OFPPacketOut(
    #         # datapath=dp, buffer_id=msg.buffer_id, in_port=msg.in_port, actions=actions)
    #         datapath=dp, buffer_id=switch_id, in_port=in_port, actions=actions)
    #     dp.send_msg(out)

    def choose_output_port(self, in_port, switch_id):  # ,switch ID
        if switch_id==1:
            return self.forwarding_table['s1']['in_port='+str(in_port)]
        if switch_id==2:
            return self.forwarding_table['s2']['in_port='+str(in_port)]

