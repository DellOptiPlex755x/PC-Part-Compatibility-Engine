# PC Part Spec & Compatibility Engine

A modular PC hardware configuration, deterministic validation, and performance analytics tool built with **Python**, **SQLite**, **Pytest**, **Streamlit**, and **pandas**.

## Architecture

* **`database.py` (Data Layer):** Initializes a normalized 6-table **SQLite** database (`parts_catalog.db`) modeling specifications across CPUs, motherboards, DDR4/DDR5 DRAM kits, M.2 NVMe PCIe SSDs (Gen3/Gen4/Gen5), GPUs, and PSUs.
* **`validator.py` (Validation Rule Engine):** Pure Python rule engine checking 6 deterministic hardware constraints, distinguishing between physical incompatibilities (`ERROR`) and bus/clock downclocking (`WARNING`).
* **`test_validator.py` (Automated Unit Tests):** **Pytest** test suite verifying boundary conditions across all 6 validation rules.
* **`app.py` (UI & Analytics Dashboard):** Interactive **Streamlit** interface and **pandas** analytics views calculating DRAM CAS latency in nanoseconds (`ns`), estimated PCIe M.2 slot throughput ceilings, and price-to-performance metrics.

## Deterministic Validation Rules

1. **CPU & Motherboard Socket Matching:** Verifies physical socket (`AM4`, `AM5`, `LGA1700`) alignment.
2. **DRAM Generation Compatibility:** Prevents physical notch mismatches between `DDR4` and `DDR5` modules and DIMM slots.
3. **DIMM Slot & Capacity Limits:** Validates module count and total gigabyte capacity against motherboard form-factor limits.
4. **DRAM Frequency Ceiling:** Flags a `WARNING` when selected memory transfer rate (`MT/s`) exceeds motherboard rating and downclocks.
5. **M.2 NVMe PCIe Bandwidth Limits:** Compares SSD PCIe generation (`Gen3`/`Gen4`/`Gen5`) against motherboard M.2 slot generation (`~3,500 MB/s`, `~7,500 MB/s`, `~14,000 MB/s` x4 ceilings).
6. **PSU Wattage & Transient Headroom:** Computes total system thermal load (`CPU TDP + GPU TDP + 75W baseline`) and checks for a 25% transient power headroom margin.

## Quickstart

```bash
pip install -r requirements.txt
pytest -v
streamlit run app.py