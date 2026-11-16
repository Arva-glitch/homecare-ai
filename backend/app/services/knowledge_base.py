"""Curated household-appliance troubleshooting knowledge used by the rule-based assistant.

Wording deliberately uses "possible causes" — the assistant must not present
uncertain diagnoses as facts.
"""

SYMPTOM_KEYWORDS = {
    "noise": ["noise", "noisy", "sound", "buzz", "humming", "rattle", "rattling", "click", "grinding", "squeak", "loud"],
    "leak": ["leak", "leaking", "water on floor", "dripping", "drip", "puddle", "seeping"],
    "not_cooling": ["not cooling", "no cooling", "warm", "not cold", "cooling less", "weak cooling", "not chilling"],
    "not_heating": ["not heating", "no hot water", "cold water", "not hot", "doesn't heat", "doesnt heat", "lukewarm"],
    "no_power": ["not working", "won't start", "wont start", "doesn't turn on", "dead", "no power", "not turning on", "stopped working"],
    "odor": ["smell", "odor", "odour", "stink", "burning smell", "musty"],
    "vibration": ["vibrat", "shaking", "shakes", "walking", "wobble"],
    "electrical": ["trip", "tripping", "shock", "spark", "mcb", "fuse", "short circuit"],
    "display": ["display", "error code", "blinking", "remote", "panel", "button", "flicker", "no picture", "screen"],
    "water_quality": ["taste", "tds", "cloudy", "dirty water", "water quality", "slow flow", "low flow"],
    "ice": ["ice", "frost", "freezing up", "frosting"],
    "power_consumption": ["electricity", "power bill", "energy", "consumption", "electric bill", "save power", "units"],
}

PROBLEM_CATEGORY_TO_SYMPTOM = {
    "Unusual Noise": "noise",
    "Leakage": "leak",
    "Not Working / No Power": "no_power",
    "Not Cooling": "not_cooling",
    "Not Heating": "not_heating",
    "Electrical / Tripping": "electrical",
    "Bad Odor": "odor",
    "Excess Vibration": "vibration",
    "Display / Controls": "display",
    "Water Quality": "water_quality",
    "High Power Consumption": "power_consumption",
    "Other": "general",
}

CATEGORY_KEYWORDS = {
    "Refrigerator": ["fridge", "refrigerator", "freezer", "refridgerator"],
    "Air Conditioner": [" ac", "ac ", "a/c", "air conditioner", "aircon", "air-conditioner", "split ac", "window ac"],
    "Washing Machine": ["washing machine", "washer", "washing", "laundry"],
    "Television": ["tv", "television", "led tv", "smart tv"],
    "Microwave": ["microwave", "oven", "otg"],
    "Water Purifier": ["purifier", "ro ", "ro,", "water filter", "uv purifier", "ro purifier"],
    "Geyser": ["geyser", "water heater", "heater", "boiler"],
}

