#!/usr/bin/env python3
"""
Fixed seed_timetable.py (standalone)
- Proper SSH local port forwarding with Paramiko
- Robust SQLAlchemy Core usage
"""

import os, sys, signal, argparse, socket, select, threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from configparser import ConfigParser
from dotenv import load_dotenv
from colorama import Fore, Style, init

import paramiko
from sqlalchemy import create_engine, text, MetaData, Table, Column, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

init(autoreset=True)

# ---------- Config ----------
def load_configuration():
    load_dotenv()  # .env
    cfg = ConfigParser()
    if not cfg.read("config.ini"):
        raise RuntimeError("config.ini not found in current directory")

    pg = cfg["postgres"]
    host = pg.get("host", "127.0.0.1")
    port = int(pg.get("port", "5432"))
    db   = pg.get("default_db", "postgres")

    # DB user/pass from .env (per your constraints)
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    if not db_user or not db_pass:
        raise RuntimeError("DB_USER/DB_PASS missing in .env")

    # SSH creds from .env
    ssh_host = os.getenv("SSH_HOST")
    ssh_port = int(os.getenv("SSH_PORT", "22"))
    ssh_user = os.getenv("SSH_USER")
    ssh_pass = os.getenv("SSH_PASS")
    if not (ssh_host and ssh_user and ssh_pass):
        raise RuntimeError("SSH_HOST/SSH_USER/SSH_PASS must be set in .env")

    # SQLAlchemy URL (driver explicit)
    db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@127.0.0.1:{port}/{db}"
    return {
        "db_url": db_url,
        "db_host": host,
        "db_port": port,
        "db_name": db,
        "ssh_host": ssh_host,
        "ssh_port": ssh_port,
        "ssh_user": ssh_user,
        "ssh_pass": ssh_pass,
    }

# ---------- SSH local port-forward (Paramiko-only) ----------
class _Forwarder(threading.Thread):
    def __init__(self, transport, local_port, remote_host, remote_port):
        super().__init__(daemon=True)
        self.transport = transport
        self.local_port = local_port
        self.remote = (remote_host, remote_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", local_port))
        self.sock.listen(5)
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()
        try:
            self.sock.close()
        except Exception:
            pass

    def run(self):
        while not self._stop.is_set():
            r, _, _ = select.select([self.sock], [], [], 0.5)
            if self.sock in r:
                try:
                    client, addr = self.sock.accept()
                except OSError:
                    break
                # open SSH channel to remote
                chan = self.transport.open_channel(
                    "direct-tcpip",
                    (self.remote[0], self.remote[1]),
                    addr
                )
                # start shuttling
                threading.Thread(target=self._pipe, args=(client, chan), daemon=True).start()

    @staticmethod
    def _pipe(client, chan):
        if chan is None:
            client.close()
            return
        try:
            while True:
                r, _, _ = select.select([client, chan], [], [], 0.5)
                if client in r:
                    data = client.recv(65536)
                    if not data:
                        break
                    chan.sendall(data)
                if chan in r:
                    data = chan.recv(65536)
                    if not data:
                        break
                    client.sendall(data)
        finally:
            try: chan.close()
            except Exception: pass
            try: client.close()
            except Exception: pass

@contextmanager
def open_ssh_tunnel(conf):
    """
    Opens an SSH connection and forwards local 127.0.0.1:<db_port> to remote <db_host>:<db_port>.
    Keeps both alive for the with-block; cleans up afterwards.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        conf["ssh_host"],
        port=conf["ssh_port"],
        username=conf["ssh_user"],
        password=conf["ssh_pass"],
        look_for_keys=False,
        allow_agent=False,
        timeout=15,
    )
    transport = ssh.get_transport()
    forwarder = _Forwarder(
        transport=transport,
        local_port=conf["db_port"],           # e.g. 5432
        remote_host=conf["db_host"],          # e.g. 127.0.0.1 (on server)
        remote_port=conf["db_port"]
    )
    forwarder.start()
    try:
        yield
    finally:
        try: forwarder.stop()
        except Exception: pass
        try: ssh.close()
        except Exception: pass

@contextmanager
def db_session(conf):
    """
    Keeps the SSH tunnel alive while the SQLAlchemy Session is open.
    """
    with open_ssh_tunnel(conf):
        engine = create_engine(conf["db_url"], echo=False, poolclass=NullPool, future=True)
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        with Session() as s:
            yield s

# ---------- DB helpers ----------
def ensure_timetables_table(session):
    md = MetaData()
    engine = session.get_bind()
    md.reflect(engine, only=[])
    if "timetables" in md.tables:
        return Table("timetables", md, autoload_with=engine)

    # create table (matches your model)
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS timetables (
            timetable_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            vehicle_id     uuid NOT NULL,
            route_id       uuid NOT NULL,
            departure_time timestamptz NOT NULL,
            arrival_time   timestamptz,
            notes          text,
            created_at     timestamptz NOT NULL DEFAULT now(),
            updated_at     timestamptz NOT NULL DEFAULT now()
        );
    """))
    session.commit()
    md.reflect(engine, only=["timetables"])
    return md.tables["timetables"]

def count_rows(session, table_name):
    return session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar_one()

def insert_row(session, table, rowdict):
    cols = ", ".join(rowdict.keys())
    vals = ", ".join(f":{k}" for k in rowdict.keys())
    stmt = text(f"INSERT INTO {table.name} ({cols}) VALUES ({vals})")
    session.execute(stmt, rowdict)

