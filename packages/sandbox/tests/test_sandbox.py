import pytest
from unittest.mock import Mock, patch, MagicMock
from sandbox.docker_client import DockerClient
from sandbox.container_pool import ContainerPool
from sandbox.snapshot import SnapshotManager
from sandbox.network import NetworkManager
from sandbox.targets.juice_shop import JuiceShopTarget
from sandbox.targets.dvwa import DVWATarget
from sandbox.targets.custom import CustomTarget
from sandbox.schemas import SandboxConfig, TargetConfig


class TestJuiceShopTarget:
    def test_target_type(self):
        target = JuiceShopTarget(TargetConfig(docker_image="test"))
        assert target.target_type == "juice_shop"
        assert target.display_name == "OWASP Juice Shop"

    def test_default_config(self):
        target = JuiceShopTarget(TargetConfig(docker_image="test"))
        config = target.get_default_config()
        assert config.docker_image == "bkimminich/juice-shop"
        assert config.docker_tag == "latest"
        assert "3000" in config.exposed_ports

    def test_supported_scenarios(self):
        target = JuiceShopTarget(TargetConfig(docker_image="test"))
        scenarios = target.get_supported_scenarios()
        assert "idor" in scenarios
        assert "injection" in scenarios
        assert "ssrf" in scenarios


class TestDVWATarget:
    def test_target_type(self):
        target = DVWATarget(TargetConfig(docker_image="test"))
        assert target.target_type == "dvwa"
        assert target.display_name == "DVWA (Damn Vulnerable Web App)"

    def test_default_config(self):
        target = DVWATarget(TargetConfig(docker_image="test"))
        config = target.get_default_config()
        assert config.docker_image == "vulnerables/web-dvwa"
        assert "80" in config.exposed_ports


class TestCustomTarget:
    def test_target_type(self):
        target = CustomTarget(TargetConfig(docker_image="custom/app"))
        assert target.target_type == "custom"
        assert target.display_name == "Custom Target Application"

    def test_validation(self):
        target = CustomTarget(TargetConfig(docker_image="custom/app"))
        assert target.validate_config(target.config) is True

        invalid_target = CustomTarget(TargetConfig(docker_image=""))
        assert invalid_target.validate_config(invalid_target.config) is False


class TestSandboxConfig:
    def test_default_values(self):
        config = SandboxConfig()
        assert config.max_containers == 10
        assert config.default_cpu_limit == "2"
        assert config.default_memory_limit == "4g"
        assert config.network == "purple-network"


class TestDockerClient:
    @patch("sandbox.docker_client.docker.DockerClient")
    def test_init_success(self, mock_docker):
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_docker.return_value = mock_client

        client = DockerClient()
        assert client.client == mock_client
        mock_client.ping.assert_called_once()

    @patch("sandbox.docker_client.docker.DockerClient")
    def test_init_failure(self, mock_docker):
        mock_client = Mock()
        mock_client.ping.side_effect = Exception("Connection refused")
        mock_docker.return_value = mock_client

        with pytest.raises(Exception):
            DockerClient()


class TestContainerPool:
    @pytest.fixture
    def mock_docker_client(self):
        client = Mock(spec=DockerClient)
        client.get_container_status.return_value = Mock(status="running")
        return client

    @pytest.mark.asyncio
    async def test_acquire_from_empty_pool(self, mock_docker_client):
        pool = ContainerPool(mock_docker_client, max_containers=5)
        mock_docker_client.create_container.return_value = Mock(id="test123")
        mock_docker_client.start_container.return_value = True

        result = await pool.acquire("juice_shop", SandboxConfig())
        assert result == "test123"
        mock_docker_client.create_container.assert_called_once()


class TestSnapshotManager:
    @pytest.fixture
    def mock_docker_client(self):
        return Mock(spec=DockerClient)

    def test_create_snapshot(self, mock_docker_client):
        manager = SnapshotManager(mock_docker_client)
        mock_docker_client.commit_container.return_value = "sha256:abc123"

        result = manager.create_snapshot("container123", "test-repo", "v1")
        assert result is not None
        assert result.repository == "test-repo"
        assert result.tag == "v1"
        mock_docker_client.commit_container.assert_called_once_with("container123", "test-repo", "v1")


class TestNetworkManager:
    @pytest.fixture
    def mock_docker_client(self):
        return Mock(spec=DockerClient)

    def test_create_isolated_network(self, mock_docker_client):
        manager = NetworkManager(mock_docker_client)
        mock_network = Mock()
        mock_network.id = "net123"
        mock_docker_client.client.networks.create.return_value = mock_network

        result = manager.create_isolated_network("test-network")
        assert result == "net123"
        mock_docker_client.client.networks.create.assert_called_once()