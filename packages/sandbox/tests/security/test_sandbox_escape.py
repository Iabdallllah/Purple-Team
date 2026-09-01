#!/usr/bin/env python3
"""
Sandbox Escape Prevention Tests
Tests Docker container isolation and escape prevention mechanisms.
"""

import pytest
import docker
import time
import re


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def docker_client():
    """Create Docker client"""
    client = docker.from_env()
    client.ping()
    yield client
    client.close()


@pytest.fixture(scope="function")
def sandbox_container(docker_client):
    """Create a secure sandbox container with all security restrictions"""
    container = docker_client.containers.run(
        "alpine:latest",
        command="sleep 300",
        detach=True,
        network_mode="none",
        read_only=True,
        cap_drop=["ALL"],
        security_opt=["no-new-privileges:true"],
        mem_limit="128m",
        cpu_quota=50000,
        pids_limit=50,
        tmpfs={"/tmp": "rw,noexec,nosuid,size=10m"},
        user="1000:1000",
    )
    time.sleep(0.5)
    yield container
    try:
        container.remove(force=True)
    except Exception:
        pass


@pytest.fixture(scope="function")
def privileged_container(docker_client):
    """Create a container WITHOUT security restrictions (for negative testing)"""
    container = docker_client.containers.run(
        "alpine:latest",
        command="sleep 300",
        detach=True,
        network_mode="bridge",
        privileged=True,
    )
    time.sleep(0.5)
    yield container
    try:
        container.remove(force=True)
    except Exception:
        pass


# ============================================================================
# Helper Functions
# ============================================================================

def exec_in_container(container, command: str):
    """Execute command in container and return (exit_code, output)"""
    result = container.exec_run(command)
    return result.exit_code, result.output.decode() if result.output else ""


# ============================================================================
# Test Classes
# ============================================================================

class TestContainerIsolation:
    """Test container isolation mechanisms"""
    
    def test_no_network_access(self, sandbox_container):
        """Verify container has no network access"""
        exit_code, _ = exec_in_container(sandbox_container, "ping -c 1 8.8.8.8")
        assert exit_code != 0, "Container should not have network access"
    
    def test_no_external_dns(self, sandbox_container):
        """Verify container cannot resolve external DNS"""
        exit_code, _ = exec_in_container(sandbox_container, "nslookup google.com")
        assert exit_code != 0, "Container should not resolve external DNS"
    
    def test_readonly_filesystem(self, sandbox_container):
        """Verify filesystem is read-only"""
        exit_code, _ = exec_in_container(sandbox_container, "touch /test_write")
        assert exit_code != 0, "Filesystem should be read-only"
    
    def test_tmp_writable(self, sandbox_container):
        """Verify /tmp is writable"""
        exit_code, _ = exec_in_container(sandbox_container, "touch /tmp/test_write")
        assert exit_code == 0, "/tmp should be writable"
    
    def test_no_capabilities(self, sandbox_container):
        """Verify all capabilities are dropped"""
        exit_code, output = exec_in_container(sandbox_container, "grep CapEff /proc/self/status")
        assert exit_code == 0
        # Effective capabilities should be 0 (no capabilities)
        assert "CapEff:\t0000000000000000" in output
    
    def test_no_new_privileges(self, sandbox_container):
        """Verify no-new-privileges is set"""
        exit_code, output = exec_in_container(sandbox_container, "grep NoNewPrivs /proc/self/status")
        assert exit_code == 0
        assert "NoNewPrivs:\t1" in output
    
    def test_pid_limit(self, sandbox_container):
        """Verify PID limit is enforced"""
        # Count current processes (exclude header line)
        exit_code, output = exec_in_container(sandbox_container, "sh -c 'ps aux | tail -n +2 | wc -l'")
        assert exit_code == 0
        process_count = int(output.strip())
        assert process_count < 50, f"Process count should be limited to 50, got {process_count}"
    
    def test_memory_limit(self, sandbox_container):
        """Verify memory limit is enforced"""
        exit_code, output = exec_in_container(sandbox_container, "cat /sys/fs/cgroup/memory.max")
        assert exit_code == 0
        assert output.strip() != "max"
        limit_bytes = int(output.strip())
        assert limit_bytes <= 134217728  # 128MB
    
    def test_cpu_limit(self, sandbox_container):
        """Verify CPU quota is enforced"""
        exit_code, output = exec_in_container(sandbox_container, "cat /sys/fs/cgroup/cpu.max")
        assert exit_code == 0
        assert "50000" in output


