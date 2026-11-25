"""Group 3 working copy for the OT-2 fluorescein calibration.

The plate and reservoir definitions and source fills below are for simulation.
Before a robot run, confirm Group 3's physical labware, matching definitions,
deck positions, minimum fills and liquid waste position with the demonstrator.
This source layout assumes a trough that spans all eight nozzles.
"""

from opentrons import protocol_api

metadata = {
    "protocolName": "Group 3 Fluorescein Serial Dilution (Whole Plate Draft)",
    "description": (
        "Built-in labware for simulation. Eight parallel twofold series in "
        "columns 1-11, PBS blanks in column 12, 100 uL final volume per well. "
        "One set of eight tips reused across the dilution."
    ),
}
requirements = {"robotType": "OT-2", "apiLevel": "2.26"}

# Liquid volumes and flow rates are per channel.
TRANSFER_UL = 100
MIX_REPS = 5
MIX_UL = 80
ASPIRATE_UL_PER_S = 50
DISPENSE_UL_PER_S = 50
SETTLE_SECONDS = 1

# Heights relative to the feature named here. Check with the actual labware.
SOURCE_ABOVE_BOTTOM_MM = 1
PLATE_ASPIRATE_ABOVE_BOTTOM_MM = 1
PLATE_DISPENSE_ABOVE_BOTTOM_MM = 2
PLATE_BLOW_OUT_BELOW_TOP_MM = 2
WASTE_DISPENSE_BELOW_TOP_MM = 2


def run(protocol: protocol_api.ProtocolContext):
    # Simulation deck. Use the lab's matching definitions and approved slots.
    tips = protocol.load_labware("opentrons_96_tiprack_300ul", 1)
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", 2)
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", 3)
    p300 = protocol.load_instrument("p300_multi_gen2", "left", tip_racks=[tips])
    p300.flow_rate.aspirate = ASPIRATE_UL_PER_S
    p300.flow_rate.dispense = DISPENSE_UL_PER_S

    fluorescein = protocol.define_liquid(
        name="10 uM fluorescein working solution",
        description="Prepared in 1X PBS before loading the robot",
        display_color="#3CB043",
    )
    pbs = protocol.define_liquid(
        name="1X PBS", description="Diluent and blank", display_color="#4A90E2"
    )

    fluorescein_src = reservoir["A1"]
    pbs_src = reservoir["A2"]
    waste = reservoir["A12"]
    # Provisional fills for the simulated trough, in total uL per trough.
    # Plate demand: 1,600 uL dye and 8,800 uL PBS. Waste receives 800 uL.
    fluorescein_src.load_liquid(liquid=fluorescein, volume=4000)
    pbs_src.load_liquid(liquid=pbs, volume=11000)

    # Row A gives the reference position for each full column (rows A-H).
    columns = plate.rows_by_name()["A"]
    first_column = columns[0]
    last_dilution_column = columns[10]

    p300.pick_up_tip()

    # Fill columns 2-12 before the tips encounter dye. Column 12 stays blank.
    for column in columns[1:]:
        p300.aspirate(TRANSFER_UL, pbs_src.bottom(SOURCE_ABOVE_BOTTOM_MM))
        p300.dispense(TRANSFER_UL, column.bottom(PLATE_DISPENSE_ABOVE_BOTTOM_MM))
        p300.blow_out(column.top(-PLATE_BLOW_OUT_BELOW_TOP_MM))

    # Seed column 1, then condition the tips before the first dilution transfer.
    p300.aspirate(2 * TRANSFER_UL, fluorescein_src.bottom(SOURCE_ABOVE_BOTTOM_MM))
    p300.dispense(2 * TRANSFER_UL, first_column.bottom(PLATE_DISPENSE_ABOVE_BOTTOM_MM))
    p300.blow_out(first_column.top(-PLATE_BLOW_OUT_BELOW_TOP_MM))
    p300.mix(3, MIX_UL, first_column.bottom(PLATE_DISPENSE_ABOVE_BOTTOM_MM))
    p300.blow_out(first_column.top(-PLATE_BLOW_OUT_BELOW_TOP_MM))

    # Ten moves: columns 1 -> 2 through 10 -> 11. Mix before moving onward.
    for source, destination in zip(columns[:10], columns[1:11]):
        p300.aspirate(TRANSFER_UL, source.bottom(PLATE_ASPIRATE_ABOVE_BOTTOM_MM))
        protocol.delay(seconds=SETTLE_SECONDS)
        p300.touch_tip(source)
        p300.dispense(TRANSFER_UL, destination.bottom(PLATE_DISPENSE_ABOVE_BOTTOM_MM))
        p300.mix(MIX_REPS, MIX_UL, destination.bottom(PLATE_DISPENSE_ABOVE_BOTTOM_MM))
        p300.blow_out(destination.top(-PLATE_BLOW_OUT_BELOW_TOP_MM))
        p300.touch_tip(destination)

    # Bring column 11 back to 100 uL per well using the empty waste trough.
    p300.aspirate(TRANSFER_UL, last_dilution_column.bottom(PLATE_ASPIRATE_ABOVE_BOTTOM_MM))
    protocol.delay(seconds=SETTLE_SECONDS)
    p300.touch_tip(last_dilution_column)
    p300.dispense(TRANSFER_UL, waste.top(-WASTE_DISPENSE_BELOW_TOP_MM))
    p300.blow_out(waste.top(-WASTE_DISPENSE_BELOW_TOP_MM))
    p300.drop_tip()
