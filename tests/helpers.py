import copy
import typing


def ignore_template_assets(
    template_json: typing.Mapping[str, typing.Any]
) -> typing.Mapping[str, typing.Any]:
    template = copy.deepcopy(template_json)
    for resource in template["Resources"].values():
        if "Code" not in resource.get("Properties", {}):
            # not target
            continue
        if "ZipFile" in resource["Properties"]["Code"]:
            # keep code to check
            continue
        resource["Properties"]["Code"] = {}
    return template
