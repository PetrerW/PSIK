from ryu.base import app_manager

from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls

from ryu.ofproto import ofproto_v1_0, ofproto_v1_3

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import ipv6
from ryu.lib.packet import icmp
from ryu.lib.packet import icmpv6


class IcmpResponder(app_manager.RyuApp):
    # OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION, ofproto_v1_3.OFP_VERSION]
    forwarding_table = {
        's1': {
            # out_port = 2
            'src_mac=00:00:00:00:00:01': 2,
            'src_mac=00:00:00:00:00:02': 1,
        },
        's2': {
            'src_mac=00:00:00:00:00:01': 2,
            'src_mac=00:00:00:00:00:02': 1,
        },
        's3': {
            'src_mac=00:00:00:00:00:01': 2,
            'src_mac=00:00:00:00:00:02': 1,
        },
        's4': {
            'src_mac=00:00:00:00:00:01': 2,
            'src_mac=00:00:00:00:00:02': 1,
        },
        's1_offload': {
            'src_mac=00:00:00:00:00:01': 3,
            'src_mac=00:00:00:00:00:02': 1,
        },
        's2_offload': {
            'src_mac=00:00:00:00:00:01': 2,
            'src_mac=00:00:00:00:00:02': 3,
        }
    }

    def __init__(self, *args, **kwargs):
        super(IcmpResponder, self).__init__(*args, **kwargs)
        #How many packets passed through s3 and s4
        self._counters = {3:0, 4:0}
        #Wheter offloading or not
        self._offload = False
        #Wheter all the switches got initial information
        self._init_table = {1:True, 2:True, 3:True, 4:True}
        #Datapaths of the switches
        self.dp_table = {1:None, 2:None, 3:None, 4:None}

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
        switch_id = dp.id
        
        if self.dp_table[switch_id] == None:
            self.dp_table[switch_id]=dp
        print("Datapaths: "+str(self.dp_table))
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        match=ofp_parser.OFPMatch()
        actions = [ofp_parser.OFPActionOutput(ofp.OFPP_CONTROLLER, 65535)]
        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                             actions)]
        
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
        switch_id = msg.datapath.id
        dp = msg.datapath

        pkt = packet.Packet(data=msg.data)
        print("Packet in from "+str(switch_id)+": "+str(pkt))
        # self.logger.info("packet-in %s" % (pkt,))
        eth = pkt.get_protocol(ethernet.ethernet)
        src_mac = eth.src
        ethertype = eth.ethertype
        #0x0800 ipv4
        #0x86DD ipv6

        if self._init_table[switch_id] == True:
            self._init_table[switch_id] = False
            # self._offload = 0
            output_port = self.choose_output_port(src_mac, switch_id, self._offload)

            #Succesfully chosen output_port
            if output_port in [1,2,3]:
                # Remove flow that sends all packets to the controller
                self.remove_controller_flow(dp, switch_id)

                # Add flows with src_mac addresses and sending to the controller
                self.add_mac_src_flow(dp, switch_id, src_mac, msg.buffer_id, output_port)

        # Count IPv4/6 packets
        elif switch_id in [3,4] and ethertype in [0x0800, 0x86DD]:
            #Increment counters for the appropriate switch
            self._counters[switch_id] = self._counters[switch_id] + 1
            print("Counter_s"+str(switch_id)+" = "+str(self._counters[switch_id]))
            if self._counters[switch_id] >= 5:
                self._counters[switch_id] = 0
                print("Counter_s"+str(switch_id)+" = "+str(self._counters[switch_id])+" (reset to zero)")
                
                self.change_offload(1, '00:00:00:00:00:01')
                self.change_offload(2, '00:00:00:00:00:02')
                
                print("Old offload state = "+str(self._offload))
                #Change offloading state
                if self._offload == True:
                    self._offload = False
                else:
                    self._offload = True
                print("New offload state = "+str(self._offload))

    def remove_controller_flow(self, dp, switch_id):
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        match=ofp_parser.OFPMatch()
        actions = [ofp_parser.OFPActionOutput(ofp.OFPP_CONTROLLER, 65535)]
        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                            actions)]
        
        req = ofp_parser.OFPFlowMod(dp, cookie=0, cookie_mask=0, table_id=0,
                                    command=ofp.OFPFC_DELETE, idle_timeout=0, 
                                    hard_timeout=0, priority=32768,
                                    buffer_id=ofp.OFP_NO_BUFFER, out_port=ofp.OFPP_ANY, 
                                    out_group=ofp.OFPG_ANY, flags=0, 
                                    match=match, instructions=inst)

        print("Deleting flow: ("+str(switch_id)+")")
        print(req)
        self.send_flow_mod(dp, req)

    def add_mac_src_flow(self, dp, switch_id, src_mac, buffer_id, output_port):
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        match = ofp_parser.OFPMatch(eth_src=src_mac)
        actions = [ofp_parser.OFPActionOutput(output_port, 65535), 
                    ofp_parser.OFPActionOutput(ofp.OFPP_CONTROLLER, 65535)]
        print(actions)
        table_id=0
        cookie = cookie_mask = 0
        idle_timeout = hard_timeout = 0
        priority = 32768

        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                                actions)]
        req = ofp_parser.OFPFlowMod(dp, cookie=cookie, cookie_mask=cookie_mask,
                                    table_id=table_id, command=ofp.OFPFC_ADD,
                                    idle_timeout=idle_timeout, hard_timeout=hard_timeout,
                                    priority=priority, buffer_id=buffer_id,
                                    out_port=ofp.OFPP_ANY, out_group=ofp.OFPG_ANY,
                                    flags=ofp.OFPFF_SEND_FLOW_REM,
                                    match=match, instructions=inst)

        print("Adding flow: ("+str(switch_id)+")")
        print(req)
        self.send_flow_mod(dp, req)

        #######################################################################
        src_mac = self.swap_mac(src_mac, switch_id)
        output_port = self.choose_output_port(src_mac, switch_id, False)
        match = ofp_parser.OFPMatch(eth_src=src_mac)
        actions = [ofp_parser.OFPActionOutput(output_port, 65535), 
                    ofp_parser.OFPActionOutput(ofp.OFPP_CONTROLLER, 65535)]
        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                                actions)]
        print("New actions: ", actions)
        
        req = ofp_parser.OFPFlowMod(dp, cookie=cookie, cookie_mask=cookie_mask,
                                    table_id=table_id, command=ofp.OFPFC_ADD,
                                    idle_timeout=idle_timeout, hard_timeout=hard_timeout,
                                    priority=priority, buffer_id=buffer_id,
                                    out_port=ofp.OFPP_ANY, out_group=ofp.OFPG_ANY,
                                    flags=ofp.OFPFF_SEND_FLOW_REM,
                                    match=match, instructions=inst)

        print("Adding flow: ("+str(switch_id)+")")
        print(req)
        self.send_flow_mod(dp, req)

    def modify_flow(self, dp, switch_id, src_mac, output_port):
        #OFPFC_MODIFY
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        match = ofp_parser.OFPMatch(eth_src=src_mac)
        actions = [ofp_parser.OFPActionOutput(output_port, 65535), 
                    ofp_parser.OFPActionOutput(ofp.OFPP_CONTROLLER, 65535)]
        print(actions)
        table_id=0
        cookie = cookie_mask = 0
        idle_timeout = hard_timeout = 0
        priority = 32768

        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                                actions)]
        req = ofp_parser.OFPFlowMod(dp, cookie=cookie, cookie_mask=cookie_mask,
                                    table_id=table_id, command=ofp.OFPFC_MODIFY,
                                    idle_timeout=idle_timeout, hard_timeout=hard_timeout,
                                    priority=priority, buffer_id=ofp.OFP_NO_BUFFER,
                                    out_port=ofp.OFPP_ANY, out_group=ofp.OFPG_ANY,
                                    flags=ofp.OFPFF_SEND_FLOW_REM,
                                    match=match, instructions=inst)

        print("Adding flow: ("+str(switch_id)+")")
        print(req)
        self.send_flow_mod(dp, req)

    def send_flow_mod(self, datapath, req):
        datapath.send_msg(req)

    def change_offload(self, switch_id, src_mac):
        output_port = self.choose_output_port(src_mac, switch_id, self._offload)
        self.print_output_port(output_port, switch_id, src_mac)
        self.modify_flow(self.dp_table[switch_id], switch_id, src_mac, output_port)

    #Determine output port on the basis of mac address table
    def choose_output_port(self, mac_addr, switch_id, offload):  # ,switch ID
        if switch_id in [3,4]:
            output_port = self.forwarding_table['s'+str(switch_id)]['src_mac='+str(mac_addr)]
        elif switch_id in [1,2]:
            if self._offload == False:
                output_port = self.forwarding_table['s'+str(switch_id)]['src_mac='+str(mac_addr)]
            else:
                output_port = self.forwarding_table['s'+str(switch_id)+'_offload']['src_mac='+str(mac_addr)]
        else:
            print("Wrong switch_id: "+str(switch_id))
            output_port = -1

        return output_port

    def swap_mac(self, src_mac, switch_id):
        print("Old src_mac: ", src_mac)
        #Swap src_mac addresses
        if src_mac == '00:00:00:00:00:02':
            src_mac = '00:00:00:00:00:01'
        elif src_mac == '00:00:00:00:00:01':
            src_mac = '00:00:00:00:00:02'

        print("New src_mac: ", src_mac)
        output_port = self.choose_output_port(src_mac, switch_id, False)
        self.print_output_port(output_port, switch_id, src_mac)
        return src_mac

    def print_output_port(self, output_port, switch_id, src_mac):
        if output_port == -1:
            print("Cannot determine the output port for switch: ", switch_id, ", src_mac: ", src_mac)
        else:
            print("Chosen output port: ", output_port)

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
