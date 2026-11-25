from opentrons import protocol_api

metadata = {
    "protocolName": "Fluorescein 1:2 Serial Dilution (4 replicates)",
    "description": (
        "12-well 2-fold serial dilution of fluorescein in PBS, repeated in rows A-D. "
        "In each row, wells 1-11 hold the dilution series and well 12 is a PBS-only "
        "blank. Every well ends at 100 uL. One tip per replicate row. Excess liquid "
        "goes to a dedicated waste well in the reservoir."
    ),
    "apiLevel": "2.26",
}

REPLICATES = 4      # rows A, B, C, D
VOLUME = 100        # uL in each well at the end
MIX_REPS = 5
MIX_VOL = 80

# Tip-retention controls: slow liquid handling so less liquid clings to the tip
ASPIRATE_RATE = 50   # uL/s (P300 GEN2 default is ~92)
DISPENSE_RATE = 50   # uL/s
SETTLE_SECONDS = 1   # pause after aspirating so liquid settles before the tip moves


def run(protocol: protocol_api.ProtocolContext):
    # Labware
    tips = protocol.load_labware("opentrons_96_tiprack_300ul", 1)
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", 2)
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", 3)
    p300 = protocol.load_instrument("p300_single_gen2", "right", tip_racks=[tips])

    p300.flow_rate.aspirate = ASPIRATE_RATE
    p300.flow_rate.dispense = DISPENSE_RATE

    # Liquid definitions (shows up in the Opentrons App deck map / setup)
    fluorescein = protocol.define_liquid(
        name="Fluorescein",
        description="Pure fluorescein stock",
        display_color="#3CB043",
    )
    pbs = protocol.define_liquid(
        name="PBS",
        description="Phosphate-buffered saline (diluent and blank)",
        display_color="#4A90E2",
    )

    fluorescein_src = reservoir["A1"]
    pbs_src = reservoir["A2"]
    waste = reservoir["A12"]  # dedicated waste well - leave it empty at the start

    # Needed: fluorescein 4 x 200 uL = 800 uL; PBS 4 x 11 x 100 uL = 4.4 mL (+ dead volume)
    fluorescein_src.load_liquid(liquid=fluorescein, volume=2000)
    pbs_src.load_liquid(liquid=pbs, volume=6000)

    for row in plate.rows()[:REPLICATES]:  # each row is one replicate: A1..A12, B1..B12, ...
        # One fresh tip per replicate, used for that whole row
        p300.pick_up_tip()

        # 1) 100 uL PBS into wells 2-12 (well 12 stays PBS-only blank)
        for well in row[1:]:
            p300.aspirate(VOLUME, pbs_src)
            p300.dispense(VOLUME, well.bottom(2))
            p300.blow_out(well.top(-2))

        # 2) 200 uL pure fluorescein into well 1
        p300.aspirate(2 * VOLUME, fluorescein_src)
        p300.dispense(2 * VOLUME, row[0].bottom(2))
        p300.blow_out(row[0].top(-2))

        # Pre-wet the tip in the fluorescein so the first transfer is not short
        # (a dry tip keeps a film of liquid on its inner wall).
        p300.mix(3, MIX_VOL, row[0].bottom(2))
        p300.blow_out(row[0].top(-2))

        # 3) Serial dilution: 100 uL from well n -> n+1, for wells 1..10 -> 2..11
        for src, dest in zip(row[:10], row[1:11]):
            p300.aspirate(VOLUME, src.bottom(1))
            protocol.delay(seconds=SETTLE_SECONDS)
            # Wipe droplets off the outside of the tip in the more concentrated well,
            # so they are not carried into the next well.
            p300.touch_tip(src)
            p300.dispense(VOLUME, dest.bottom(2))
            p300.mix(MIX_REPS, MIX_VOL, dest.bottom(2))
            p300.blow_out(dest.top(-2))
            p300.touch_tip(dest)

        # 4) Remove 100 uL from well 11 into the waste well so it ends at 100 uL.
        #    Dispense from the top so the tip never touches the waste liquid.
        p300.aspirate(VOLUME, row[10].bottom(1))
        protocol.delay(seconds=SETTLE_SECONDS)
        p300.touch_tip(row[10])
        p300.dispense(VOLUME, waste.top(-2))
        p300.blow_out(waste.top(-2))

        p300.drop_tip()
