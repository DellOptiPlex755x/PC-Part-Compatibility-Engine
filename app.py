import streamlit as st
import pandas as pd
from database import init_db, get_parts_by_table
from validator import (
    evaluate_build,
    PCIE_X4_BANDWIDTH_LIMITS_MBS,
    BASELINE_SYSTEM_OVERHEAD_W,
)

st.set_page_config(
    page_title="PC Part Spec & Compatibility Engine",
    page_icon="🖥️",
    layout="wide",
)

# Initialize SQLite database & seed catalog on first run
init_db()

cpus = get_parts_by_table("cpus")
motherboards = get_parts_by_table("motherboards")
memory_kits = get_parts_by_table("memory_kits")
storage_drives = get_parts_by_table("storage_drives")
gpus = get_parts_by_table("gpus")
psus = get_parts_by_table("psus")

st.title("🖥️ PC Part Spec & Compatibility Engine")
st.caption(
    "Hardware configuration, deterministic rule validation, and DRAM/NVMe performance analytics powered by Python, SQLite, Pytest, and pandas."
)

# Helper index lookup to pre-select a balanced AM5 + Kingston DDR5/NVMe build by default
def find_default_index(parts_list, target_substring, fallback=0):
    for idx, part in enumerate(parts_list):
        if target_substring.lower() in part["name"].lower():
            return idx
    return fallback


# ---------------- SECTION B: TWO-COLUMN MAIN WORKSPACE ----------------
col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.subheader("1. Select Hardware Components")

    selected_cpu = st.selectbox(
        "Processor (CPU)",
        options=cpus,
        index=find_default_index(cpus, "7800X3D"),
        format_func=lambda x: f"{x['name']} ({x['socket']} | {x['cores']} Cores | {x['tdp_w']}W TDP) — ${x['price']:.2f}",
    )

    selected_mobo = st.selectbox(
        "Motherboard",
        options=motherboards,
        index=find_default_index(motherboards, "B650 Tomahawk"),
        format_func=lambda x: (
            f"{x['name']} ({x['socket']} | {x['ddr_gen']}-{x['max_ram_speed_mts']} | "
            f"PCIe Gen{x['m2_pcie_gen']} M.2 | {x['ram_slots']} Slots) — ${x['price']:.2f}"
        ),
    )

    selected_ram = st.selectbox(
        "Memory (DRAM)",
        options=memory_kits,
        index=find_default_index(memory_kits, "Kingston FURY Beast 32GB (2x16GB) DDR5-6000"),
        format_func=lambda x: (
            f"{x['name']} ({x['ddr_gen']} | {x['speed_mts']} MT/s | CL{x['cas_latency']}) — ${x['price']:.2f}"
        ),
    )

    selected_ssd = st.selectbox(
        "Primary Storage (M.2 NVMe SSD)",
        options=storage_drives,
        index=find_default_index(storage_drives, "Kingston KC3000 2TB"),
        format_func=lambda x: (
            f"{x['name']} (PCIe Gen{x['pcie_gen']} x4 | {x['seq_read_mbs']}/{x['seq_write_mbs']} MB/s) — ${x['price']:.2f}"
        ),
    )

    selected_gpu = st.selectbox(
        "Graphics Card (GPU)",
        options=gpus,
        index=find_default_index(gpus, "4070 Super"),
        format_func=lambda x: f"{x['name']} ({x['vram_gb']}GB VRAM | {x['tdp_w']}W TDP) — ${x['price']:.2f}",
    )

    selected_psu = st.selectbox(
        "Power Supply (PSU)",
        options=psus,
        index=find_default_index(psus, "RM750e"),
        format_func=lambda x: f"{x['name']} ({x['wattage']}W | {x['efficiency_rating']}) — ${x['price']:.2f}",
    )

# Evaluate all 6 deterministic rules
validation_results = evaluate_build(
    selected_cpu,
    selected_mobo,
    selected_ram,
    selected_ssd,
    selected_gpu,
    selected_psu,
)

