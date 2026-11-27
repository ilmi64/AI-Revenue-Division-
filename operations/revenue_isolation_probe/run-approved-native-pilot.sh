#!/bin/bash
set -eu -o pipefail
umask 077
here="$(cd "$(dirname "$0")" && pwd)"
source "$here/capsule-supervision.sh"

if [[ $# == 1 && $1 == --preflight ]]; then
  require_aggregate_daemon
  exit
fi
if [[ $# != 3 || ! $1 =~ ^sha256:[a-f0-9]{64}$ ]]; then
  printf '%s\n' 'Usage: run-approved-native-pilot.sh VERIFIED_IMAGE_ID STAGE PRIVATE_EVIDENCE_PARENT' >&2
  exit 2
fi
require_aggregate_daemon
image=$1
[[ $(docker_local image inspect -f '{{json .Config.Volumes}}' "$image") == null ]] || exit 125
stage=$(realpath -e -- "$2")
private_parent=$(realpath -e -- "$3")
if [[ $(stat -c '%u:%a' "$private_parent") != "$(id -u):700" || ! -d $private_parent ]]; then
  printf '%s\n' 'Evidence parent must be an owner-private directory' >&2
  exit 2
fi
model=$stage/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf
prompt=$here/../fixtures/native-pilot-prompt.txt
for file in "$model" "$prompt"; do
  if [[ "$file" == *','* || "$file" == *$'\n'* || ! -f "$file" || -L "$file" ]]; then
    exit 2
  fi
done
prompt=$(realpath -e -- "$prompt")
python "$here/../check_revenue_native_artifacts.py" "$stage" --cpu-model-smoke
printf '%s  %s\n' 05e35b5b43dbda72f293b70b796878d169f3e5f64187d7f59eb72d56ac471e42 "$prompt" | sha256sum -c -
evidence=$(mktemp -d "$private_parent/one-shot.XXXXXX")
id=
cleanup() {
  local status=$?
  trap - EXIT
  if [[ -n $id ]]; then
    if remove_capsule "$id"; then
      printf '%s\n' 'capsule_removed=true' >> "$evidence/receipt.txt"
    else
      printf '%s\n' 'capsule_removed=unconfirmed' >> "$evidence/receipt.txt"
      printf 'Cleanup unconfirmed. Freeze further execution and remove container %s\n' "$id" >&2
      exit 125
    fi
  fi
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' HUP TERM
id=$(docker_local create --runtime runsc --pull=never --cgroupns=private --restart=no \
  --read-only --network=none --log-driver=none --ipc=none --no-healthcheck --cap-drop=ALL --security-opt=no-new-privileges \
  --cpus=2 --memory=6g --memory-swap=6g --pids-limit=32 --user=65534:65534 \
  --ulimit fsize=65536:65536 --ulimit nofile=64:64 --ulimit core=0:0 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=67108864,mode=1777 --workdir=/tmp \
  --mount "type=bind,src=$model,dst=/pilot/model.gguf,readonly" \
  --mount "type=bind,src=$prompt,dst=/pilot/prompt.txt,readonly" \
  --env HOME=/tmp --env LD_LIBRARY_PATH=/pilot/runtime \
  --env HTTP_PROXY= --env HTTPS_PROXY= --env ALL_PROXY= --env NO_PROXY= \
  --env http_proxy= --env https_proxy= --env all_proxy= --env no_proxy= \
  --entrypoint /pilot/require-aggregate-cgroup "$image" \
  /usr/bin/timeout --signal=KILL 115s /usr/bin/prlimit \
  --as=6442450944:6442450944 --nproc=32:32 --cpu=240:240 -- \
  /pilot/runtime/llama-cli --single-turn --simple-io --no-display-prompt \
  -m /pilot/model.gguf -f /pilot/prompt.txt -ngl 0 -t 2 -c 2048 -n 256 --seed 42)
[[ "$id" =~ ^[0-9a-f]{64}$ ]] || exit 125
printf 'image=%s\ncontainer=%s\n' "$image" "$id" > "$evidence/receipt.txt"
printf 'Private pilot evidence: %s\n' "$evidence"
SECONDS=0
status=0
attach_with_deadline "$id" 120 > "$evidence/output.txt" 2> "$evidence/runner.log" || status=$?
printf 'attach_status=%s\nelapsed_seconds=%s\n' "$status" "$SECONDS" >> "$evidence/receipt.txt"
sha256sum "$evidence/output.txt" "$evidence/runner.log" >> "$evidence/receipt.txt"
[[ $status == 0 ]] || exit "$status"
[[ $(docker_local inspect -f '{{.State.Status}} {{.State.ExitCode}} {{.State.OOMKilled}}' "$id") == 'exited 0 false' ]] || exit 125
