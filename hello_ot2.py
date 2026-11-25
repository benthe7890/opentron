from opentrons import protocol_api

metadata = {"protocolName": "Hello OT-2", "apiLevel": "2.26"}


def run(protocol: protocol_api.ProtocolContext):
    tips = protocol.load_labware("opentrons_96_tiprack_300ul", 1)
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", 2)
    p300 = protocol.load_instrument("p300_single_gen2", "right", tip_racks=[tips])
    p300.transfer(100, plate["A1"], plate["B1"])
