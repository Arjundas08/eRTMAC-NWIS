"""
NWIS PULSE — Canonical Engineering Telemetry Normalizer (Phase 06)
Converts raw drilling telemetry vendor mnemonics and engineering units into
the canonical NWIS measurement contract.

Standard Canonical Units:
- Depths (MD, TVD, Bit Depth): meters (m)
- Rate of Penetration (ROP): meters/hour (m/h)
- Weight on Bit (WOB): kilonewtons (kN)
- Rotary Speed (RPM): revolutions per minute (rpm)
- Surface Torque: kilonewton-meters (kN.m)
- Standpipe Pressure (SPP): kilopascals (kPa)
- Hookload: kilonewtons (kN)
- Flow In: liters/minute (L/min)
- Flow Out: percent (%)
- Pit Volume: cubic meters (m³)
- Mud Weight: specific gravity (sg)
- Equivalent Circulating Density (ECD): specific gravity (sg)
- Total Gas: percent (%)
"""

from typing import Dict, Any, Tuple, Optional


# Canonical mnemonic aliases
MNEMONIC_MAP = {
    # Depths
    "md": "MD", "dept": "MD", "dmea": "MD", "bitdepth": "BIT_DEPTH", "bpos": "BIT_DEPTH",
    "dbtm": "BIT_DEPTH", "depth_md": "MD", "tvd": "TVD", "dver": "TVD", "depth_tvd": "TVD",
    
    # Mechanical
    "rop": "ROP", "ropa": "ROP", "rop5": "ROP", "rop_avg": "ROP", "rateofpenetration": "ROP",
    "wob": "WOB", "woba": "WOB", "wobk": "WOB", "weightonbit": "WOB",
    "rpm": "RPM", "rpma": "RPM", "rpm_surf": "RPM", "rotaryspeed": "RPM",
    "torque": "TORQUE", "torqa": "TORQUE", "stor": "TORQUE", "surfacetorque": "TORQUE",
    "hookload": "HOOKLOAD", "hkld": "HOOKLOAD", "hlda": "HOOKLOAD",
    
    # Hydraulics
    "spp": "SPP", "sppa": "SPP", "pres": "SPP", "standpipepressure": "SPP",
    "flow_in": "FLOW_IN", "flowin": "FLOW_IN", "flwi": "FLOW_IN", "flowina": "FLOW_IN",
    "flow_out": "FLOW_OUT", "flowout": "FLOW_OUT", "flwo": "FLOW_OUT", "flowouta": "FLOW_OUT",
    "pit_volume": "PIT_VOLUME", "pitvol": "PIT_VOLUME", "pvol": "PIT_VOLUME", "pvola": "PIT_VOLUME", "actvol": "PIT_VOLUME",
    "mud_weight": "MUD_WEIGHT", "mudw": "MUD_WEIGHT", "mwin": "MUD_WEIGHT", "mw": "MUD_WEIGHT",
    "ecd": "ECD", "ecdbit": "ECD", "ecd_sg": "ECD",
    
    # Mud Logging / Gas
    "gas": "GAS_TOTAL", "gast": "GAS_TOTAL", "tgas": "GAS_TOTAL", "totalgas": "GAS_TOTAL"
}


def normalize_mnemonic(raw_mnemonic: str) -> str:
    """Maps vendor-specific mnemonic to canonical channel name."""
    clean = raw_mnemonic.strip().lower().replace(" ", "_")
    return MNEMONIC_MAP.get(clean, raw_mnemonic.upper())