KB: dict[str, dict[str, dict]] = {
    "Refrigerator": {
        "noise": {
            "causes": ["Condenser or evaporator fan obstructed or worn", "Compressor working harder than normal",
                       "Fridge not level, causing panels to rattle", "Items on top or behind vibrating"],
            "steps": ["Check the fridge is level and not touching the wall or cabinets",
                      "Clear anything on top of or behind the unit",
                      "Unplug, then clean the rear condenser coils with a soft brush",
                      "Listen to locate the source: inside (fan), back-bottom (compressor or condenser fan)"],
            "pro": "Call a technician if you hear loud clicking at the back, grinding, or the noise comes with poor cooling — compressor or fan-motor faults need professional repair.",
        },
        "not_cooling": {
            "causes": ["Thermostat set too warm", "Dirty condenser coils", "Door gasket not sealing",
                       "Blocked air vents inside the compartment", "Possible gas leak or compressor fault"],
            "steps": ["Set the thermostat to the recommended level (3–4 or about 3–4°C)",
                      "Do the paper test on door seals — paper should not slide out easily",
                      "Do not overload; keep vents inside unblocked", "Clean the condenser coils",
                      "Leave 10 cm clearance around the unit for airflow"],
            "pro": "If it still doesn't cool after 24 hours, or the compressor isn't running, book a technician — refrigerant and compressor work must be done professionally.",
        },
        "leak": {
            "causes": ["Clogged defrost drain", "Cracked or misplaced drip tray", "Damaged water line (models with dispensers)"],
            "steps": ["Clear the defrost drain hole at the back wall of the fridge using warm water",
                      "Check that the drip tray under the fridge is in place and not cracked",
                      "Make sure the fridge tilts slightly backwards so the doors close and drain properly"],
            "pro": "Book servicing if water keeps pooling after clearing the drain, or if water is near electrical parts.",
        },
        "ice": {
            "causes": ["Door left ajar or worn gasket", "Defrost heater or timer fault", "Clogged drain"],
            "steps": ["Check that door seals close fully", "Manually defrost the freezer if ice build-up is heavy",
                      "Avoid placing hot food inside"],
            "pro": "Repeated frost build-up on a frost-free model suggests a defrost-system fault that needs a technician.",
        },
    },
    "Air Conditioner": {
        "not_cooling": {
            "causes": ["Dirty air filters", "Outdoor unit blocked or dirty", "Low refrigerant (possible leak)",
                       "Wrong mode or temperature setting"],
            "steps": ["Confirm it is in Cool mode at 24–26°C", "Clean the indoor filters (every 2–4 weeks in peak season)",
                      "Clear leaves or debris around the outdoor unit", "Close doors and windows while cooling"],
            "pro": "If cooling is still weak after cleaning the filters, book a service — gas top-ups and leak checks need a certified technician.",
        },
        "leak": {
            "causes": ["Clogged condensate drain pipe", "Indoor unit not mounted level", "Dirty filters causing coil freezing"],
            "steps": ["Switch off and clean the filters", "Check the drain pipe outside for blockage or kinks",
                      "Look for ice on the coils — if present, run Fan mode to thaw"],
            "pro": "Persistent dripping from the indoor unit needs a technician to flush the drain line and check the mounting.",
        },
        "noise": {
            "causes": ["Loose panels or screws", "Debris in the fan", "Worn fan motor bearing", "Compressor issue (outdoor unit)"],
            "steps": ["Switch off and check for loose front panels", "Clean filters and look for debris",
                      "Check the outdoor unit stands on a stable surface"],
            "pro": "Grinding, banging, or screeching sounds should be inspected by a technician promptly.",
        },
        "odor": {
            "causes": ["Mould or bacteria on filters or coils", "Stagnant water in the drain pan", "Burning smell may indicate an electrical fault"],
            "steps": ["Clean or replace the filters", "Run Fan mode for 15 minutes after cooling to dry the coils"],
            "pro": "If you smell burning, switch it off at the mains immediately and call a technician.",
        },
    },
    "Washing Machine": {
        "leak": {
            "causes": ["Loose or damaged inlet hose", "Drain hose not secured or clogged", "Worn door seal (front-load)",
                       "Too much detergent causing overflow"],
            "steps": ["Tighten the inlet hose connections and check for cracks",
                      "Inspect the door gasket for tears or trapped debris", "Clean the drain filter (usually bottom-front)",
                      "Use the correct detergent type and amount (HE detergent for front-loaders)"],
            "pro": "If water leaks from underneath the machine, the pump or tub seal may be faulty — book a technician.",
        },
        "noise": {
            "causes": ["Unbalanced load", "Coins or objects in the drum or pump", "Worn drum bearings", "Transit bolts not removed (new machines)"],
            "steps": ["Redistribute the load evenly", "Check the drum and drain filter for foreign objects",
                      "On new machines, confirm the transit bolts were removed"],
            "pro": "A loud rumbling during spin that gets worse over time often points to bearings — a technician should inspect it.",
        },
        "vibration": {
            "causes": ["Machine not level", "Unbalanced load", "Worn shock absorbers or suspension"],
            "steps": ["Adjust the levelling feet and check with a spirit level", "Avoid washing a single heavy item alone",
                      "Place it on a firm floor or an anti-vibration mat"],
            "pro": "Excessive shaking with an even load suggests suspension wear; schedule an inspection.",
        },
        "odor": {
            "causes": ["Detergent and fabric-softener residue", "Damp door seal", "Clogged drain filter"],
            "steps": ["Run an empty hot cycle with drum cleaner or vinegar", "Leave the door open after washes",
                      "Clean the detergent drawer and drain filter monthly"],
            "pro": "Persistent odour after cleaning may indicate a drainage problem that needs servicing.",
        },
    },
    "Water Purifier": {
        "water_quality": {
            "causes": ["Sediment or carbon filter due for replacement", "RO membrane fouled", "UV lamp nearing end of life"],
            "steps": ["Check when the filters were last changed (typically every 6–12 months)",
                      "Check TDS with a meter if you have one", "Flush the purifier for 2–3 minutes"],
            "pro": "Book a filter or membrane replacement with an authorised service technician; don't drink water that tastes or smells unusual.",
        },
        "leak": {
            "causes": ["Loose pipe fittings", "Cracked filter housing", "Faulty float valve or solenoid valve"],
            "steps": ["Switch off the inlet valve", "Check and push in the push-fit connectors", "Look for cracks in the housings"],
            "pro": "Call a technician if the leak is from a housing or internal valve.",
        },
    },
    "Geyser": {
        "not_heating": {
            "causes": ["Thermostat set low or faulty", "Burnt heating element", "Tripped thermal cut-out", "Scale build-up"],
            "steps": ["Check the power supply and the indicator lamp", "Set the thermostat to 50–60°C",
                      "Allow full heating time (20–40 minutes for storage geysers)"],
            "pro": "Element, thermostat, and cut-out replacements involve mains electricity and hot water — use a qualified electrician or technician.",
        },
        "leak": {
            "causes": ["Pressure-relief valve releasing", "Loose inlet or outlet connections", "Corroded tank"],
            "steps": ["Switch off power and the water inlet", "Check whether the drip is from a fitting or from the tank itself"],
            "pro": "Tank leaks or a constantly dripping relief valve need immediate professional attention.",
        },
        "electrical": {
            "causes": ["Element insulation failure", "Moisture in wiring", "Overloaded circuit"],
            "steps": ["Switch off the geyser at the MCB and do not use it"],
            "pro": "A tripping geyser or any shock is a safety hazard — stop using it and call an electrician right away.",
        },
    },
    "Microwave": {
        "not_heating": {
            "causes": ["Faulty magnetron", "Blown high-voltage diode or capacitor", "Door switch fault"],
            "steps": ["Test by heating a cup of water for 1 minute", "Make sure the door closes firmly"],
            "pro": "Microwaves contain high-voltage capacitors that stay dangerous even when unplugged — do not open the casing; have it serviced professionally.",
        },
        "noise": {
            "causes": ["Turntable roller or motor worn", "Magnetron or fan fault"],
            "steps": ["Clean and reseat the turntable and roller ring"],
            "pro": "Loud buzzing or arcing sparks inside need professional inspection.",
        },
        "electrical": {
            "causes": ["Metal object inside", "Damaged waveguide cover", "Internal fault"],
            "steps": ["Stop it immediately if you see sparks", "Remove any metal or foil", "Inspect the waveguide cover for burns"],
            "pro": "Repeated sparking requires a technician.",
        },
    },
    "Television": {
        "display": {
            "causes": ["Loose HDMI or cable", "Wrong input source", "Software glitch", "Backlight or panel fault"],
            "steps": ["Check cables and the input source", "Power-cycle: unplug for 60 seconds",
                      "Update the TV firmware", "Shine a torch at the screen — a faint image suggests a backlight problem"],
            "pro": "Backlight or panel faults require an authorised service centre.",
        },
        "no_power": {
            "causes": ["Power outlet or cable issue", "Remote batteries", "Power-supply board fault"],
            "steps": ["Try another socket", "Use the physical power button", "Check whether the standby LED lights up"],
            "pro": "No standby light at all usually means a power-board fault — book servicing.",
        },
    },
}

