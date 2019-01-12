from ryu.base import app_manager

from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls

from ryu.ofproto import ofproto_v1_0, ofproto_v1_3

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import icmp


class IcmpResponder(app_manager.RyuApp):
    # OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION, ofproto_v1_3.OFP_VERSION]
    # forwarding_table = {
    #     's1': {
    #         # out_port = 2
    #         'in_port=1': 2,
    #         'in_port=2': 1,
    #     },
    #     's2': {
    #         'in_port=2': 1,
    #         'in_port=1': 2,
    #     },
    #     's3': {
    #         'in_port=1': 2,
    #         'in_port=2': 1,
    #     },
    #     's4': {
    #         'in_port=1': 2,
    #         'in_port=2': 1,
    #     }
    # }
    forwarding_table = {
        's1': {
            # out_port = 2
            'dst_mac=00:00:00:00:00:01': 1,
            'dst_mac=00:00:00:00:00:02': 2,
        },
        's2': {
            'dst_mac=00:00:00:00:00:01': 2,
            'dst_mac=00:00:00:00:00:02': 1,
        },
        's3': {
            'dst_mac=00:00:00:00:00:01': 1,
            'dst_mac=00:00:00:00:00:02': 2,
        },
        's4': {
            'dst_mac=00:00:00:00:00:01': 1,
            'dst_mac=00:00:00:00:00:02': 2,
        }
    }

    def __init__(self, *args, **kwargs):
        super(IcmpResponder, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        msg = ev.msg
        print("Got ofp_event.EventOFPSwitchFeatures: ", msg)
        self.logger.debug('OFPSwitchFeatures received: '
                        'datapath_id=0x%016x n_buffers=%d '
                        'n_tables=%d auxiliary_id=%d '
                        'capabilities=0x%08x',
                        msg.datapath_id, msg.n_buffers, msg.n_tables,
                        msg.auxiliary_id, msg.capabilities)

        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        match=ofp_parser.OFPMatch()
        actions = [ofp_parser.OFPActionOutput(ofp.OFPP_CONTROLLER, 65535)]
        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                             actions)]
        # cookie = 0
        # command = ofp.OFPFC_ADD
        # idle_timeout = hard_timeout = 0
        # priority = 32768
        # out_port = ofproto.OFPP_NONE
        # flags = 0
        
        req = ofp_parser.OFPFlowMod(dp, cookie=0, cookie_mask=0, table_id=0, 
                                    command=ofp.OFPFC_ADD, idle_timeout=0, 
                                    hard_timeout=0, priority=32768, 
                                    buffer_id=ofp.OFP_NO_BUFFER, out_port=ofp.OFPP_ANY, 
                                    out_group=ofp.OFPG_ANY, flags=0, 
                                    match=match, instructions=inst)

        self.send_flow_mod(dp, req)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        # in_port = msg.in_port
        pkt = packet.Packet(data=msg.data)
        print("packet-in %s" % (pkt,))
        self.logger.info("packet-in %s" % (pkt,))

        switch_id = msg.datapath.id
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        # TODO port_no doesn't exist
        in_port = ofp_parser.OFPPort.name
        print("in_port: ",str(in_port))
        # output_port = self.choose_output_port(in_port, switch_id)
        # reason = self.get_reason(msg, ofp)
        
        # print("I got a packetIn message (", msg.buffer_id, ") from switch: ", msg.datapath.id, ". Reason: ", reason)

        # if(output_port == -1):
        #     print("Cannot determine the output port for switch: ", switch_id, ", in_port: ", in_port)
        # else:
        #     print("Chosen output port: ", output_port)

        #     #TODO: Insert your match

        #     match = ofp_parser.OFPMatch(in_port=in_port)
        #     actions = [ofp_parser.OFPActionOutput(output_port, 65535)]

        #     cookie = 0
        #     command = ofp.OFPFC_ADD
        #     idle_timeout = hard_timeout = 0
        #     priority = 32768
        #     # out_port = ofproto.OFPP_NONE
        #     flags = 0
        #     req = ofp_parser.OFPFlowMod(
        #         dp, match, cookie, command, idle_timeout, hard_timeout,
        #         priority, msg.buffer_id, output_port, flags, actions)
        #     self.send_flow_mod(dp, req)

    def send_flow_mod(self, datapath, req):
        datapath.send_msg(req)

    # # Determine output port on the basis of input port table
    # def choose_output_port(self, in_port, switch_id):  # ,switch ID
    #     output_port = self.forwarding_table['s'+str(switch_id)]['in_port='+str(in_port)]
    #     if output_port in [1,2]:
    #         return output_port
    #     else:
    #         return -1

    #Determine output port on the basis of mac address table
    def choose_output_port(self, dst_mac, switch_id, offload):  # ,switch ID
        output_port = self.forwarding_table['s'+str(switch_id)]['dst_mac='+str(dst_mac)]
        if output_port == 1
            return output_port
        elif output_port == 2:
        # If offloading is active, push the traffic through the port 3
            if offload == True:
                return 3
            else
                return 2
        else:
            return -1    

    def get_reason(self, msg, ofp):
        if  msg.reason == ofp.OFPR_NO_MATCH:
            reason = 'NO MATCH'        
        elif msg.reason == ofp.OFPR_ACTION:
            reason = 'ACTION'
        elif msg.reason == ofp.OFPR_INVALID_TTL:
            reason = 'INVALID TTL'
        else:
            reason = 'unknown'
        return reason
