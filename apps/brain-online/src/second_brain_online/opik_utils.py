import os

import opik
from opik.configurator.configure import OpikConfigurator

from second_brain_online.config import settings


def configure() -> None:
    if settings.COMET_API_KEY and settings.COMET_PROJECT:
        try:
            client = OpikConfigurator(api_key=settings.COMET_API_KEY)
            default_workspace = client._get_default_workspace()
        except Exception:
            print(
                "Default workspace not found. Setting workspace to None and enabling interactive mode."
            )
            default_workspace = None

        os.environ["OPIK_PROJECT_NAME"] = settings.COMET_PROJECT

        opik.configure(
            api_key=settings.COMET_API_KEY,
            workspace=default_workspace,
            use_local=False,
            force=True,
        )
        print(
            f"Opik configured successfully using workspace '{default_workspace}'"
        )
    else:
        print(
            "COMET_API_KEY and COMET_PROJECT are not set. Set them to enable prompt monitoring with Opik (powered by Comet ML)."
        )


def get_or_create_dataset(name: str, prompts: list[str]) -> opik.Dataset | None:
    client = opik.Opik()
    try:
        dataset = client.get_dataset(name=name)
    except Exception:
        dataset = None

    if dataset:
        print(f"Dataset '{name}' already exists. Skipping dataset creation.")

        return dataset

    assert prompts, "Prompts are required to create a dataset."

    dataset_items = []
    for prompt in prompts:
        dataset_items.append(
            {
                "input": prompt,
            }
        )

    dataset = create_dataset(
        name=name,
        description="Dataset for evaluating the agentic app.",
        items=dataset_items,
    )

    return dataset


def create_dataset(name: str, description: str, items: list[dict]) -> opik.Dataset:
    client = opik.Opik()

    dataset = client.get_or_create_dataset(name=name, description=description)
    dataset.insert(items)

    dataset = client.get_dataset(name=name)

    return dataset