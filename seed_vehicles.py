#!/usr/bin/env python3
"""
Standalone seed_vehicles.py
- Connects to Postgres over SSH tunnel
- Seeds the vehicles table with sample rows
"""

import os, sys, signal, argparse, socket, select, threading
from contextlib import contextmanager
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
    load_dotenv()
    cfg = ConfigParser()
    if not cfg.read("config.ini"):
        raise RuntimeError("config.ini not found")

    pg = cfg["postgres"]
    host = pg.get("host", "127.0.0.1")
    port = int(pg.get("port", "5432"))
    db   = pg.get("default_db", "postgres")

    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    if not db_user or not db_pass:
        raise RuntimeError("DB_USER/DB_PASS missing in .env")

    ssh_host = os.getenv("SSH_HOST")
    ssh_port = int(os.getenv("SSH_PORT", "22"))
    ssh_user = os.getenv("SSH_USER")
    ssh_pass = os.getenv("SSH_PASS")
    if not (ssh_host and ssh_user and ssh_pass):
        raise RuntimeError("SSH_HOST/SSH_USER/SSH_PASS must be set in .env")

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

# ---------- SSH Forwarder ----------
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
        try: self.sock.close()
        except Exception: pass

    def run(self):
        while not self._stop.is_set():
            r, _, _ = select.select([self.sock], [], [], 0.5)
            if self.sock in r:
                try:
                    client, addr = self.sock.accept()
                except OSError:
                    break
                chan = self.transport.open_channel("direct-tcpip", self.remote, addr)
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
                    if not data: break
                    chan.sendall(data)
                if chan in r:
                    data = chan.recv(65536)
                    if not data: break
                    client.sendall(data)
        finally:
            try: chan.close()
            except: pass
            try: client.close()
            except: pass

@contextmanager
def open_ssh_tunnel(conf):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(conf["ssh_host"], port=conf["ssh_port"],
                username=conf["ssh_user"], password=conf["ssh_pass"],
                look_for_keys=False, allow_agent=False, timeout=15)
    transport = ssh.get_transport()
    forwarder = _Forwarder(transport, conf["db_port"], conf["db_host"], conf["db_port"])
    forwarder.start()
    try:
        yield
    finally:
        try: forwarder.stop()
        except: pass
        try: ssh.close()
        except: pass

@contextmanager
def db_session(conf):
    with open_ssh_tunnel(conf):
        engine = create_engine(conf["db_url"], echo=False, poolclass=NullPool, future=True)
        Session = sessionmaker(bind=engine, future=True)
        with Session() as s:
            yield s

# ---------- Helpers ----------
def ensure_vehicles_table(session):
    md = MetaData()
    engine = session.get_bind()
    md.reflect(engine, only=["vehicles"])
    return md.tables["vehicles"]

def insert_vehicle(session, table, row):
    cols = ", ".join(row.keys())
    vals = ", ".join(f":{k}" for k in row.keys())
    stmt = text(f"INSERT INTO {table.name} ({cols}) VALUES ({vals})")
    session.execute(stmt, row)

import random

def generate_vehicle_data(country_id):
    """Generate 100 vehicles with random reg codes between ZR90 and ZR502 (inclusive)."""
    vehicles = []
    used = set()

    while len(vehicles) < 100:
        num = random.randint(90, 502)
        if num in used:
            continue
        used.add(num)

        reg_code = f"ZR{num}"
        vehicles.append({
            "country_id": country_id,
            "reg_code": reg_code,
            "status": "available",
            "notes": f"Seeded vehicle {len(vehicles)+1}"
        })
    return vehicles


# ---------- Main ----------
def seed_vehicles(interactive=True):
    conf = load_configuration()
    with db_session(conf) as db:
        table = ensure_vehicles_table(db)

        # get first country_id
        country_id = db.execute(text("SELECT country_id FROM countries LIMIT 1")).scalar_one()
        data = generate_vehicle_data(country_id)

        inserted = 0
        for row in data:
            try:
                insert_vehicle(db, table, row)
                db.commit()
                inserted += 1
                if interactive:
                    print(Fore.GREEN + f"[OK] Inserted {row['reg_code']}")
            except Exception as e:
                db.rollback()
                print(Fore.RED + f"[X] {e}")

        print(Style.BRIGHT + f"Inserted {inserted} vehicles.")

def main():
    p = argparse.ArgumentParser()
    args = p.parse_args()
    seed_vehicles(interactive=True)

if __name__ == "__main__":
    main()
