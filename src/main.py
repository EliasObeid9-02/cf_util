import re, os, sys, bs4, time
import json, requests, argparse
from pathlib import Path

codeforces = "https://codeforces.com"
codeforces_api = codeforces + "/api"
codeforces_contests = codeforces + "/contests/with"
contest_status = codeforces_api + "/contest.status"
user_status = codeforces_api + "/user.status"

codeforces_tags = ["2-sat", "binary-search", "bitmasks", "brute-force",
    "chinese-remainder-theorem", "combinatorics", "constructive-algorithms",
    "data-structures", "dfs-and-similar", "divide-and-conquer", "dp", "dsu",
    "expression-parsing", "fft", "flows", "games", "geometry", "graph-matchings", "graphs", "greedy",
    "hashing", "implementation", "interactive", "math", "matrices", "meet-in-the-middle",
    "number-theory", "probabilities", "schedules", "shortest-paths", "sortings",
    "string-suffix-structures", "strings", "ternary-search", "trees", "two-pointers"]
### START Utility Functions

def get_submission_link(submission_id: str, contest_id: str) -> str:
    return codeforces + "/contest/" + contest_id + "/submission/" + submission_id

def get_submission_code(submission_id: str, contest_id: str) -> str:
    submission_link = get_submission_link(submission_id, contest_id)
    while True:
        page = requests.get(submission_link)
        html = bs4.BeautifulSoup(page.text, "html.parser")
        if (page.status_code != requests.codes.ok or
            not html.find(id="program-source-text")):
            time.sleep(30)
            continue
        break
    return html.find(id="program-source-text").text

def get_contest_list(user_handle: str) -> list:
    while True:
        page = requests.get(codeforces_contests + '/' + user_handle, {"type": "all"})
        html = bs4.BeautifulSoup(page.text, "html.parser")
        if page.status_code != requests.codes.ok or not html.find("a"):
            time.sleep(30)
            continue
        break

    contest_list = []
    for contest in html.find_all("a", {"href" : re.compile("/submissions/%s/contest/*" % user_handle)}):
        index = contest["href"].rfind('/') + 1
        contest_id = contest["href"][index:]
        contest_list.append(contest_id)
    return contest_list

def valid_tags(problem_tags: list[str], tags: list[str], combine_by_or: bool):
    for wanted_tag in tags:
        exists = (wanted_tag in problem_tags)
        if combine_by_or and exists:
            return True

        if not exists:
            return False
    return True

### END Utility Functions

### START Sub Commands

def contests_downloader(user_handle: str, count: int):
    if requests.get(codeforces + "/profile/" + user_handle).url == codeforces:
        raise Exception("Invalid user handle! User doesn't exist.")

    contests_folder = Path(user_handle) / "contests"
    os.mkdirs(contests_folder)
    for contest_id in get_contest_list(user_handle):
        os.mkdir(contests_folder / contest_id)
        try:
            data = json.loads(requests.get(contest_status, {"contestId": contest_id, "handle": user_handle}).text)
        except:
            raise Exception("Codeforces is down! Please try again later.")

        for submission in data["result"]:
            if submission["author"]["participantType"] == "PRACTICE":
                continue

            submission_id = str(submission["id"])
            submission_verdict = submission["verdict"]
            problem_index = submission["problem"]["index"]

            if submission_verdict != "OK":
                continue

            count -= 1
            if count == 0:
                break

            submission_code = get_submission_code(submission_id, contest_id)
            path = contests_folder / contest_id / str(problem_index + ".txt")
            if os.path.exists(path) and os.path.isfile(path):
                continue

            with open(path, "w") as code_file:
                code_file.write(submission_code)