def update_arrival(session, table, vehicle_id, route_id, departure_time_iso, arrival_time_iso):
    stmt = text(f"""
        UPDATE {table.name}
        SET arrival_time = :arrival_time
        WHERE vehicle_id = :vehicle_id
          AND route_id = :route_id
          AND departure_time = :departure_time
    """)
    session.execute(stmt, {
        "arrival_time": arrival_time_iso,
        "vehicle_id": vehicle_id,
        "route_id": route_id,
        "departure_time": departure_time_iso
    })

# ---------- Data gen ----------
def generate_timetable_data(session, trips_per_vehicle=2, headway_minutes=30):
    """
    Generate timetable entries by distributing available vehicles across real routes.
    """

    vehicles = session.execute(
        text("SELECT vehicle_id, reg_code FROM vehicles WHERE status = 'available' ORDER BY reg_code")
    ).fetchall()

    routes = session.execute(
        text("SELECT route_id, short_name FROM routes WHERE is_active = true ORDER BY short_name")
    ).fetchall()

    if not vehicles:
        print(Fore.YELLOW + "[WARN] No available vehicles found — timetable generation skipped.")
        return []

    if not routes:
        print(Fore.YELLOW + "[WARN] No active routes found — timetable generation skipped.")
        return []

    timetables = []
    now = datetime.utcnow().replace(second=0, microsecond=0)

    # Round-robin distribute vehicles to existing routes
    for i, v in enumerate(vehicles):
        route = routes[i % len(routes)]
        for j in range(trips_per_vehicle):
            dep = now + timedelta(minutes=(i * headway_minutes) + j * 120)
            arr = dep + timedelta(minutes=60)
            timetables.append({
                "vehicle_id": str(v.vehicle_id),
                "route_id": str(route.route_id),
                "departure_time": dep.isoformat() + "Z",
                "arrival_time": arr.isoformat() + "Z",
                "notes": f"Auto-seeded {v.reg_code} on route {route.short_name}"
            })

    return timetables


def write_timetables_sql(timetables, out_dir="."):
    out_path = os.path.join(out_dir, "timetables.sql")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("-- Auto-generated by seed_timetable.py\n\n")
        f.write("CREATE TABLE IF NOT EXISTS timetables (\n")
        f.write("  timetable_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),\n")
        f.write("  vehicle_id   uuid NOT NULL,\n")
        f.write("  route_id     uuid NOT NULL,\n")
        f.write("  departure_time timestamptz NOT NULL,\n")
        f.write("  arrival_time   timestamptz,\n")
        f.write("  notes        text,\n")
        f.write("  created_at   timestamptz NOT NULL DEFAULT now(),\n")
        f.write("  updated_at   timestamptz NOT NULL DEFAULT now()\n")
        f.write(");\n\n")
        f.write("INSERT INTO timetables (vehicle_id, route_id, departure_time, arrival_time, notes) VALUES\n")
        rows = []
        for r in timetables:
            notes = (r["notes"] or "").replace("'", "''")
            rows.append(
                f"  ('{r['vehicle_id']}', '{r['route_id']}', '{r['departure_time']}', '{r['arrival_time']}', '{notes}')"
            )
        f.write(",\n".join(rows))
        f.write(";\n")
    return out_path

# ---------- SIG handling ----------
def graceful_exit(sig, frame):
    print("\nExiting gracefully.")
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)

# ---------- Main seeding ----------
def seed_timetable(interactive=True):
    conf = load_configuration()
    result = {"inserted": 0, "updated": 0, "skipped": 0, "sql_file": None}

    print(Style.DIM + "[INFO] Opening SSH tunnel and DB session...")
    with db_session(conf) as db:
        # Ensure table
        tbl = ensure_timetables_table(db)

        existing = count_rows(db, tbl.name)
        update_mode = False
        if interactive:
            print("""
[Help]
- This seeds the 'timetables' table.
- Interactive mode asks before updating existing rows.
            """)
        if interactive and existing > 0:
            choice = input(f"[?] Found {existing} existing rows. Update arrivals if duplicates? (Y/n, S=skip): ").strip().lower()
            if choice == "s":
                print("[INFO] Skipping.")
                return result
            update_mode = (choice in ("", "y", "yes"))
        elif existing > 0:
            update_mode = True

        data = generate_timetable_data(db, trips_per_vehicle=3, headway_minutes=15)

        for row in data:
            try:
                if update_mode:
                    update_arrival(
                        db, tbl,
                        row["vehicle_id"], row["route_id"],
                        row["departure_time"], row["arrival_time"]
                    )
                    db.commit()
                    result["updated"] += 1
                    if interactive:
                        print(Fore.GREEN + f"[OK] Updated {row['vehicle_id']} / {row['route_id']} @ {row['departure_time']}")
                else:
                    insert_row(db, tbl, row)
                    db.commit()
                    result["inserted"] += 1
                    if interactive:
                        print(Fore.GREEN + f"[OK] Inserted {row['vehicle_id']} / {row['route_id']} @ {row['departure_time']}")
            except Exception as e:
                db.rollback()
                result["skipped"] += 1
                print(Fore.RED + f"[X] {e}")

        # Write SQL file next to script
        sql_path = write_timetables_sql(data, out_dir=os.path.dirname(os.path.abspath(__file__)))
        result["sql_file"] = sql_path
        if interactive:
            print(Style.BRIGHT + f"\nSummary: Inserted={result['inserted']}, Updated={result['updated']}, Skipped={result['skipped']}")
            print(Fore.GREEN + f"[OK] Generated {sql_path}")
    return result

def main():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("-h", "--help", action="store_true")
    args = p.parse_args()
    if args.help:
        print("""
[Help]
- Seeds the 'timetables' table via SSH-tunneled Postgres.
- Reads DB creds from .env; DB host/port/name from config.ini.
- Example: python seed_timetable.py
        """)
        return
    print(seed_timetable(interactive=True))

if __name__ == "__main__":
    main()
