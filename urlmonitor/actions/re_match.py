import re


def action_object(name, arglst, url, content, variables, log):
    result = []
    for regex in arglst:
        match = re.search(regex.encode(), content, re.MULTILINE)
        if match:
            all_groups = [match[0]] + list(match.groups())
        else:
            all_groups = [b""]
        result.append([x.decode() for x in all_groups])

    return {"re_match": result[0], "re_match_all": result}
