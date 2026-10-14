from src.utils import s3


def test_upload_json_creates_bucket_if_missing(monkeypatch):
    calls = []

    class FakeClient:
        def head_bucket(self, Bucket):
            raise Exception("Bucket not found")

        def create_bucket(self, Bucket):
            calls.append(("create_bucket", Bucket))

        def put_object(self, Bucket, Key, Body, ContentType):
            calls.append(("put_object", Bucket, Key, ContentType))

    monkeypatch.setattr(s3, "_get_s3_client", lambda: FakeClient())
    monkeypatch.setattr(s3, "_bucket", lambda: "demo-bucket")

    s3.upload_json_to_s3("raw/test.json", {"hello": "world"})

    assert ("create_bucket", "demo-bucket") in calls
    assert any(item[0] == "put_object" for item in calls)
