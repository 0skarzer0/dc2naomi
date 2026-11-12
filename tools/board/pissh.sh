#!/bin/bash
# pissh.sh 'COMMAND' : runs a command on a netbooter Raspberry with plain ssh (no paramiko needed: e.g. the Linux
# shell of the Claude desktop app on the user's PC). Environment: PIHOST (the Raspberry), PIPASS (root's password,
# given by the user in the chat: never write it in a file). The password reaches ssh through SSH_ASKPASS.
set -e
ASK=$(mktemp); printf '#!/bin/sh\necho "$PIPASS"\n' > "$ASK"; chmod 700 "$ASK"
trap 'rm -f "$ASK"' EXIT
SSH_ASKPASS="$ASK" SSH_ASKPASS_REQUIRE=force DISPLAY=:0 setsid -w ssh -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile="$HOME/.dc2naomi_known_hosts" -o ConnectTimeout=8 -o ServerAliveInterval=10 \
  -o PubkeyAuthentication=no ${PISSH_OPTS} root@"$PIHOST" "$@"
