"""
=========================================================================
MeshNetworkRTL_test.py
=========================================================================
Test for NetworkRTL

Author : Yanghui Ou, Cheng Tan
  Date : Mar 20, 2019
"""
from pymtl3                           import *
from pymtl3.stdlib.rtl.queues         import NormalQueueRTL
from pymtl3.stdlib.test.test_srcs     import TestSrcRTL
from ocn_pclib.test.net_sinks         import TestNetSinkRTL
from pymtl3.stdlib.test               import TestVectorSimulator
from meshnet.MeshNetworkRTL           import MeshNetworkRTL
from meshnet.DORYMeshRouteUnitRTL     import DORYMeshRouteUnitRTL
from meshnet.DORXMeshRouteUnitRTL     import DORXMeshRouteUnitRTL
from router.InputUnitRTL              import InputUnitRTL
from ocn_pclib.ifcs.positions         import mk_mesh_pos
from ocn_pclib.ifcs.packets           import mk_mesh_pkt
from pymtl3.passes.sverilog           import ImportPass, TranslationPass

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, MsgType, mesh_wid, mesh_ht, src_msgs, sink_msgs,
                 src_initial, src_interval, sink_initial, sink_interval,
                 arrival_time=None ):

    MeshPos = mk_mesh_pos( mesh_wid, mesh_ht )
    s.num_routers = mesh_wid * mesh_ht
    s.dut = MeshNetworkRTL( MsgType, MeshPos, mesh_wid, mesh_ht, 0)
    match_func = lambda a, b : a.payload == b.payload

    s.srcs  = [ TestSrcRTL   ( MsgType, src_msgs[i],  src_initial,  src_interval  )
                for i in range ( s.dut.num_routers ) ]
    if arrival_time != None:
      s.sinks = [ TestNetSinkRTL( MsgType, sink_msgs[i], sink_initial,
                  sink_interval, arrival_time[i], match_func=match_func)
                  for i in range ( s.dut.num_routers ) ]
    else:
      s.sinks = [ TestNetSinkRTL  ( MsgType, sink_msgs[i], sink_initial,
                  sink_interval, match_func=match_func)
                  for i in range ( s.dut.num_routers ) ]

    # Connections

    for i in range ( s.dut.num_routers ):
      s.srcs[i].send //= s.dut.recv[i]
      s.dut.send[i]  //= s.sinks[i].recv

  def done( s ):
    srcs_done = 1
    sinks_done = 1
    for i in range( s.num_routers ):
      if s.srcs[i].done() == 0:
        srcs_done = 0
    for i in range( s.num_routers ):
      if s.sinks[i].done() == 0:
        sinks_done = 0
    return srcs_done and sinks_done
  def line_trace( s ):
    return s.dut.line_trace()

#-------------------------------------------------------------------------
# run_rtl_sim
#-------------------------------------------------------------------------

def run_sim( test_harness, max_cycles=100 ):

  # Create a simulator

  test_harness.elaborate()
  test_harness.apply( DynamicSim )
  test_harness.sim_reset()

  # Run simulation

  ncycles = 0
  print()
  print( "{}:{}".format( ncycles, test_harness.line_trace() ))
  while not test_harness.done() and ncycles < max_cycles:
    test_harness.tick()
    ncycles += 1
    print( "{}:{}".format( ncycles, test_harness.line_trace() ))

  # Check timeout

  assert ncycles < max_cycles

  test_harness.tick()
  test_harness.tick()
  test_harness.tick()

#-------------------------------------------------------------------------
# Test cases (specific for 4x4 mesh)
#-------------------------------------------------------------------------

def test_srcsink_mesh4x4():

  #           src, dst, payload
  test_msgs = [ (0, 15, 101), (1, 14, 102), (2, 13, 103), (3, 12, 104),
                (4, 11, 105), (5, 10, 106), (6,  9, 107), (7,  8, 108),
                (8,  7, 109), (9,  6, 110), (10, 5, 111), (11, 4, 112),
                (12, 3, 113), (13, 2, 114), (14, 1, 115), (15, 0, 116) ]

  src_packets  =  [ [],[],[],[],
                    [],[],[],[],
                    [],[],[],[],
                    [],[],[],[] ]

  sink_packets =  [ [],[],[],[],
                    [],[],[],[],
                    [],[],[],[],
                    [],[],[],[] ]

  # note that need to yield one/two cycle for reset
  arrival_pipes = [[8], [6], [6], [8],
                   [6], [4], [4], [6],
                   [6], [4], [4], [6],
                   [8], [6], [6], [8]]

  mesh_wid = 4
  mesh_ht  = 4

  PacketType = mk_mesh_pkt( mesh_wid, mesh_ht )
  for (src, dst, payload) in test_msgs:
    pkt = PacketType( src%mesh_wid, src//mesh_wid, dst%mesh_wid, dst//mesh_wid, 1, payload )
    src_packets [src].append( pkt )
    sink_packets[dst].append( pkt )

  th = TestHarness( PacketType, mesh_wid, mesh_ht, src_packets, sink_packets,
                    0, 0, 0, 0, arrival_pipes )
  run_sim( th )
