import sqlite3
from typing import List, Dict, Any

VALID_TABLES = {
    "cpus",
    "motherboards",
    "memory_kits",
    "storage_drives",
    "gpus",
    "psus",
}


def get_connection(db_path: str = "parts_catalog.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = "parts_catalog.db") -> None:
    """Creates the 6 hardware specification tables and seeds initial catalog data if empty."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS cpus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            socket TEXT NOT NULL,
            cores INTEGER NOT NULL,
            tdp_w INTEGER NOT NULL,
            price REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS motherboards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            socket TEXT NOT NULL,
            chipset TEXT NOT NULL,
            form_factor TEXT NOT NULL,
            ddr_gen TEXT NOT NULL,
            ram_slots INTEGER NOT NULL,
            max_ram_gb INTEGER NOT NULL,
            max_ram_speed_mts INTEGER NOT NULL,
            m2_slots INTEGER NOT NULL,
            m2_pcie_gen INTEGER NOT NULL,
            price REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS memory_kits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            ddr_gen TEXT NOT NULL,
            capacity_gb INTEGER NOT NULL,
            modules_count INTEGER NOT NULL,
            speed_mts INTEGER NOT NULL,
            cas_latency INTEGER NOT NULL,
            price REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS storage_drives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            capacity_gb INTEGER NOT NULL,
            pcie_gen INTEGER NOT NULL,
            seq_read_mbs INTEGER NOT NULL,
            seq_write_mbs INTEGER NOT NULL,
            price REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS gpus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            vram_gb INTEGER NOT NULL,
            tdp_w INTEGER NOT NULL,
            price REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS psus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            wattage INTEGER NOT NULL,
            efficiency_rating TEXT NOT NULL,
            price REAL NOT NULL
        );
        """
    )

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM cpus")
    if cursor.fetchone()[0] == 0:
        cpus_seed = [
            ("AMD Ryzen 5 5600X", "AMD", "AM4", 6, 65, 139.99),
            ("AMD Ryzen 7 5800X3D", "AMD", "AM4", 8, 105, 319.99),
            ("AMD Ryzen 5 7600X", "AMD", "AM5", 6, 105, 209.99),
            ("AMD Ryzen 7 7800X3D", "AMD", "AM5", 8, 120, 389.99),
            ("Intel Core i5-13600K", "Intel", "LGA1700", 14, 181, 259.99),
            ("Intel Core i7-14700K", "Intel", "LGA1700", 20, 253, 379.99),
        ]
        cursor.executemany(
            "INSERT INTO cpus (name, brand, socket, cores, tdp_w, price) VALUES (?, ?, ?, ?, ?, ?)",
            cpus_seed,
        )

        motherboards_seed = [
            ("MSI B550-A PRO", "AM4", "B550", "ATX", "DDR4", 4, 128, 4400, 2, 4, 109.99),
            ("ASUS ROG Strix B550-I Gaming", "AM4", "B550", "Mini-ITX", "DDR4", 2, 64, 5100, 2, 4, 199.99),
            ("ASRock B450M Pro4", "AM4", "B450", "Micro-ATX", "DDR4", 4, 64, 3200, 2, 3, 79.99),
            ("MSI MAG B650 Tomahawk WiFi", "AM5", "B650", "ATX", "DDR5", 4, 192, 6400, 3, 4, 199.99),
            ("ASUS ROG Strix X670E-E Gaming", "AM5", "X670E", "ATX", "DDR5", 4, 192, 8000, 4, 5, 439.99),
            ("Gigabyte Z790 AORUS Elite AX", "LGA1700", "Z790", "ATX", "DDR5", 4, 192, 7600, 4, 4, 239.99),
        ]
        cursor.executemany(
            """INSERT INTO motherboards 
            (name, socket, chipset, form_factor, ddr_gen, ram_slots, max_ram_gb, max_ram_speed_mts, m2_slots, m2_pcie_gen, price) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            motherboards_seed,
        )

        memory_kits_seed = [
            ("Kingston FURY Beast 16GB (2x8GB) DDR4-3200 CL16", "Kingston", "DDR4", 16, 2, 3200, 16, 44.99),
            ("Kingston FURY Renegade 32GB (2x16GB) DDR4-3600 CL16", "Kingston", "DDR4", 32, 2, 3600, 16, 84.99),
            ("Corsair Vengeance LPX 64GB (4x16GB) DDR4-3600 CL18", "Corsair", "DDR4", 64, 4, 3600, 18, 139.99),
            ("Kingston FURY Beast 32GB (2x16GB) DDR5-5600 CL36", "Kingston", "DDR5", 32, 2, 5600, 36, 98.99),
            ("Kingston FURY Beast 32GB (2x16GB) DDR5-6000 CL30", "Kingston", "DDR5", 32, 2, 6000, 30, 114.99),
            ("Kingston FURY Renegade 32GB (2x16GB) DDR5-7200 CL38", "Kingston", "DDR5", 32, 2, 7200, 38, 154.99),
            ("Kingston FURY Beast 64GB (2x32GB) DDR5-6000 CL30", "Kingston", "DDR5", 64, 2, 6000, 30, 209.99),
        ]
        cursor.executemany(
            """INSERT INTO memory_kits 
            (name, brand, ddr_gen, capacity_gb, modules_count, speed_mts, cas_latency, price) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            memory_kits_seed,
        )

        storage_drives_seed = [
            ("Samsung 970 EVO Plus 1TB M.2 NVMe", "Samsung", 1000, 3, 3500, 3300, 79.99),
            ("Kingston NV2 1TB M.2 NVMe", "Kingston", 1000, 4, 3500, 2100, 62.99),
            ("Kingston KC3000 1TB M.2 NVMe", "Kingston", 1000, 4, 7000, 6000, 94.99),
            ("Kingston KC3000 2TB M.2 NVMe", "Kingston", 2000, 4, 7000, 7000, 149.99),
            ("Kingston FURY Renegade 2TB M.2 NVMe", "Kingston", 2000, 4, 7300, 7000, 164.99),
            ("Crucial T700 2TB M.2 NVMe", "Crucial", 2000, 5, 12400, 11800, 269.99),
        ]
        cursor.executemany(
            """INSERT INTO storage_drives 
            (name, brand, capacity_gb, pcie_gen, seq_read_mbs, seq_write_mbs, price) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            storage_drives_seed,
        )

        gpus_seed = [
            ("AMD Radeon RX 7600", 8, 165, 259.99),
            ("NVIDIA GeForce RTX 4060 Ti", 8, 160, 389.99),
            ("AMD Radeon RX 7800 XT", 16, 263, 499.99),
            ("NVIDIA GeForce RTX 4070 Super", 12, 220, 589.99),
            ("NVIDIA GeForce RTX 4080 Super", 16, 320, 999.99),
        ]
        cursor.executemany(
            "INSERT INTO gpus (name, vram_gb, tdp_w, price) VALUES (?, ?, ?, ?)",
            gpus_seed,
        )

        psus_seed = [
            ("EVGA 450 BR", 450, "80+ Bronze", 49.99),
            ("Corsair CX550", 550, "80+ Bronze", 64.99),
            ("Corsair RM650", 650, "80+ Gold", 84.99),
            ("Corsair RM750e", 750, "80+ Gold", 99.99),
            ("Corsair RM850x", 850, "80+ Gold", 134.99),
        ]
        cursor.executemany(
            "INSERT INTO psus (name, wattage, efficiency_rating, price) VALUES (?, ?, ?, ?)",
            psus_seed,
        )

        conn.commit()

    conn.close()


def get_parts_by_table(table_name: str, db_path: str = "parts_catalog.db") -> List[Dict[str, Any]]:
    """Queries all hardware components from a validated table ordered by price ascending."""
    if table_name not in VALID_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")

    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} ORDER BY price ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows