import math
from typing import Dict, Any, List

PCIE_X4_BANDWIDTH_LIMITS_MBS = {
    3: 3500,
    4: 7500,
    5: 14000,
}

BASELINE_SYSTEM_OVERHEAD_W = 75


def check_cpu_socket(cpu: Dict[str, Any], mobo: Dict[str, Any]) -> Dict[str, str]:
    """Rule 1: Validates physical CPU socket matching against the motherboard."""
    if cpu["socket"] == mobo["socket"]:
        return {
            "rule": "CPU & Motherboard Socket",
            "status": "PASS",
            "message": f"CPU socket {cpu['socket']} matches motherboard socket ({mobo['chipset']} chipset).",
        }
    return {
        "rule": "CPU & Motherboard Socket",
        "status": "ERROR",
        "message": f"Socket mismatch: {cpu['name']} requires an {cpu['socket']} socket, but {mobo['name']} uses {mobo['socket']}.",
    }


def check_ram_generation(ram: Dict[str, Any], mobo: Dict[str, Any]) -> Dict[str, str]:
    """Rule 2: Validates DRAM generation (DDR4 vs. DDR5) against motherboard DIMM architecture."""
    if ram["ddr_gen"] == mobo["ddr_gen"]:
        return {
            "rule": "DRAM Generation Compatibility",
            "status": "PASS",
            "message": f"Memory generation {ram['ddr_gen']} matches motherboard DIMM slots.",
        }
    return {
        "rule": "DRAM Generation Compatibility",
        "status": "ERROR",
        "message": f"Physical notch mismatch: {ram['name']} is {ram['ddr_gen']}, but {mobo['name']} only accepts {mobo['ddr_gen']} modules.",
    }


def check_ram_slots_and_capacity(ram: Dict[str, Any], mobo: Dict[str, Any]) -> Dict[str, str]:
    """Rule 3: Checks DIMM module count and total capacity against motherboard limits."""
    if ram["modules_count"] > mobo["ram_slots"] or ram["capacity_gb"] > mobo["max_ram_gb"]:
        return {
            "rule": "DIMM Slots & Capacity Limits",
            "status": "ERROR",
            "message": (
                f"Kit has {ram['modules_count']} sticks ({ram['capacity_gb']}GB), exceeding motherboard limit "
                f"({mobo['ram_slots']} slots / {mobo['max_ram_gb']}GB max)."
            ),
        }
    return {
        "rule": "DIMM Slots & Capacity Limits",
        "status": "PASS",
        "message": f"{ram['modules_count']} of {mobo['ram_slots']} DIMM slots used ({ram['capacity_gb']}GB / {mobo['max_ram_gb']}GB max).",
    }


def check_ram_speed_limit(ram: Dict[str, Any], mobo: Dict[str, Any]) -> Dict[str, str]:
    """Rule 4: Checks if DRAM transfer rate (MT/s) exceeds motherboard rated memory clock."""
    if ram["speed_mts"] > mobo["max_ram_speed_mts"]:
        return {
            "rule": "DRAM Frequency Support",
            "status": "WARNING",
            "message": (
                f"Speed downclock: {ram['speed_mts']} MT/s RAM exceeds motherboard rating "
                f"({mobo['max_ram_speed_mts']} MT/s) and will downclock to {mobo['max_ram_speed_mts']} MT/s."
            ),
        }
    return {
        "rule": "DRAM Frequency Support",
        "status": "PASS",
        "message": f"Motherboard supports full {ram['speed_mts']} MT/s XMP/EXPO memory profile.",
    }


def check_nvme_pcie_bandwidth(ssd: Dict[str, Any], mobo: Dict[str, Any]) -> Dict[str, str]:
    """Rule 5: Evaluates M.2 NVMe PCIe generation compatibility and slot bandwidth ceilings."""
    mobo_gen = mobo["m2_pcie_gen"]
    ssd_gen = ssd["pcie_gen"]
    ceiling = PCIE_X4_BANDWIDTH_LIMITS_MBS.get(mobo_gen, 7500)

    if ssd_gen > mobo_gen:
        return {
            "rule": "M.2 NVMe PCIe Bandwidth Limits",
            "status": "WARNING",
            "message": (
                f"PCIe bandwidth cap: PCIe Gen{ssd_gen} SSD ({ssd['seq_read_mbs']} MB/s) is backward-compatible "
                f"with motherboard's PCIe Gen{mobo_gen} M.2 slot, but peak speed will cap at ~{ceiling} MB/s."
            ),
        }
    return {
        "rule": "M.2 NVMe PCIe Bandwidth Limits",
        "status": "PASS",
        "message": f"Motherboard PCIe Gen{mobo_gen} M.2 slot supports full {ssd['seq_read_mbs']} MB/s read throughput.",
    }


def check_power_budget(cpu: Dict[str, Any], gpu: Dict[str, Any], psu: Dict[str, Any]) -> Dict[str, str]:
    """Rule 6: Validates system TDP load and 25% transient spike headroom against PSU wattage."""
    estimated_load = cpu["tdp_w"] + gpu["tdp_w"] + BASELINE_SYSTEM_OVERHEAD_W
    recommended_psu = math.ceil(estimated_load * 1.25)

    if psu["wattage"] < estimated_load:
        return {
            "rule": "Power Supply Headroom",
            "status": "ERROR",
            "message": f"Insufficient power: {psu['wattage']}W PSU is below estimated peak draw ({estimated_load}W).",
        }
    if psu["wattage"] < recommended_psu:
        return {
            "rule": "Power Supply Headroom",
            "status": "WARNING",
            "message": (
                f"Tight power margin: {psu['wattage']}W PSU covers {estimated_load}W load, "
                f"but {recommended_psu}W (+25% headroom) is recommended for transient spikes."
            ),
        }
    return {
        "rule": "Power Supply Headroom",
        "status": "PASS",
        "message": f"{psu['wattage']}W PSU provides {psu['wattage'] - estimated_load}W headroom over {estimated_load}W estimated system draw.",
    }


def evaluate_build(
    cpu: Dict[str, Any],
    mobo: Dict[str, Any],
    ram: Dict[str, Any],
    ssd: Dict[str, Any],
    gpu: Dict[str, Any],
    psu: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Runs all 6 deterministic hardware validation rules on the selected configuration."""
    return [
        check_cpu_socket(cpu, mobo),
        check_ram_generation(ram, mobo),
        check_ram_slots_and_capacity(ram, mobo),
        check_ram_speed_limit(ram, mobo),
        check_nvme_pcie_bandwidth(ssd, mobo),
        check_power_budget(cpu, gpu, psu),
    ]