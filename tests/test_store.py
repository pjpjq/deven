from app.store import Store, MODELS


def test_reference_limit_and_clear(tmp_path):
    store = Store(str(tmp_path / "state.sqlite"))
    for idx in range(6):
        store.add_ref(42, f"file-{idx}", f"file-{idx}.jpg")
    assert [x[0] for x in store.get_refs(42)] == [
        "file-2", "file-3", "file-4", "file-5"
    ]
    store.clear_refs(42)
    assert store.get_refs(42) == []


def test_models_and_last_image(tmp_path):
    store = Store(str(tmp_path / "state.sqlite"))
    assert store.get_model(42) == "flare"
    store.set_model(42, "sunburst")
    assert MODELS[store.get_model(42)] == "gpt-image-2.6-sunburst"
    store.set_last_image(42, "telegram-image-id")
    assert store.get_last_image(42) == "telegram-image-id"
