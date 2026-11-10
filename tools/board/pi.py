#!/usr/bin/env python3
"""pi.py 'COMMAND': runs a shell command on the netbooter Raspberry over SSH (paramiko) and prints its output.
Environment: PIHOST (the Raspberry's address), PIPASS (root's password; never write it in a file).
Keep commands short (60 s): start long jobs with nohup ... & and look at their log with another call."""
import os, sys, paramiko
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ["PIHOST"], username="root", password=os.environ["PIPASS"], timeout=8, look_for_keys=False, allow_agent=False)
_, o, e = c.exec_command(sys.argv[1], timeout=60)
sys.stdout.write(o.read().decode(errors="replace")); sys.stdout.write(e.read().decode(errors="replace"))
