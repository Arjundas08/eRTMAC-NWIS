#!/usr/bin/env python3
"""
eRTMAC Telemetry Ingestion Simulator
Simulates a live WITS0/WITSML streaming feed from an active drilling rig.
Streams real-time bit depth increments and triggers NWIS look-ahead hazard warnings.
"""

import time
import requests
import json
import sys

API_BASE_URL = "http://127.0.0.1:8000/api/v1"

def simulate_active_drilling():
    active_well_id = "NO-15/9-F-12"
    kb_elevation = 43.5

    print("==================================================================")
    print("   eRTMAC LIVE TELEMETRY SIMULATION: RIG RIG-OIL-09               ")
    print("==================================================================")
    print(f"Target Well: {active_well_id}")
    print("Streaming protocol: WITSML 1.4.1.1 JSON Adapter")
    print("Connecting to NWIS Decision Support Engine...\n")

    # Depth progression stepping towards the Hugin Sandstone loss zone (2860m TVDSS)
    drilling_profile = [
        {"md": 2850.0, "tvdss": 2806.5, "formation": "Heather FM", "torque": 12.0, "spp": 2800, "flow_out": 98.0},
        {"md": 2875.0, "tvdss": 2831.5, "formation": "Heather FM", "torque": 13.5, "spp": 2850, "flow_out": 97.5},
        {"md": 2893.5, "tvdss": 2850.0, "formation": "Hugin FM",   "torque": 15.0, "spp": 2900, "flow_out": 95.0}, # Approaching loss zone!
        {"md": 2905.0, "tvdss": 2858.0, "formation": "Hugin FM",   "torque": 19.5, "spp": 3450, "flow_out": 82.0}, # Torque spike & pit loss!
        {"md": 2920.0, "tvdss": 2870.0, "formation": "Hugin FM",   "torque": 14.0, "spp": 2950, "flow_out": 92.0}
    ]

    for step in drilling_profile:
        md = step["md"]
        tvdss = step["tvdss"]
        fm = step["formation"]

        payload = {
            "active_well_id": active_well_id,
            "current_bit_depth_md_m": md,
            "current_bit_depth_tvdss_m": tvdss,
            "active_formation": fm,
            "lookahead_window_m": 75.0,
            "recent_telemetry": {
                "rop_mhr": 14.2,
                "wob_klbs": 24.0,
                "rpm": 110.0,
                "torque_kftlbs": step["torque"],
                "spp_psi": step["spp"],
                "flow_in_gpm": 550.0,
                "flow_out_pct": step["flow_out"],
                "pit_volume_m3": 45.0,
                "ecd_sg": 1.28
            }
        }

        print(f"[RIG TELEMETRY] Depth: {md}m MD / {tvdss}m TVDSS | Formation: {fm} | Torque: {step['torque']} kft-lbs | SPP: {step['spp']} psi")

        try:
            res = requests.post(f"{API_BASE_URL}/lookahead/scan", json=payload, timeout=3.0)
            if res.status_code == 200:
                data = res.json()
                hazard_level = data["hazard_level"]
                alerts = data["alerts"]

                if hazard_level in ["WARNING", "CRITICAL"]:
                    print(f"  >>> [!] PROACTIVE LOOK-AHEAD ALERT: LEVEL {hazard_level} ({len(alerts)} offset hazards identified)")
                    for alert in alerts:
                        print(f"      - {alert['hazard_type']} at {alert['projected_tvdss_m']}m TVDSS (Lead: {alert['lead_distance_m']}m ahead)")
                        print(f"        Offset Precedent: {alert['source_offset_well']} | Citation: {alert['source_citation']}")
                        print(f"        Recommended Mitigation: {alert['recommended_mitigation']}")
                else:
                    print(f"  >>> Horizon Status: {hazard_level} (No upcoming hazards in 75m window)")
            else:
                print(f"  >>> API Response Error: {res.status_code}")
        except Exception as e:
            print(f"  >>> Could not reach backend API at {API_BASE_URL}: {e}")

        print("-" * 70)
        time.sleep(1.0)

if __name__ == "__main__":
    simulate_active_drilling()
