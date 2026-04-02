#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEST_TMP_DIR="$(mktemp -d)"
FAILURES=0

cleanup() {
    rm -rf "$TEST_TMP_DIR"
}
trap cleanup EXIT

# 构造隔离的 skill 副本，避免仓库内现有配置干扰回归测试。
prepare_isolated_skill_copy() {
    local target_dir="$1"

    cp -R "$ROOT_DIR" "$target_dir"
    rm -f "$target_dir/.config"
}

# 生成一份最小可用配置，供脚本 source 与字段校验使用。
create_valid_config() {
    local config_file="$1"

    mkdir -p "$(dirname "$config_file")"
    cat >"$config_file" <<'EOF'
ZENTAO_URL=http://127.0.0.1:9191/zentao
ZENTAO_ACCOUNT=tester
ZENTAO_PASSWORD=secret
GITLAB_URL=http://127.0.0.1:8080
GITLAB_TOKEN=test-token
GITLAB_PROJECT_ID=123
TARGET_BRANCH=develop
PROJECT_OWNER=test-owner
EOF
}

# 统一在指定目录执行命令，模拟用户在项目仓库内调用 skill 的场景。
run_in_dir() {
    local workdir="$1"
    shift

    (
        cd "$workdir"
        "$@"
    )
}

# 支持带环境变量的目录内执行，用于校验相对路径覆盖逻辑。
run_in_dir_env() {
    local workdir="$1"
    shift

    (
        cd "$workdir"
        env "$@"
    )
}

run_capture() {
    local output_file="$1"
    shift
    local status

    set +e
    "$@" >"$output_file" 2>&1
    status=$?
    set -e

    printf '%s' "$status"
}

record_failure() {
    local message="$1"
    echo "FAIL: $message" >&2
    FAILURES=$((FAILURES + 1))
}

assert_exit_code() {
    local actual="$1"
    local expected="$2"
    local message="$3"

    if [[ "$actual" -ne "$expected" ]]; then
        record_failure "$message (expected=$expected actual=$actual)"
    fi
}

assert_contains() {
    local file="$1"
    local expected="$2"
    local message="$3"

    if ! grep -Fq "$expected" "$file"; then
        record_failure "$message"
        echo "--- output ---" >&2
        cat "$file" >&2
        echo "--------------" >&2
    fi
}

test_project_default_config() {
    local skill_copy="${TEST_TMP_DIR}/skill-default"
    local project_dir="${TEST_TMP_DIR}/project-default"
    local output_file="${TEST_TMP_DIR}/project-default.out"
    local status

    prepare_isolated_skill_copy "$skill_copy"
    mkdir -p "$project_dir"
    create_valid_config "${project_dir}/zc-bug-fix.config"

    status="$(run_capture "$output_file" run_in_dir "$project_dir" "${skill_copy}/scripts/check_config.sh")"
    assert_exit_code "$status" 0 "check_config 应优先读取项目根目录 zc-bug-fix.config"
    assert_contains "$output_file" "CONFIG_OK" "项目级配置存在时应返回 CONFIG_OK"
}

test_relative_env_override() {
    local skill_copy="${TEST_TMP_DIR}/skill-env"
    local project_dir="${TEST_TMP_DIR}/project-env"
    local output_file="${TEST_TMP_DIR}/project-env.out"
    local status

    prepare_isolated_skill_copy "$skill_copy"
    mkdir -p "${project_dir}/configs"
    create_valid_config "${project_dir}/configs/custom.config"

    status="$(run_capture "$output_file" run_in_dir_env "$project_dir" ZC_BUG_FIX_CONFIG=configs/custom.config "${skill_copy}/scripts/check_config.sh")"
    assert_exit_code "$status" 0 "ZC_BUG_FIX_CONFIG 的相对路径应按项目目录解析"
    assert_contains "$output_file" "CONFIG_OK" "相对路径覆盖成功后应返回 CONFIG_OK"
}

