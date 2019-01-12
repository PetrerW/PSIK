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
        super(IcmpResponder, self).__init__(*args, **kwargs)
        #self.hw_addr = '0a:e4:1c:d1:3e:44'
        #self.ip_addr = '192.0.2.9'

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        msg = ev.msg
    
        self.logger.debug('OFPSwitchFeatures received: '
                      'datapath_id=0x%016x n_buffers=%d '
                      'n_tables=%d capabilities=0x%08x ports=%s',
                      msg.datapath_id, msg.n_buffers, msg.n_tables,
                      msg.capabilities, msg.ports)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.in_port
        pkt = packet.Packet(data=msg.data)
        self.logger.info("packet-in %s" % (pkt,))

        switch_id = msg.datapath.id
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        output_port = self.choose_output_port(in_port, switch_id)

        print("Chosen output port: ", output_port)

        #TODO: Insert your match

        match = ofp_parser.OFPMatch(in_port=in_port)
        actions = [ofp_parser.OFPActionOutput(output_port, 65535)]

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

    #     pkt_ethernet = pkt.get_protocol(ethernet.ethernet)
    #     if not pkt_ethernet:
    #         return
    #     pkt_arp = pkt.get_protocol(arp.arp)
    #     if pkt_arp:
    #         self._handle_arp(datapath, port, pkt_ethernet, pkt_arp)
    #         return
    #     pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
    #     pkt_icmp = pkt.get_protocol(icmp.icmp)
    #     if pkt_icmp:
    #         self._handle_icmp(datapath, port, pkt_ethernet, pkt_ipv4, pkt_icmp)
    #         return

    # def _handle_arp(self, datapath, port, pkt_ethernet, pkt_arp):
    #     if pkt_arp.opcode != arp.ARP_REQUEST:
    #         return
    #     pkt = packet.Packet()
    #     pkt.add_protocol(ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
    #                                        dst=pkt_ethernet.src,
    #                                        src=self.hw_addr))
    #     pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
    #                              src_mac=self.hw_addr,
    #                              src_ip=self.ip_addr,
    #                              dst_mac=pkt_arp.src_mac,
    #                              dst_ip=pkt_arp.src_ip))
    #     self._send_packet(datapath, port, pkt)

    # def _handle_icmp(self, datapath, port, pkt_ethernet, pkt_ipv4, pkt_icmp):
    #     if pkt_icmp.type != icmp.ICMP_ECHO_REQUEST:
    #         return
    #     pkt = packet.Packet()
    #     pkt.add_protocol(ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
    #                                        dst=pkt_ethernet.src,
    #                                        src=self.hw_addr))
    #     pkt.add_protocol(ipv4.ipv4(dst=pkt_ipv4.src,
    #                                src=self.ip_addr,
    #                                proto=pkt_ipv4.proto))
    #     pkt.add_protocol(icmp.icmp(type_=icmp.ICMP_ECHO_REPLY,
    #                                code=icmp.ICMP_ECHO_REPLY_CODE,
    #                                csum=0,
    #                                data=pkt_icmp.data))
    #     self._send_packet(datapath, port, pkt)

    # def _send_packet(self, datapath, port, pkt):
    #     ofproto = datapath.ofproto
    #     parser = datapath.ofproto_parser
    #     pkt.serialize()
    #     self.logger.info("packet-out %s" % (pkt,))
    #     data = pkt.data
    #     actions = [parser.OFPActionOutput(port=port)]
    #     out = parser.OFPPacketOut(datapath=datapath,
    #                               buffer_id=ofproto.OFP_NO_BUFFER,
    #                               in_port=ofproto.OFPP_CONTROLLER,
    #                               actions=actions,
    #                               data=data)
    #     datapath.send_msg(out)

    def choose_output_port(self, in_port, switch_id):  # ,switch ID
        if switch_id==1:
            return self.forwarding_table['s1']['in_port='+str(in_port)]
        if switch_id==2:
            return self.forwarding_table['s2']['in_port='+str(in_port)]