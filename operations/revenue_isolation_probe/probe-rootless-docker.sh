#!/bin/bash
set -eu -o pipefail
umask 077
evidence="$(cd "$(dirname "$0")" && pwd)"
probe="$(mktemp -d /tmp/daivora-inert-probe.XXXXXX)"
source "$evidence/capsule-supervision.sh"
image=
container="daivora-inert-$(basename "$probe" | cut -d. -f2 | tr '[:upper:]' '[:lower:]')"
cleanup() {
  docker_local rm -f "$container" >/dev/null 2>&1 || true
  if test -n "$image"; then docker_local image rm "$image" >/dev/null; fi
  rm -rf -- "$probe"
}
trap cleanup EXIT
entry=(/probe "$probe/host-only-canary")
case "${2:-}" in
  test-aggregate-controls)
    require_aggregate_daemon
    entry=(/require-aggregate-cgroup "${entry[@]}" test-timeout-cleanup);;
  test-timeout-cleanup) entry+=(test-timeout-cleanup);;
  test-process-limits) entry+=(test-process-limits);;
  test-inherited-limits)
    entry=(/usr/bin/prlimit --as=6442450944:6442450944 --nproc=32:32 --cpu=240:240
           -- /probe "$probe/host-only-canary" test-inherited-limits);;
  "") ;;
  *) printf '%s\n' 'Unknown inert probe scope'; exit 2;;
esac
options=$(docker_local info --format '{{json .SecurityOptions}}')
case "$options" in *rootless*) ;; *) printf '%s\n' 'Managed daemon lacks rootless mode'; exit 1;; esac
docker_local info --format 'Docker {{.ServerVersion}} · default {{.DefaultRuntime}} · cgroup {{.CgroupVersion}} · {{json .SecurityOptions}}'
mkdir "$probe/rootfs"
gcc -std=c11 -O2 -Wall -Wextra -Werror -static "$evidence/inert-container-probe.c" -o "$probe/rootfs/probe"
chmod 755 "$probe/rootfs/probe"
if [[ ${2:-} == test-aggregate-controls ]]; then
  gcc -std=c11 -O2 -Wall -Wextra -Werror -static "$evidence/require-aggregate-cgroup.c" \
    -o "$probe/rootfs/require-aggregate-cgroup"
fi
if test "${2:-}" = test-inherited-limits; then
  for host_file in /usr/bin/prlimit /lib/x86_64-linux-gnu/libsmartcols.so.1 \
      /lib/x86_64-linux-gnu/libc.so.6 /lib64/ld-linux-x86-64.so.2; do
    target="$probe/rootfs$host_file"
    mkdir -p "$(dirname "$target")"
    cp -L "$host_file" "$target"
    chmod 755 "$target"
    sha256sum "$host_file"
  done
fi
find "$probe/rootfs" -type d -exec chmod 755 {} +
printf A > "$probe/input"
printf outside > "$probe/host-only-canary"
chmod 444 "$probe/input"
image=$(tar -C "$probe/rootfs" -cf - . | docker_local import -)
printf 'Local inert image %s\n' "$image"
capsule_id=$(docker_local create --cgroupns=private --name "$container" --runtime "${1:-runc}" --pull=never \
  --read-only --network=none --log-driver=none --ipc=none --no-healthcheck --cap-drop=ALL --security-opt=no-new-privileges \
  --pids-limit=32 --memory=6g --memory-swap=6g --cpus=2 --user=65534:65534 \
  --ulimit fsize=65536:65536 --ulimit nofile=64:64 --ulimit core=0:0 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=67108864,mode=1777 \
  --mount "type=bind,src=$probe/input,dst=/input,readonly" \
  --env HTTP_PROXY= --env HTTPS_PROXY= --env ALL_PROXY= --env NO_PROXY= \
  --env http_proxy= --env https_proxy= --env all_proxy= --env no_proxy= \
  "$image" "${entry[@]}")
docker_local inspect -f 'daemon configuration runtime={{.HostConfig.Runtime}} network={{.HostConfig.NetworkMode}} rootfs_readonly={{.HostConfig.ReadonlyRootfs}} memory={{.HostConfig.Memory}} pids={{.HostConfig.PidsLimit}} nano_cpus={{.HostConfig.NanoCpus}} caps_dropped={{.HostConfig.CapDrop}} security={{.HostConfig.SecurityOpt}}' "$container"
if [[ ${2:-} == test-aggregate-controls ]]; then
  attach_with_deadline "$capsule_id" 10 > "$probe/stdout" 2> "$probe/stderr" &
  attach_pid=$!
  for ((attempt=0; attempt<50; attempt++)); do
    grep -q '^PASS inert process tree ready' "$probe/stdout" && break
    kill -0 "$attach_pid" 2>/dev/null || break
    sleep 0.1
  done
  cat "$probe/stderr"
  grep -q '^Aggregate pilot controls read back before workload$' "$probe/stderr"
  grep -q '^PASS inert process tree ready' "$probe/stdout"
  host_pid=$(docker_local inspect -f '{{.State.Pid}}' "$capsule_id")
  [[ "$host_pid" =~ ^[1-9][0-9]*$ ]]
  cgroup_path=$(sed -n 's/^0:://p' "/proc/$host_pid/cgroup")
  [[ "$cgroup_path" == /* && "$cgroup_path" != / && "$cgroup_path" != *..* ]]
  cgroup="/sys/fs/cgroup$cgroup_path"
  test "$(cat "$cgroup/cpu.max")" = '200000 100000'
  test "$(cat "$cgroup/memory.max")" = 6442450944
  test "$(cat "$cgroup/memory.swap.max")" = 0
  test "$(cat "$cgroup/pids.max")" = 32
  printf 'PASS host kernel aggregate controls for %s\n' "$capsule_id"
  remove_capsule "$capsule_id"
  wait "$attach_pid" || true
  exit
fi
if [[ ${2:-} == test-timeout-cleanup ]]; then
  attach_status=0
  attach_with_deadline "$capsule_id" 3 > "$probe/stdout" 2> "$probe/stderr" || attach_status=$?
  remove_capsule "$capsule_id"
  cat "$probe/stdout"
  grep -q '^PASS inert process tree ready' "$probe/stdout"
  test "$attach_status" = 137
  printf 'PASS attach exceeded 3 s, status %s, forced capsule removal verified for %s\n' "$attach_status" "$capsule_id"
  exit
fi
timeout 20s env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH \
    docker --host=unix:///var/run/docker.sock start -a "$container"
test "$(docker_local inspect -f '{{.State.ExitCode}}' "$container")" = 0
