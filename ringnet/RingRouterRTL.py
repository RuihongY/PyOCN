#=========================================================================
# RingRouteRTL.py
#=========================================================================
# Ring network-on-chip router
#
# Author : Cheng Tan, Yanghui Ou
#   Date : April 6, 2019

from pymtl3 import *

from ocn_pclib.ifcs.CreditIfc import CreditRecvIfcRTL, CreditSendIfcRTL
from router.Router import Router
from router.SwitchUnitRTL import SwitchUnitRTL
from router.InputUnitCreditRTL import InputUnitCreditRTL
from router.OutputUnitCreditRTL import OutputUnitCreditRTL

from RingRouteUnitRTL import RingRouteUnitRTL

class RingRouterRTL( Router ):

  def construct( s,
    PacketType,
    PositionType,
    InputUnitType=InputUnitCreditRTL,
    RouteUnitType=RingRouteUnitRTL,
    SwitchUnitType=SwitchUnitRTL,
    OutputUnitType=OutputUnitCreditRTL
  ):

    s.num_inports  = 3
    s.num_outports = 3

    # Interface

    s.pos  = InPort( PositionType )
    s.recv = [ CreditRecvIfcRTL( PacketType, 2 ) for _ in range( s.num_inports  ) ]
    s.send = [ CreditSendIfcRTL( PacketType, 2 ) for _ in range( s.num_outports ) ]

    # Components

    s.input_units  = [ InputUnitType( PacketType )
                      for _ in range( s.num_inports ) ]

    s.route_units  = [ RouteUnitType( PacketType, PositionType, s.num_outports )
                      for i in range( s.num_inports ) ]

    s.switch_units = [ SwitchUnitType( PacketType, s.num_inports )
                      for _ in range( s.num_outports ) ]

    s.output_units = [ OutputUnitType( PacketType )
                      for _ in range( s.num_outports ) ]

    # Connection

    for i in range( s.num_inports ):
      s.connect( s.recv[i],             s.input_units[i].recv )
      s.connect( s.input_units[i].give, s.route_units[i].get  )
      s.connect( s.pos,                 s.route_units[i].pos  )

    for i in range( s.num_inports ):
      for j in range( s.num_outports ):
        s.connect( s.route_units[i].give[j], s.switch_units[j].get[i] )

    for j in range( s.num_outports ):
#      s.connect( s.switch_units[j].send, s.output_units[j].recv )
      s.connect( s.switch_units[j].give, s.output_units[j].get )
      s.connect( s.output_units[j].send, s.send[j]              )

  # Line trace

  def line_trace( s ):

    in_trace  = [ "" for _ in range( s.num_inports  ) ]
    out_trace = [ "" for _ in range( s.num_outports ) ]

    for i in range( s.num_inports ):
      in_trace[i]  = "{}".format( s.recv[i].line_trace() )
    for i in range( s.num_outports ):
      out_trace[i] = "{}".format( s.send[i].line_trace() )

    return "{}({}){}".format(
      "|".join( in_trace ),
      s.pos,
      "|".join( out_trace )
    )
