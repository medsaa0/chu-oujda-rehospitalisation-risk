from orchestration.prefect_flows.pipeline_flow import (
    etl_task,
    features_task,
    hospital_readmission_pipeline,
    ingestion_task,
    marts_task,
    validation_task,
    warehouse_task,
)


def test_flow_has_expected_name() -> None:
    assert hospital_readmission_pipeline.name == "hospital-readmission-pipeline"


def test_tasks_are_named_after_their_pipeline_step() -> None:
    expected_names = {
        ingestion_task: "ingestion",
        validation_task: "validation",
        etl_task: "etl",
        features_task: "feature_engineering",
        warehouse_task: "data_warehouse",
        marts_task: "data_marts",
    }

    for task_object, expected_name in expected_names.items():
        assert task_object.name == expected_name


def test_tasks_have_retries_configured() -> None:
    for task_object in (
        ingestion_task,
        validation_task,
        etl_task,
        features_task,
        warehouse_task,
        marts_task,
    ):
        assert task_object.retries == 2
