# ==============================================================================
# Copyright (C) 2013 NoviFlow Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
from ryu.base.app_manager import RyuApp
import ryu.controller.ofp_event as ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.ofproto.ofproto_v1_3 import OFP_VERSION

from novilib.set_config_table import create_table_features
from proto.experimenter_of13 import ConfigUdpPayloadSizeOffset, NoviMatch, SetUdpPayload

import sys, signal, logging

from rene import *

RANGES = { (80, 88): 1,
           (10, 15): 2,
           (20, 24): 3 }

LOG = logging.getLogger(__name__)
novi_app_name = 'novi_app_name'

""" 
Ctrl-C Handler
"""
def ctrl_c_handler(signal, frame):
    LOG.info("#### Ctrl-C. Exiting Application ####")
    sys.exit(0)

USE_RENE = True
   
""" 
Main Application
"""
class UdpPayloadExample(RyuApp):
    OFP_VERSIONS = [OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(UdpPayloadExample, self).__init__(*args, **kwargs)
        signal.signal(signal.SIGINT, ctrl_c_handler)
        self.logger.info('#### Starting Example application to show usage of RENE ####')
        

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        self.logger.info("Established connection with datapath ID: 0x%x" % ev.msg.datapath_id)
        
        if not USE_RENE:
            match_list = {0: ['eth_type', 'ip_proto']}
            tab_ids = [0]
            datapath.send_msg(create_table_features(datapath, ev.msg.n_tables,
                                                    table_id=tab_ids, match_list=match_list))
            datapath.send_msg(parser.OFPBarrierRequest(datapath))

            match = parser.OFPMatch(eth_type=0x0800,ip_proto=6)
            out = parser.OFPActionOutput(ofproto.OFPP_IN_PORT)
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, [out])]
            mod = parser.OFPFlowMod(datapath=datapath, table_id=0,
                                match=match, instructions=inst)
            datapath.send_msg(mod)
            return

        # Match fields to be supported in the tables
        matches_t0 = ['eth_type', 'ip_proto', 'tcp_dst']
        matches_t1 = ['metadata']
        match_list = { 0: matches_t0, 1: matches_t1 }
        # List of table_id to be configured with the previous match fields
        tab_ids = [0, 1]
        
        # Configure table to include UDP payload match field
        datapath.send_msg(create_table_features(datapath, ev.msg.n_tables, 
                                                table_id=tab_ids, match_list=match_list))
        datapath.send_msg(parser.OFPBarrierRequest(datapath))
        
        # Add a flow to match on UDP payload and to set a new value
        #output = parser.OFPActionOutput(output_port, ofproto.OFPCML_NO_BUFFER)
        #exp_act = SetUdpPayload(set_size, set_offset, set_value)
        #instructions = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, [exp_act, output])]
         
        #udp_match = NoviMatch(udp_payload=m_udp_val)
        #flow_mod = datapath.ofproto_parser.OFPFlowMod(
        #    datapath, table_id=0, command=ofproto.OFPFC_ADD, priority=3000, 
        #    match=udp_match, instructions=instructions)
        #datapath.send_msg(flow_mod)

        # Install conversion flows
        for i in range(65536):
            match = parser.OFPMatch(eth_type=0x0800,ip_proto=6,tcp_dst=i)
            inst = [ parser.OFPInstructionWriteMetadata(encodeValue(i), 0),
                     parser.OFPInstructionGotoTable(1) ]
            mod = parser.OFPFlowMod(datapath=datapath, table_id=0,
                                match=match, instructions=inst)
            datapath.send_msg(mod)

        datapath.send_msg(parser.OFPBarrierRequest(datapath))

        # Install classification flows
        for (s, t) in RANGES:
            (value, mask) = encodeRange(s, t)

            v = RANGES[(s,t)]
            out = parser.OFPActionOutput(ofproto.OFPP_IN_PORT)
            setvalue = parser.OFPActionSetField(tcp_dst=v)
            match = parser.OFPMatch(metadata=(value, mask))
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, [setvalue, out])]

            mod = parser.OFPFlowMod(datapath=datapath, table_id = 1,
                                match=match, instructions=inst)

            datapath.send_msg(mod)
