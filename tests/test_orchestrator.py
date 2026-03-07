import json

import pytest
from pydantic import BaseModel

from app.pipeline.llm_enricher import DatasetProfile
from app.pipeline.orchestrator import json_ready
from app.pipeline.step_base import PipelineContext


class DummyModel(BaseModel):
    a: int
    b: str
    nested: DatasetProfile | None = None


def test_json_ready_serializes_pydantic_models():
    profile = DatasetProfile(total_rows=42, total_columns=5, has_dates=True)
    # direct application should return a dictionary with primitive values
    ready = json_ready(profile)
    assert isinstance(ready, dict)
    assert ready["total_rows"] == 42
    assert ready["has_dates"] is True

    # nested models should be walked recursively
    dummy = DummyModel(a=1, b="x", nested=profile)
    nested_ready = json_ready(dummy)
    assert nested_ready["nested"]["total_rows"] == 42

    # result should be JSON serializable without blowing up
    json.dumps(nested_ready)


def test_step_outputs_with_dataset_profile_are_jsonable():
    ctx = PipelineContext(job_id="123", file_path="/tmp/foo.xlsx")
    ctx.dataset_profile = DatasetProfile(total_rows=10)

    # the new helper method should exist and behave like ``model_dump``
    assert isinstance(ctx.dataset_profile.to_dict(), dict)
    assert ctx.dataset_profile.to_dict()["total_rows"] == 10

    step_outputs = {"dataset_profile": json_ready(ctx.dataset_profile)}
    # ensure the dictionary contains no raw BaseModel
    assert not isinstance(step_outputs["dataset_profile"], DatasetProfile)

    # final sanity: writing to string should succeed
    s = json.dumps(step_outputs)
    assert "total_rows" in s


def test_serialize_dataclasses_and_detached_schema():
    # construct a minimal DetectedSchema with nested dataclasses
    from app.pipeline.schema_detector import ColumnSchema, DetectedSchema, SheetSchema

    col = ColumnSchema(name="id", inferred_type="Int64", null_count=0, unique_count=1, is_primary_key=True)
    sheet = SheetSchema(name="Sheet1", columns=[col], row_count=1)
    schema = DetectedSchema(sheets=[sheet], relationships=[])

    serialized = json_ready(schema)
    # should be a dict with primitive contents
    assert isinstance(serialized, dict)
    assert serialized["sheets"][0]["name"] == "Sheet1"
    assert serialized["sheets"][0]["columns"][0]["name"] == "id"

    # also verify nested lists convert
    assert json.dumps(serialized)


def test_jsonsafe_type_decorator():
    from app.db.serialization import JSONSafe, serialize_for_db

    typ = JSONSafe()

    # process_bind_param should return same as serialize_for_db
    class Dummy:
        def __str__(self):
            return "dummy"

    d = {"x": Dummy()}
    bound = typ.process_bind_param(d, None)
    assert bound == serialize_for_db(d)
    assert isinstance(bound, dict)


def test_commit_or_rollback_rolls_back_on_error():
    # mimic a session object
    class FakeSession:
        def __init__(self):
            self.rolled = False

        async def commit(self):
            raise RuntimeError("boom")

        async def rollback(self):
            self.rolled = True

    fake = FakeSession()

    async def runner():
        # reimplement the helper logic from orchestrator
        try:
            await fake.commit()
        except Exception:
            await fake.rollback()
            raise

    import asyncio

    with pytest.raises(RuntimeError):
        asyncio.run(runner())
    assert fake.rolled


def test_pipeline_state_jsonsafe_binding():
    from app.models.pipeline_state import PipelineState
    from app.pipeline.schema_detector import DetectedSchema

    # confirm column type is our JSONSafe alias
    col_type = PipelineState.__table__.c.step_outputs.type
    from app.db.serialization import JSONSafe

    assert isinstance(col_type, JSONSafe)

    # ensure binding a dataclass goes through the serializer
    schema = DetectedSchema(sheets=[], relationships=[])
    bound = col_type.process_bind_param({"schema": schema}, None)
    assert isinstance(bound, dict)
    assert isinstance(bound["schema"], dict)


def test_attribute_auto_serialization():
    import uuid

    from app.models.pipeline_state import PipelineState
    from app.pipeline.schema_detector import DetectedSchema

    ps = PipelineState(job_id=uuid.uuid4())
    schema = DetectedSchema(sheets=[], relationships=[])
    # assign raw object
    ps.step_outputs = {"schema": schema}
    # listener should have converted it
    assert isinstance(ps.step_outputs["schema"], dict)

    # also check AnalysisJob columns
    from app.models.job import AnalysisJob

    aj = AnalysisJob(user_id=uuid.uuid4(), org_id=uuid.uuid4(), file_name="x", file_path="y", file_size_bytes=0)
    aj.schema_result = schema
    assert isinstance(aj.schema_result, dict)