with col_right:
    st.subheader("2. Live Compatibility Scorecard")
    for res in validation_results:
        status = res["status"]
        text = f"**[{status}] {res['rule']}:** {res['message']}"
        if status == "PASS":
            st.success(text)
        elif status == "WARNING":
            st.warning(text)
        else:
            st.error(text)

# ---------------- SECTION A: TOP TELEMETRY & STATUS BANNER ----------------
total_price = sum(
    part["price"]
    for part in [selected_cpu, selected_mobo, selected_ram, selected_ssd, selected_gpu, selected_psu]
)
estimated_load_w = selected_cpu["tdp_w"] + selected_gpu["tdp_w"] + BASELINE_SYSTEM_OVERHEAD_W
psu_headroom_w = selected_psu["wattage"] - estimated_load_w
headroom_pct = round((psu_headroom_w / selected_psu["wattage"]) * 100)

st.divider()
m1, m2, m3 = st.columns(3)
m1.metric("Total Build Price", f"${total_price:,.2f}")
m2.metric("Estimated System Load", f"{estimated_load_w} W", "CPU + GPU + 75W baseline")
m3.metric(
    "PSU Headroom",
    f"{psu_headroom_w:+d} W ({headroom_pct}% margin)",
    delta=f"{selected_psu['wattage']}W Rated PSU",
    delta_color="normal" if psu_headroom_w >= 0 else "inverse",
)

statuses = [r["status"] for r in validation_results]
if "ERROR" in statuses:
    st.error("CRITICAL ERROR — Physical incompatibility or power deficit detected. Review the compatibility scorecard above.")
elif "WARNING" in statuses:
    st.warning("WARNING — Build is physically compatible, but 1+ components exceed motherboard bus or speed limits.")
else:
    st.success("PASS — All 6 hardware compatibility, bus speed, and power headroom checks passed.")

st.divider()

# ---------------- SECTION C: BOTTOM ANALYTICS TABS (PANDAS) ----------------
st.subheader("3. Hardware Performance & Value Analytics")
tab_ram, tab_ssd, tab_bom = st.tabs(
    [
        "📊 DRAM CAS Latency & Value Analyzer",
        "⚡ NVMe SSD Throughput & PCIe Slot Analyzer",
        "📋 Complete Bill of Materials (CSV Export)",
    ]
)