test_non_target_config_is_ignored() {
    local skill_copy="${TEST_TMP_DIR}/skill-non-target"
    local project_dir="${TEST_TMP_DIR}/project-non-target"
    local output_file="${TEST_TMP_DIR}/project-non-target.out"
    local status

    prepare_isolated_skill_copy "$skill_copy"
    mkdir -p "$project_dir"
    create_valid_config "${skill_copy}/.config"

    status="$(run_capture "$output_file" run_in_dir "$project_dir" "${skill_copy}/scripts/check_config.sh")"
    assert_exit_code "$status" 1 "非目标配置文件存在时不应被读取"
    assert_contains "$output_file" "${project_dir}/zc-bug-fix.config" "非目标配置文件存在时仍应提示项目级配置路径"
}

test_missing_config_hint() {
    local skill_copy="${TEST_TMP_DIR}/skill-missing"
    local project_dir="${TEST_TMP_DIR}/project-missing"
    local output_file="${TEST_TMP_DIR}/project-missing.out"
    local status

    prepare_isolated_skill_copy "$skill_copy"
    mkdir -p "$project_dir"

    status="$(run_capture "$output_file" run_in_dir "$project_dir" "${skill_copy}/scripts/check_config.sh")"
    assert_exit_code "$status" 1 "缺少配置时 check_config 应返回非零"
    assert_contains "$output_file" "${project_dir}/zc-bug-fix.config" "缺少配置时应提示项目级配置路径"
    assert_contains "$output_file" "zc-bug-fix.config.example" "缺少配置时应提示新的示例文件名"
}

test_config_hint_command() {
    local skill_copy="${TEST_TMP_DIR}/skill-hint"
    local project_dir="${TEST_TMP_DIR}/project-hint"
    local output_file="${TEST_TMP_DIR}/project-hint.out"
    local status

    prepare_isolated_skill_copy "$skill_copy"
    mkdir -p "$project_dir"

    status="$(run_capture "$output_file" run_in_dir "$project_dir" "${skill_copy}/scripts/bugfix_flow.sh" config-hint)"
    assert_exit_code "$status" 0 "config-hint 应可直接输出项目级配置提示"
    assert_contains "$output_file" "${project_dir}/zc-bug-fix.config" "config-hint 应指向项目级配置文件"
    assert_contains "$output_file" "zc-bug-fix.config.example" "config-hint 应指向新的示例文件"
}

test_downstream_scripts_use_project_config() {
    local skill_copy="${TEST_TMP_DIR}/skill-downstream"
    local project_dir="${TEST_TMP_DIR}/project-downstream"
    local gitlab_output="${TEST_TMP_DIR}/gitlab-help.out"
    local zentao_output="${TEST_TMP_DIR}/zentao-help.out"
    local gitlab_status
    local zentao_status

    prepare_isolated_skill_copy "$skill_copy"
    mkdir -p "$project_dir"
    create_valid_config "${project_dir}/zc-bug-fix.config"

    gitlab_status="$(run_capture "$gitlab_output" run_in_dir "$project_dir" "${skill_copy}/scripts/gitlab.sh" help)"
    zentao_status="$(run_capture "$zentao_output" run_in_dir "$project_dir" "${skill_copy}/scripts/zentao.sh" help)"

    assert_exit_code "$gitlab_status" 0 "gitlab.sh 应可读取项目级配置"
    assert_contains "$gitlab_output" "GitLab API脚本" "gitlab.sh help 应正常输出 usage"
    assert_exit_code "$zentao_status" 0 "zentao.sh 应可读取项目级配置"
    assert_contains "$zentao_output" "禅道脚本" "zentao.sh help 应正常输出 usage"
}

test_project_default_config
test_relative_env_override
test_non_target_config_is_ignored
test_missing_config_hint
test_config_hint_command
test_downstream_scripts_use_project_config

if [[ "$FAILURES" -ne 0 ]]; then
    echo "config_resolution_test: ${FAILURES} 个用例失败" >&2
    exit 1
fi

echo "config_resolution_test: all tests passed"