def convert_unit(val: float, source_unit: str, target_unit: str) -> Tuple[float, str]:
    """
    Deterministically converts physical units between petroleum engineering standards.
    Returns (converted_value, target_unit).
    """
    s_unit = source_unit.strip().lower()
    t_unit = target_unit.strip().lower()

    if s_unit == t_unit:
        return val, target_unit

    # Length / Depth conversions
    if s_unit in ["ft", "feet", "foot"] and t_unit in ["m", "meter", "meters"]:
        return val * 0.3048, "m"
    if s_unit in ["m", "meter", "meters"] and t_unit in ["ft", "feet"]:
        return val / 0.3048, "ft"

    # Velocity / ROP conversions
    if s_unit in ["ft/h", "ft/hr", "fph"] and t_unit in ["m/h", "m/hr"]:
        return val * 0.3048, "m/h"
    if s_unit in ["m/h", "m/hr"] and t_unit in ["ft/h", "ft/hr"]:
        return val / 0.3048, "ft/h"

    # Force / WOB / Hookload conversions
    if s_unit in ["klbs", "klbf", "k-lbs"] and t_unit in ["kn", "kilonewtons"]:
        return val * 4.44822, "kN"
    if s_unit in ["lbs", "lbf"] and t_unit in ["kn", "kilonewtons"]:
        return (val * 4.44822) / 1000.0, "kN"
    if s_unit in ["t", "tonne", "tonnes"] and t_unit in ["kn", "kilonewtons"]:
        return val * 9.80665, "kN"

    # Torque conversions
    if s_unit in ["kft.lb", "kft-lb", "k-ft-lb"] and t_unit in ["kn.m", "kn*m"]:
        return val * 1.355818, "kN.m"
    if s_unit in ["ft.lb", "ft-lb", "ft.lbf"] and t_unit in ["kn.m", "kn*m"]:
        return (val * 1.355818) / 1000.0, "kN.m"

    # Pressure conversions
    if s_unit in ["psi", "psia", "psig"] and t_unit in ["kpa", "kilopascal"]:
        return val * 6.89476, "kPa"
    if s_unit in ["bar", "bars"] and t_unit in ["kpa", "kilopascal"]:
        return val * 100.0, "kPa"
    if s_unit in ["kpa"] and t_unit in ["psi"]:
        return val / 6.89476, "psi"

    # Flow rate conversions
    if s_unit in ["gpm", "gal/min", "usgpm"] and t_unit in ["l/min", "lpm"]:
        return val * 3.78541, "L/min"
    if s_unit in ["l/min", "lpm"] and t_unit in ["gpm"]:
        return val / 3.78541, "gpm"

    # Volume conversions
    if s_unit in ["bbl", "bbls", "barrels"] and t_unit in ["m3", "m³", "cubic_meters"]:
        return val * 0.158987, "m³"
    if s_unit in ["m3", "m³"] and t_unit in ["bbl"]:
        return val / 0.158987, "bbl"

    # Density conversions
    if s_unit in ["ppg", "lb/gal", "lbm/gal"] and t_unit in ["sg", "g/cm3"]:
        return val * 0.119826, "sg"
    if s_unit in ["sg", "g/cm3"] and t_unit in ["ppg"]:
        return val / 0.119826, "ppg"

    # Fallback to no conversion if unknown
    return val, source_unit


def canonicalize_packet(raw_channels: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes dictionary of raw channels with values & units and produces
    normalized measurements in canonical NWIS units.
    Preserves original values in metadata.
    """
    normalized = {}
    metadata = {}

    target_units = {
        "MD": "m",
        "BIT_DEPTH": "m",
        "TVD": "m",
        "ROP": "m/h",
        "WOB": "kN",
        "RPM": "rpm",
        "TORQUE": "kN.m",
        "SPP": "kPa",
        "HOOKLOAD": "kN",
        "FLOW_IN": "L/min",
        "FLOW_OUT": "%",
        "PIT_VOLUME": "m³",
        "MUD_WEIGHT": "sg",
        "ECD": "sg",
        "GAS_TOTAL": "%"
    }

    for raw_mne, payload in raw_channels.items():
        if isinstance(payload, dict):
            raw_val = payload.get("value")
            raw_unit = payload.get("unit", "")
        else:
            raw_val = payload
            raw_unit = ""

        canonical_name = normalize_mnemonic(raw_mne)
        target_unit = target_units.get(canonical_name, raw_unit)

        if isinstance(raw_val, (int, float)):
            conv_val, final_unit = convert_unit(float(raw_val), raw_unit, target_unit)
            normalized[canonical_name] = round(conv_val, 4)
            metadata[canonical_name] = {
                "original_mnemonic": raw_mne,
                "original_value": raw_val,
                "original_unit": raw_unit,
                "normalized_unit": final_unit
            }
        else:
            normalized[canonical_name] = raw_val

    return {
        "canonical_channels": normalized,
        "channel_metadata": metadata
    }
