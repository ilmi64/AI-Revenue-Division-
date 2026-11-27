# Source from the approved one-shot launcher or the inert probe.
docker_local() {
  timeout --kill-after=1s 10s env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH \
    docker --host=unix:///var/run/docker.sock "$@"
}

require_aggregate_daemon() {
  local observed
  observed=$(docker_local info --format '{{.CgroupDriver}} {{.CgroupVersion}} {{.MemoryLimit}} {{.PidsLimit}} {{.CPUCfsQuota}} {{.SwapLimit}} {{json .SecurityOptions}}') || return 1
  case "$observed" in
    'systemd 2 true true true true '*name=rootless*) return 0;;
  esac
  printf 'Aggregate capsule capability unavailable: %s\n' "$observed" >&2
  return 125
}

attach_with_deadline() {
  local id=$1 deadline=$2
  timeout --signal=KILL "${deadline}s" prlimit --fsize=65536:65536 -- \
    env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH \
    docker --host=unix:///var/run/docker.sock start -a "$id"
}

remove_capsule() {
  local id=$1 remaining
  [[ "$id" =~ ^[0-9a-f]{64}$ ]] || return 1
  timeout --kill-after=1s 5s env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS \
    -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH docker --host=unix:///var/run/docker.sock rm -f "$id" >/dev/null || return 1
  remaining=$(timeout --kill-after=1s 5s env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS \
    -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH docker --host=unix:///var/run/docker.sock \
    ps -aq --no-trunc --filter "id=$id") || return 1
  test -z "$remaining"
}
