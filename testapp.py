from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0, ofproto_v1_3

class L2Switch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION, ofproto_v1_3.OFP_VERSION]
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
        ofp = msg.datapath.ofproto
        
        if  msg.reason == ofp.OFPR_NO_MATCH:
            reason = 'NO MATCH'
            self.choose_fields(msg)        
        elif msg.reason == ofp.OFPR_ACTION:
            reason = 'ACTION'
        elif msg.reason == ofp.OFPR_INVALID_TTL:
            reason = 'INVALID TTL'
        else:
            reason = 'unknown'
        
        print("I got a packetIn message (", msg.buffer_id, ") from switch: ", msg.datapath.id, ". Reason: ", reason, ", Message: \"", msg, "\"")

            # # Input port of the packet
            # in_port = msg.in_port

            # ofp_parser = dp.ofproto_parser
            # port = self.choose_output_port(in_port, switch_id)

            # print("Chosen output port: ", port)

            # actions = [ofp_parser.OFPActionOutput(port, 65535)]
            # out = ofp_parser.OFPPacketOut(
            #     # datapath=dp, buffer_id=msg.buffer_id, in_port=msg.in_port, actions=actions)
            #     datapath=dp, buffer_id=packet_id, in_port=in_port, actions=actions)
            # print(out)
            # send_flow_mod(dp, 0, packet_id, in_port, port)

    # Choose, which fields to send in send_flow_mod function
    def choose_fields(self, msg):
        # Datapath ID of the switch that has sent the message
        packet_id = msg.buffer_id
        switch_id = msg.datapath.id
        dp = msg.datapath
        ofp = dp.ofproto
        # Input port of the packet
        in_port = msg.in_port

        
        port = self.choose_output_port(in_port, switch_id)
        
        ofp_parser = dp.ofproto_parser
        
        print("Chosen output port: ", port)

        #TODO: Insert your match

        match = ofp_parser.OFPMatch(in_port=in_port)
        actions = [ofp_parser.OFPActionOutput(port, 65535)]

        cookie = 0
        command = ofp.OFPFC_ADD
        idle_timeout = hard_timeout = 0
        priority = 32768
        buffer_id = packet_id
        # out_port = ofproto.OFPP_NONE
        flags = 0
        req = ofp_parser.OFPFlowMod(
            dp, match, cookie, command, idle_timeout, hard_timeout,
            priority, buffer_id, port, flags, actions)
        self.send_flow_mod(dp, req)

    def send_flow_mod(self, datapath, req):
        datapath.send_msg(req)

    def choose_output_port(self, in_port, switch_id):  # ,switch ID
        if switch_id==1:
            return self.forwarding_table['s1']['in_port='+str(in_port)]
        if switch_id==2:
            return self.forwarding_table['s2']['in_port='+str(in_port)]


