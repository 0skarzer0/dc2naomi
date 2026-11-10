#!/usr/bin/env python3
"""piput.py LOCAL REMOTE: copies a file to the netbooter Raspberry (SFTP). Environment: PIHOST, PIPASS."""
import os, sys, paramiko
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ["PIHOST"], username="root", password=os.environ["PIPASS"], timeout=8, look_for_keys=False, allow_agent=False)
s = c.open_sftp(); s.put(sys.argv[1], sys.argv[2]); print("put", sys.argv[2], s.stat(sys.argv[2]).st_size)
