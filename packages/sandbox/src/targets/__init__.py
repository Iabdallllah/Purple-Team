from sandbox.targets.base import BaseTargetApp, TargetConfig
from sandbox.targets.juice_shop import JuiceShopTarget
from sandbox.targets.dvwa import DVWATarget
from sandbox.targets.custom import CustomTarget

TARGET_REGISTRY = {
    "juice_shop": JuiceShopTarget,
    "dvwa": DVWATarget,
    "custom": CustomTarget,
}


def get_target_class(target_type: str) -> type[BaseTargetApp]:
    if target_type not in TARGET_REGISTRY:
        raise ValueError(f"Unknown target type: {target_type}")
    return TARGET_REGISTRY[target_type]


def create_target(target_type: str, config: Optional[TargetConfig] = None) -> BaseTargetApp:
    target_class = get_target_class(target_type)
    if config is None:
        config = target_class(TargetConfig(docker_image="")).get_default_config()
    return target_class(config)


def list_available_targets() -> List[str]:
    return list(TARGET_REGISTRY.keys())