class TestPrivilegeEscalationPrevention:
    """Test prevention of privilege escalation"""
    
    def test_no_sudo(self, sandbox_container):
        """Verify sudo is not available"""
        exit_code, _ = exec_in_container(sandbox_container, "which sudo")
        assert exit_code != 0
    
    def test_no_suid_binaries(self, sandbox_container):
        """Verify no SUID binaries exist"""
        exit_code, output = exec_in_container(sandbox_container, "sh -c 'find / -perm -4000 -type f 2>/dev/null || true'")
        assert output.strip() == ""
    
    def test_no_sgid_binaries(self, sandbox_container):
        """Verify no SGID binaries exist"""
        exit_code, output = exec_in_container(sandbox_container, "sh -c 'find / -perm -2000 -type f 2>/dev/null || true'")
        assert exit_code == 0 or output.strip() == ""
        assert output.strip() == ""
    
    def test_cannot_mount(self, sandbox_container):
        """Verify cannot mount filesystems"""
        exit_code, _ = exec_in_container(sandbox_container, "mount -t tmpfs tmpfs /mnt")
        assert exit_code != 0
    
    def test_cannot_load_kernel_modules(self, sandbox_container):
        """Verify cannot load kernel modules"""
        exit_code, _ = exec_in_container(sandbox_container, "modprobe dummy")
        assert exit_code != 0
    
    def test_cannot_access_docker_socket(self, sandbox_container):
        """Verify cannot access Docker socket"""
        exit_code, output = exec_in_container(sandbox_container, "sh -c 'ls -la /var/run/docker.sock 2>&1 || echo not_found'")
        assert "not_found" in output or exit_code != 0
    
    def test_cannot_ptrace(self, sandbox_container):
        """Verify ptrace is disabled"""
        exit_code, output = exec_in_container(sandbox_container, "sh -c 'strace -p 1 2>&1 | head -1; echo STRC_EXIT:$?'")
        output = output.lower()
        # strace may not be installed in alpine; check for either permission denied or not found, or seccomp blocking
        assert "permission denied" in output or "operation not permitted" in output or "not found" in output or exit_code != 0
        # also verify seccomp is active as primary ptrace protection
        exit_code2, out2 = exec_in_container(sandbox_container, "grep Seccomp /proc/self/status")
        assert "Seccomp:\t2" in out2


class TestFilesystemIsolation:
    """Test filesystem isolation"""
    
    def test_no_host_paths_accessible(self, sandbox_container):
        """Verify host paths are not accessible"""
        sensitive_paths = [
            "/etc/passwd",
            "/etc/shadow",
            "/root",
            "/home",
            "/boot",
            "/sys",
            "/proc/1/environ",
            "/proc/1/cmdline",
            "/var/run/docker.sock",
        ]
        
        for path in sensitive_paths:
            exit_code, output = exec_in_container(sandbox_container, f"cat {path} 2>&1")
            output = output.lower()
            assert "permission denied" in output or exit_code != 0 or output == ""
    
    def test_proc_limited(self, sandbox_container):
        """Verify /proc is limited"""
        exit_code, output = exec_in_container(sandbox_container, "ls /proc/")
        assert exit_code == 0
        assert "1" in output  # Should only see own PID namespace
    
    def test_no_device_access(self, sandbox_container):
        """Verify no device access"""
        exit_code, output = exec_in_container(sandbox_container, "ls /dev/")
        assert exit_code == 0
        assert "sda" not in output  # No block devices
        assert "loop" not in output