with tab_ram:
    st.markdown(
        "**Calculated CAS Latency Formula:** `Latency (ns) = (CAS Latency × 2000) / Speed (MT/s)`"
    )
    df_ram = pd.DataFrame(memory_kits)
    df_ram["calculated_cas_latency_ns"] = (df_ram["cas_latency"] * 2000 / df_ram["speed_mts"]).round(2)
    df_ram["price_per_gb"] = (df_ram["price"] / df_ram["capacity_gb"]).round(2)
    df_ram["selected"] = df_ram["id"].apply(lambda x: "✅ Current" if x == selected_ram["id"] else "")

    display_ram = df_ram[
        [
            "selected",
            "name",
            "brand",
            "ddr_gen",
            "capacity_gb",
            "speed_mts",
            "cas_latency",
            "calculated_cas_latency_ns",
            "price_per_gb",
            "price",
        ]
    ].sort_values(by="calculated_cas_latency_ns", ascending=True)

    st.dataframe(
        display_ram.rename(
            columns={
                "selected": "Status",
                "name": "Memory Kit",
                "brand": "Brand",
                "ddr_gen": "Type",
                "capacity_gb": "Capacity (GB)",
                "speed_mts": "Speed (MT/s)",
                "cas_latency": "CL",
                "calculated_cas_latency_ns": "CAS Latency (ns)",
                "price_per_gb": "$ / GB",
                "price": "Price ($)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.bar_chart(
        display_ram.set_index("name")[["calculated_cas_latency_ns", "price_per_gb"]],
        height=300,
    )

with tab_ssd:
    slot_gen = selected_mobo["m2_pcie_gen"]
    slot_cap = PCIE_X4_BANDWIDTH_LIMITS_MBS[slot_gen]
    st.markdown(
        f"**Selected Motherboard M.2 Slot:** `PCIe Gen{slot_gen} x4` (Estimated sequential ceiling: **`~{slot_cap:,} MB/s`**)"
    )

    df_ssd = pd.DataFrame(storage_drives)
    df_ssd["effective_read_mbs"] = df_ssd["seq_read_mbs"].clip(upper=slot_cap)
    df_ssd["bandwidth_limited"] = df_ssd["seq_read_mbs"] > slot_cap
    df_ssd["mbs_per_dollar"] = (df_ssd["effective_read_mbs"] / df_ssd["price"]).round(1)
    df_ssd["price_per_tb"] = (df_ssd["price"] / (df_ssd["capacity_gb"] / 1000)).round(2)
    df_ssd["selected"] = df_ssd["id"].apply(lambda x: "✅ Current" if x == selected_ssd["id"] else "")

    display_ssd = df_ssd[
        [
            "selected",
            "name",
            "brand",
            "pcie_gen",
            "seq_read_mbs",
            "effective_read_mbs",
            "bandwidth_limited",
            "mbs_per_dollar",
            "price_per_tb",
            "price",
        ]
    ].sort_values(by="effective_read_mbs", ascending=False)

    st.dataframe(
        display_ssd.rename(
            columns={
                "selected": "Status",
                "name": "NVMe SSD",
                "brand": "Brand",
                "pcie_gen": "SSD PCIe Gen",
                "seq_read_mbs": "Rated Read (MB/s)",
                "effective_read_mbs": "Effective Read on Board (MB/s)",
                "bandwidth_limited": "Slot Capped?",
                "mbs_per_dollar": "Effective MB/s per $",
                "price_per_tb": "$ / TB",
                "price": "Price ($)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.bar_chart(
        display_ssd.set_index("name")[["seq_read_mbs", "effective_read_mbs"]],
        height=300,
    )

with tab_bom:
    bom_rows = [
        {"Category": "Processor (CPU)", "Component": selected_cpu["name"], "Key Spec": f"{selected_cpu['socket']} | {selected_cpu['tdp_w']}W TDP", "Price ($)": selected_cpu["price"]},
        {"Category": "Motherboard", "Component": selected_mobo["name"], "Key Spec": f"{selected_mobo['socket']} | {selected_mobo['ddr_gen']} | PCIe Gen{selected_mobo['m2_pcie_gen']} M.2", "Price ($)": selected_mobo["price"]},
        {"Category": "Memory (DRAM)", "Component": selected_ram["name"], "Key Spec": f"{selected_ram['capacity_gb']}GB | {selected_ram['speed_mts']} MT/s | CL{selected_ram['cas_latency']}", "Price ($)": selected_ram["price"]},
        {"Category": "Storage (NVMe SSD)", "Component": selected_ssd["name"], "Key Spec": f"{selected_ssd['capacity_gb']}GB | PCIe Gen{selected_ssd['pcie_gen']} | {selected_ssd['seq_read_mbs']} MB/s", "Price ($)": selected_ssd["price"]},
        {"Category": "Graphics Card (GPU)", "Component": selected_gpu["name"], "Key Spec": f"{selected_gpu['vram_gb']}GB VRAM | {selected_gpu['tdp_w']}W TDP", "Price ($)": selected_gpu["price"]},
        {"Category": "Power Supply (PSU)", "Component": selected_psu["name"], "Key Spec": f"{selected_psu['wattage']}W | {selected_psu['efficiency_rating']}", "Price ($)": selected_psu["price"]},
    ]
    df_bom = pd.DataFrame(bom_rows)
    st.dataframe(df_bom, use_container_width=True, hide_index=True)

    csv_bytes = df_bom.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Build Spec (.csv)",
        data=csv_bytes,
        file_name="pc_build_configuration.csv",
        mime="text/csv",
    )