def problems_downloader(user_handle: str, count: int, min_rating: int, max_rating: int, tags: list[str], combine_by_or: bool):
    if requests.get(codeforces + "/profile/" + user_handle).url == codeforces:
        raise Exception("Invalid user handle! User doesn't exist.")

    problems_folder = Path(user_handle) / "problems"
    if not os.path.exists(problems_folder):
        os.makedirs(problems_folder)
    accepted_submissions_count = {}
    try:
        data = json.loads(requests.get(user_status, {"handle": user_handle}).text)
    except:
        raise Exception("Codeforces is down! Please try again later.")

    for submission in data["result"]:
        if not submission["problem"].get("rating"):
            continue

        submission_id = str(submission["id"])
        submission_verdict = submission["verdict"]
        contest_id = str(submission["contestId"])
        problem_tags = submission["problem"]["tags"]
        problem_index = submission["problem"]["index"]
        problem_rating = submission["problem"]["rating"]

        if (submission_verdict != "OK" or
        not (min_rating <= problem_rating and problem_rating <= max_rating) or
        not valid_tags(problem_tags, tags, combine_by_or)):
            continue

        count -= 1
        if count == 0:
            break

        contest_folder = problems_folder / contest_id
        if not os.path.exists(contest_folder):
            os.mkdir(contest_folder)

        submission_code = get_submission_code(submission_id, contest_id)
        problem_name = contest_id + problem_index
        if not accepted_submissions_count.get(problem_name):
            accepted_submissions_count[problem_name] = 1

        submission_folder = contest_folder / (problem_name + "_%d%s" % (accepted_submissions_count[problem_name], ".txt"))
        accepted_submissions_count[problem_name] += 1
        with open(submission_folder, "w") as code_file:
            code_file.write(submission_code)

### END Sub Commands

### START Command Line Argument Parser

parser = argparse.ArgumentParser(prog="cf_util",
                                 description="Utility to get information " \
                                             "from the Codeforces website.")
subparser = parser.add_subparsers(title="Sub Commands",dest="command")
subparser.required = True

parser_contests_downloader = subparser.add_parser("contests-downloader",
                                                  description="Downloads the in-contest submissions of a specified user "   \
                                                  "in order from last participated in, optionally takes a second argument " \
                                                  "to specify the number of contests to download.")
parser_contests_downloader.add_argument("handle", type=str, help="Codeforces user handle.")
parser_contests_downloader.add_argument("-c", "--count", dest="count", type=int,
                                        help="Number of contests to download. Maximum of 5.")

parser_problems_downloader = subparser.add_parser("problems-downloader",
                                                  description="Downloads a user's submissions in order from last sent "     \
                                                  "to first sent, optionally can specify the minimum/maximum rating of "    \
                                                  "of a problem and can specify the allowed tags.")
parser_problems_downloader.add_argument("handle", type=str, help="Codeforces user handle.")
parser_problems_downloader.add_argument("-c", "--count", dest="count", required=False, type=int,
                                        help="Number of submissions to download. Maximum of 30.")
parser_problems_downloader.add_argument("-m", "--min-rating", dest="min_rating", type=int,
                                        help="Minumum rating of problem's submission allowed to be downloaded.")
parser_problems_downloader.add_argument("-M", "--max-rating", dest="max_rating", type=int,
                                        help="Maximum rating of problem's submission allowed to be downloaded.")
parser_problems_downloader.add_argument("-t", "--tags", dest="tags", nargs="+", type=str, choices=codeforces_tags,
                                        help="List of problem tags allowed to be downloaded.Note that the tags must be "   \
                                        "worded exactly how they are worded on codeforces, tags made up from multiple "     \
                                        "words then they must separated by a dash '-'.")
parser_problems_downloader.add_argument("-o", "--combine-by-or", dest="combine_by_or", type=bool,
                                        help="Option to specify whether all tags must be present to be downloaded.")

### END Command Line Argument Parser

def main():
    if len(sys.argv) == 1:
        raise Exception("Must specify command!")

    argv = sys.argv[1:]
    args = parser.parse_args(argv)
    match args.command:
        case "contests-downloader"  : command_contests_downloader(args)
        case "problems-downloader"  : command_problems_downloader(args)
        case _                      : raise Exception("Incorrect command!")

def command_contests_downloader(args):
    handle = args.handle
    count = 10_000
    if args.count:
        count = args.count
    contests_downloader(handle, count)

def command_problems_downloader(args):
    handle = args.handle
    count = 10_000
    min_rating = 0
    max_rating = 3_500
    tags = []
    combine_by_or = False

    if args.count:
        count = args.count

    if args.min_rating:
        min_rating = args.min_rating

    if args.max_rating:
        max_rating = args.max_rating

    if args.tags:
        for tag in args.tags:
            if tag == "meet-in-the-middle" or tag == "2-sat":
                tags.append(tag.lower())
            else:
                tags.append(tag.replace('-', ' ').lower())

    if args.combine_by_or:
        combine_by_or = args.combine_by_or
    problems_downloader(handle, count, min_rating, max_rating, tags, combine_by_or)