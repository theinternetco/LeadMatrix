import subprocess
import sys

subprocess.run([sys.executable, "app/create_db.py"], check=True)
subprocess.run([sys.executable, "fetch_all_gmb_locations.py"], check=True)
subprocess.run([sys.executable, "push_to_db.py"], check=True)
subprocess.run([sys.executable, "update_gmb_urls_in_db.py"], check=True)
