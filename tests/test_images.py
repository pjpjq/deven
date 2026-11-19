import base64
from types import SimpleNamespace
import pytest

import app.images as images


def test_generate_text_only(monkeypatch):
    calls = []
    class FakeImages:
        def generate(self, **kwargs):
            calls.append(("generate", kwargs))
            return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(b"image").decode())])
        def edit(self, **kwargs):
            raise AssertionError("Unexpected edit call")
    monkeypatch.setattr(images, "OpenAI", lambda api_key: SimpleNamespace(images=FakeImages()))
    assert images.generate("key", "gpt-image-2.6-flare", "a luxury villa") == b"image"
    assert calls[0][0] == "generate"


def test_references_use_binary_edit(monkeypatch):
    calls = []
    class FakeImages:
        def edit(self, **kwargs):
            calls.append(kwargs)
            assert kwargs["image"][0].read() == b"not-a-URL"
            return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(b"edited").decode())])
        def generate(self, **kwargs):
            raise AssertionError("Expected edits with images")
    monkeypatch.setattr(images, "OpenAI", lambda api_key: SimpleNamespace(images=FakeImages()))
    assert images.generate("key", "gpt-image-2.6-sunburst", "replace marble", [("room.jpg", b"not-a-URL")], is_edit=True) == b"edited"
    assert calls[0]["model"] == "gpt-image-2.6-sunburst"


def test_edit_requires_image(monkeypatch):
    with pytest.raises(ValueError, match="original image"):
        images.generate("key", "gpt-image-2.6-flare", "change sofa", is_edit=True)


def test_reject_bad_reference_filename():
    with pytest.raises(ValueError, match="Reference file"):
        images.image_stream("bad.txt", b"garbage")
