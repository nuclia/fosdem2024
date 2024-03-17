from nucliadb_sdk.v2.exceptions import NotFoundError
from nuclia import sdk
import traceback
import string
import json

CACHE_FILE = "fosdem.cache.2024"

APIKEY_2024 = ""
KB_2024 = "https://europe-1.nuclia.cloud/api/v1/kb/ace5bccb-5d5b-45d6-830a-3b0db0c26827"

auth = sdk.NucliaAuth()
auth.kb(url=KB_2024, token=APIKEY_2024)
print(auth._config.get_default_kb())


kb_sdk = sdk.NucliaKB()
resources_sdk = sdk.NucliaResource()
upload_sdk = sdk.NucliaUpload()
resource_sdk = sdk.NucliaResource()
resources = kb_sdk.list(url=KB_2024, api_key=APIKEY_2024)

# Upload new objects

TRANS = str.maketrans("", "", string.punctuation)
with open(CACHE_FILE, "r") as cache_fd:
    cache = json.loads(cache_fd.read())

count = 0
for url, obj in cache.items():
    print(obj["title"])
    print(f"{count}/{len(cache)}")
    count += 1
    if obj["video"] is not None and obj["uploaded"] is False:
        slug = obj["title"].translate(TRANS).replace(" ", "-").replace("’", "").lower()
        slug = "".join([x for x in list(slug) if ord(x) < 123])
        print(obj["title"])
        print(slug)
        create = True
        try:
            res = resource_sdk.get(slug=slug, show=["basic", "values"])
            if res.data.files is not None and "video" in res.data.files:
                obj["uploaded"] = True
                with open(CACHE_FILE, "w+") as cache_file:
                    cache_file.write(json.dumps(cache))
                print("Fixed")
                continue
            create = False
        except NotFoundError:
            pass

        if create:
            rid = resources_sdk.create(**obj)
        else:
            rid = res.id

        obj["rid"] = rid
        print(rid)
        try:
            upload_sdk.remote(origin=obj["video"], rid=rid, field="video.webm")

            if obj["attachment"] is not None:
                upload_sdk.remote(origin=obj["attachment"], rid=rid, field="slides.pdf")
            obj["uploaded"] = True
        except Exception:
            traceback.print_stack()

        with open(CACHE_FILE, "w+") as cache_file:
            cache_file.write(json.dumps(cache))
