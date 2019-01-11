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
        dp = msg.datapath

        # Datapath ID of the switch that has sent the message
        packet_id = msg.buffer_id
        switch_id = msg.datapath.id
        ofp = dp.ofproto

        print("OFPROTO = ", ofp)

        if  msg.reason == ofp.OFPR_NO_MATCH:
            reason = 'NO MATCH'
        elif msg.reason == ofp.OFPR_ACTION:
            reason = 'ACTION'
        elif msg.reason == ofp.OFPR_INVALID_TTL:
            reason = 'INVALID TTL'
        else:
            reason = 'unknown'
        print("I got a packetIn message (", packet_id, ") from switch: ", switch_id, ". Reason: ", reason, ", Message: \"", msg, "\"")

        if msg.reason == ofp.OFPR_NO_MATCH:
        # Input port of the packet
        in_port = msg.in_port

        ofp_parser = dp.ofproto_parser
        port = self.choose_output_port(in_port, switch_id)

        print("Chosen output port: ", port)

        actions = [ofp_parser.OFPActionOutput(port, 65535)]
        out = ofp_parser.OFPPacketOut(
             # datapath=dp, buffer_id=msg.buffer_id, in_port=msg.in_port, actions=actions)
             datapath=dp, buffer_id=packet_id, in_port=in_port, actions=actions)
        print(out)
        dp.send_msg(out)

    def send_flow_mod(self, datapath, table_id, buffer_id, in_port):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        # cookie = cookie_mask = 0
        # table_id = 0
        idle_timeout = hard_timeout = 0
        priority = 32768
        # buffer_id = ofp.OFP_NO_BUFFER
        match = ofp_parser.OFPMatch(in_port=in_port, eth_dst='ff:ff:ff:ff:ff:ff')
        actions = [ofp_parser.OFPActionOutput(ofp.OFPP_NORMAL, 0)]
        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                                actions)]
        req = ofp_parser.OFPFlowMod(datapath, cookie, cookie_mask,
                                    table_id, ofp.OFPFC_ADD,
                                    idle_timeout, hard_timeout,
                                    priority, buffer_id,
                                    ofp.OFPP_ANY, ofp.OFPG_ANY,
                                    ofp.OFPFF_SEND_FLOW_REM,
                                    match, inst)
        datapath.send_msg(req)

    def choose_output_port(self, in_port, switch_id):  # ,switch ID
        if switch_id==1:
            return self.forwarding_table['s1']['in_port='+str(in_port)]
        if switch_id==2:
            return self.forwarding_table['s2']['in_port='+str(in_port)]


