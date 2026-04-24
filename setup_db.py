import subprocess
import sys
import os

env = os.environ.copy()
env["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))

subprocess.run([sys.executable, "app/create_db.py"], check=True, env=env)
subprocess.run([sys.executable, "fetch_all_gmb_locations.py"], check=True, env=env)
subprocess.run([sys.executable, "push_to_db.py"], check=True, env=env)
subprocess.run([sys.executable, "update_gmb_urls_in_db.py"], check=True, env=env)
