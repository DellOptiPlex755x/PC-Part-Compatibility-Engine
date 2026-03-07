from validator import (
    check_cpu_socket,
    check_ram_generation,
    check_ram_slots_and_capacity,
    check_ram_speed_limit,
    check_nvme_pcie_bandwidth,
    check_power_budget,
    evaluate_build,
)


def test_cpu_socket_match():
    cpu = {"name": "AMD Ryzen 7 7800X3D", "socket": "AM5"}
    mobo = {"name": "MSI MAG B650 Tomahawk WiFi", "socket": "AM5", "chipset": "B650"}
    res = check_cpu_socket(cpu, mobo)
    assert res["status"] == "PASS"


def test_cpu_socket_mismatch():
    cpu = {"name": "AMD Ryzen 7 7800X3D", "socket": "AM5"}
    mobo = {"name": "Gigabyte Z790 AORUS Elite AX", "socket": "LGA1700", "chipset": "Z790"}
    res = check_cpu_socket(cpu, mobo)
    assert res["status"] == "ERROR"
    assert "Socket mismatch" in res["message"]


def test_ram_generation_match_and_mismatch():
    ram_ddr5 = {"name": "Kingston FURY Beast DDR5", "ddr_gen": "DDR5"}
    mobo_ddr4 = {"name": "MSI B550-A PRO", "ddr_gen": "DDR4"}
    mobo_ddr5 = {"name": "MSI MAG B650 Tomahawk WiFi", "ddr_gen": "DDR5"}

    assert check_ram_generation(ram_ddr5, mobo_ddr5)["status"] == "PASS"
    err_res = check_ram_generation(ram_ddr5, mobo_ddr4)
    assert err_res["status"] == "ERROR"
    assert "Physical notch mismatch" in err_res["message"]


def test_ram_slots_exceeded_on_itx_board():
    ram_4dimm = {"modules_count": 4, "capacity_gb": 64}
    mobo_itx = {"ram_slots": 2, "max_ram_gb": 64}
    res = check_ram_slots_and_capacity(ram_4dimm, mobo_itx)
    assert res["status"] == "ERROR"


def test_ram_slots_and_capacity_valid():
    ram_2dimm = {"modules_count": 2, "capacity_gb": 32}
    mobo_atx = {"ram_slots": 4, "max_ram_gb": 192}
    res = check_ram_slots_and_capacity(ram_2dimm, mobo_atx)
    assert res["status"] == "PASS"


def test_ram_speed_downclock_warning():
    ram_fast = {"speed_mts": 7200}
    mobo_limit = {"max_ram_speed_mts": 6400}
    res = check_ram_speed_limit(ram_fast, mobo_limit)
    assert res["status"] == "WARNING"
    assert "downclock" in res["message"]


def test_nvme_pcie_gen5_on_gen4_slot_warning():
    ssd_gen5 = {"pcie_gen": 5, "seq_read_mbs": 12400}
    mobo_gen4 = {"m2_pcie_gen": 4}
    res = check_nvme_pcie_bandwidth(ssd_gen5, mobo_gen4)
    assert res["status"] == "WARNING"
    assert "7500 MB/s" in res["message"]


def test_nvme_pcie_gen4_on_gen4_slot_pass():
    ssd_gen4 = {"pcie_gen": 4, "seq_read_mbs": 7000}
    mobo_gen4 = {"m2_pcie_gen": 4}
    res = check_nvme_pcie_bandwidth(ssd_gen4, mobo_gen4)
    assert res["status"] == "PASS"


def test_psu_wattage_headroom_states():
    # Estimated load = 120 + 220 + 75 = 415W; Recommended (+25%) = ceil(518.75) = 519W
    cpu = {"tdp_w": 120}
    gpu = {"tdp_w": 220}

    assert check_power_budget(cpu, gpu, {"wattage": 750})["status"] == "PASS"
    assert check_power_budget(cpu, gpu, {"wattage": 450})["status"] == "WARNING"
    assert check_power_budget(cpu, gpu, {"wattage": 350})["status"] == "ERROR"


def test_evaluate_build_returns_all_six_checks():
    cpu = {"name": "Ryzen 7 7800X3D", "socket": "AM5", "tdp_w": 120}
    mobo = {
        "name": "MSI B650",
        "socket": "AM5",
        "chipset": "B650",
        "ddr_gen": "DDR5",
        "ram_slots": 4,
        "max_ram_gb": 192,
        "max_ram_speed_mts": 6400,
        "m2_pcie_gen": 4,
    }
    ram = {"name": "Kingston FURY Beast", "ddr_gen": "DDR5", "modules_count": 2, "capacity_gb": 32, "speed_mts": 6000}
    ssd = {"name": "Kingston KC3000", "pcie_gen": 4, "seq_read_mbs": 7000}
    gpu = {"name": "RTX 4070 Super", "tdp_w": 220}
    psu = {"name": "Corsair RM750e", "wattage": 750}

    results = evaluate_build(cpu, mobo, ram, ssd, gpu, psu)
    assert len(results) == 6
    assert all(r["status"] == "PASS" for r in results)