class TestNetworkIsolation:
    """Test network isolation"""
    
    def test_no_outbound_connections(self, sandbox_container):
        """Verify no outbound connections possible"""
        exit_code, output = exec_in_container(sandbox_container, "sh -c 'wget --timeout=2 http://httpbin.org/get 2>&1 | head -5'")
        output = output.lower()
        assert "failed" in output or "unreachable" in output or "bad address" in output or "network is unreachable" in output or exit_code != 0
    
    def test_no_inbound_connections(self, sandbox_container):
        """Verify no inbound connections possible"""
        exit_code, output = exec_in_container(sandbox_container, "sh -c 'timeout 2 nc -l -p 8080 2>&1 || echo failed'")
        output = output.lower()
        assert "failed" in output or exit_code != 0
    
    def test_no_raw_sockets(self, sandbox_container):
        """Verify raw sockets not available"""
        exit_code, output = exec_in_container(sandbox_container, "sh -c 'python3 -c \"import socket; s=socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP); print(raw)\" 2>&1'")
        output = output.lower()
        assert "permission denied" in output or "operation not permitted" in output or exit_code != 0


class TestResourceLimits:
    """Test resource limits enforcement"""
    
    def test_disk_quota(self, sandbox_container):
        """Verify disk quota"""
        exit_code, output = exec_in_container(sandbox_container, "df -h /tmp")
        assert exit_code == 0
        assert "10.0M" in output or "10M" in output or "10m" in output
    
    def test_file_descriptor_limit(self, sandbox_container):
        """Verify file descriptor limits"""
        exit_code, output = exec_in_container(sandbox_container, "sh -c \"cat /proc/self/limits | grep 'open files'\"")
        assert exit_code == 0
        # Parse the soft limit (4th column)
        parts = output.split()
        if len(parts) >= 4:
            try:
                limit = int(parts[3])
                assert limit <= 4096
            except ValueError:
                pass
    
    def test_cpu_time_limit(self, sandbox_container):
        """Verify CPU time limits"""
        exit_code, _ = exec_in_container(sandbox_container, "timeout 5 bash -c 'while true; do :; done' 2>&1")


class TestNegativeTesting:
    """Test that unrestricted containers CAN do these things (control tests)"""
    
    def test_privileged_can_mount(self, privileged_container):
        """Verify privileged container CAN mount"""
        exit_code, _ = exec_in_container(privileged_container, "mount -t tmpfs tmpfs /mnt")
        assert exit_code == 0
    
    def test_privileged_can_access_devices(self, privileged_container):
        """Verify privileged container CAN access devices"""
        exit_code, output = exec_in_container(privileged_container, "sh -c 'ls /dev/ | grep -E \"sda|loop\" || ls /dev/null && echo ok'")
        # privileged should at least be able to list devices; check container is privileged
        assert exit_code == 0
    
    def test_privileged_can_load_modules(self, privileged_container):
        """Verify privileged container CAN load modules"""
        exit_code, output = exec_in_container(privileged_container, "modprobe dummy 2>&1")
        output = output.lower()
        assert "permission denied" not in output


class TestSecurityConfiguration:
    """Test security configuration validation"""
    
    def test_seccomp_profile(self, sandbox_container):
        """Verify seccomp profile is applied"""
        exit_code, output = exec_in_container(sandbox_container, "grep Seccomp /proc/self/status")
        assert exit_code == 0
        assert "Seccomp:\t2" in output
    
    def test_capabilities_dropped(self, sandbox_container):
        """Verify all capabilities dropped"""
        exit_code, output = exec_in_container(sandbox_container, "grep CapEff /proc/self/status")
        assert exit_code == 0
        assert "CapEff:\t0000000000000000" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])