GENERAL_BY_SYMPTOM = {
    "no_power": {
        "causes": ["Power socket or plug issue", "Tripped MCB or blown fuse", "Internal power-supply fault"],
        "steps": ["Check the socket with another device", "Check the MCB / distribution board",
                  "Inspect the power cord for damage"],
        "pro": "If the supply is fine but the appliance is dead, a technician should check the internal electronics.",
    },
    "electrical": {
        "causes": ["Insulation failure", "Moisture ingress", "Overloaded circuit", "Faulty earthing"],
        "steps": ["Stop using the appliance and switch it off at the MCB", "Do not touch it with wet hands"],
        "pro": "Electrical tripping or shocks are safety hazards — have a qualified electrician inspect it before further use.",
    },
    "power_consumption": {
        "causes": ["Dirty filters or coils make motors work harder", "Old, low star-rated appliances",
                   "Thermostats set to extremes", "Standby power draw"],
        "steps": ["Set AC to 24–26°C and clean its filters regularly", "Keep fridge coils clean and door seals tight",
                  "Run washing machines with full loads on cold or eco cycles",
                  "Use timers for geysers instead of keeping them on all day",
                  "Switch off TVs and set-top boxes at the plug", "Prefer 5-star BEE rated appliances when replacing old ones"],
        "pro": "An energy audit or a service visit can identify appliances drawing unusually high power.",
    },
    "general": {
        "causes": ["Wear from age or usage", "Missed routine maintenance"],
        "steps": ["Consult the user manual's troubleshooting section", "Power-cycle the appliance",
                  "Note any error codes, sounds, or smells to share with a technician"],
        "pro": "If the issue persists or affects safety, book a professional service.",
    },
}


def lookup(category: str, symptom: str) -> dict:
    entry = KB.get(category, {}).get(symptom)
    if entry:
        return entry
    return GENERAL_BY_SYMPTOM.get(symptom) or GENERAL_BY_SYMPTOM["general"]


def format_troubleshooting(appliance_label: str, category: str, symptom: str, severity: str | None = None) -> str:
    e = lookup(category, symptom)
    lines = [f"**Possible causes for {appliance_label}** (these are possibilities, not a confirmed diagnosis):"]
    lines += [f"- {c}" for c in e["causes"]]
    lines.append("")
    lines.append("**Troubleshooting steps you can safely try:**")
    lines += [f"{i}. {s}" for i, s in enumerate(e["steps"], 1)]
    lines.append("")
    lines.append(f"**When to call a professional:** {e['pro']}")
    if severity in ("High", "Critical"):
        lines.append("")
        lines.append("⚠️ Given the reported severity, stop using the appliance if there is any safety risk "
                     "(burning smell, sparks, shocks, or water near electrics) and book professional servicing soon.")
    return "\n".join(lines)
