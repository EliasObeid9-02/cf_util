import re, os, sys, bs4, time
import json, requests, argparse
from pathlib import Path

minimum_gym_id = 100_001
codeforces = "https://codeforces.com"
codeforces_api = codeforces + "/api"
codeforces_gym = codeforces + "/gym"
codeforces_contests = codeforces + "/contests/with"
contest_status = codeforces_api + "/contest.status"
user_status = codeforces_api + "/user.status"
codeforces_tags = [
    "2-sat",
    "binary-search",
    "bitmasks",
    "brute-force",
    "chinese-remainder-theorem",
    "combinatorics",
    "constructive-algorithms",
    "data-structures",
    "dfs-and-similar",
    "divide-and-conquer",
    "dp",
    "dsu",
    "expression-parsing",
    "fft",
    "flows",
    "games",
    "geometry",
    "graph-matchings",
    "graphs",
    "greedy",
    "hashing",
    "implementation",
    "interactive",
    "math",
    "matrices",
    "meet-in-the-middle",
    "number-theory",
    "probabilities",
    "schedules",
    "shortest-paths",
    "sortings",
    "string-suffix-structures",
    "strings",
    "ternary-search",
    "trees",
    "two-pointers",
]

### START Utility Functions


def get_problem_link(problem_index: str, contest_id: str) -> str:
    return codeforces + "/contest/" + contest_id + "/problem/" + problem_index


def get_submission_link(submission_id: str, contest_id: str) -> str:
    return codeforces + "/contest/" + contest_id + "/submission/" + submission_id


def get_submission_code(submission_id: str, contest_id: str) -> str:
    submission_link = get_submission_link(submission_id, contest_id)
    while True:
        page = requests.get(submission_link)
        html = bs4.BeautifulSoup(page.text, "html.parser")
        if page.status_code != requests.codes.ok or not html.find(
            id="program-source-text"
        ):
            time.sleep(30)
            continue
        break
    return html.find(id="program-source-text").text


def get_contest_list(user_handle: str) -> list:
    while True:
        page = requests.get(codeforces_contests + "/" + user_handle, {"type": "all"})
        html = bs4.BeautifulSoup(page.text, "html.parser")
        if page.status_code != requests.codes.ok or not html.find("a"):
            time.sleep(30)
            continue
        break

    contest_list = []
    for contest in html.find_all(
        "a", {"href": re.compile("/submissions/%s/contest/*" % user_handle)}
    ):
        index = contest["href"].rfind("/") + 1
        contest_id = contest["href"][index:]
        contest_list.append(contest_id)
    return contest_list


def valid_tags(problem_tags: list[str], tags: list[str], combine_by_or: bool):
    for wanted_tag in tags:
        exists = wanted_tag in problem_tags
        if combine_by_or and exists:
            return True

        if not exists:
            return False
    return True


### END Utility Functions

### START Sub Commands


def contests_downloader(user_handles: list[str], contest_count: int):
    for user_handle in user_handles:
        count = contest_count
        if requests.get(codeforces + "/profile/" + user_handle).url == codeforces:
            raise Exception("Invalid user handle! User doesn't exist.")

        files_path = Path("problems") / user_handle
        os.makedirs(files_path)
        for contest_id in get_contest_list(user_handle):
            os.mkdir(files_path / contest_id)
            try:
                data = json.loads(
                    requests.get(
                        contest_status, {"contestId": contest_id, "handle": user_handle}
                    ).text
                )
            except:
                raise Exception("Codeforces is down! Please try again later.")

            count -= 1
            for submission in data["result"]:
                if submission["author"]["participantType"] == "PRACTICE":
                    continue

                submission_id = str(submission["id"])
                submission_verdict = submission["verdict"]
                problem_index = submission["problem"]["index"]

                if submission_verdict != "OK":
                    continue

                submission_code = get_submission_code(submission_id, contest_id)
                path = files_path / contest_id / str(problem_index + ".txt")
                if os.path.exists(path) and os.path.isfile(path):
                    continue

                with open(path, "w") as code_file:
                    code_file.write(submission_code)

            if count == 0:
                break


def problems_downloader(
    user_handles: list[str],
    problem_count: int,
    min_rating: int,
    max_rating: int,
    tags: list[str],
    combine_by_or: bool,
    list_only: bool,
):
    for user_handle in user_handles:
        count = problem_count
        if requests.get(codeforces + "/profile/" + user_handle).url == codeforces:
            raise Exception("Invalid user handle! User doesn't exist.")

        files_path = Path("problems") / user_handle
        if not os.path.exists(files_path):
            os.makedirs(files_path)

        accepted_submissions_count = {}
        try:
            data = json.loads(requests.get(user_status, {"handle": user_handle}).text)
        except:
            raise Exception("Codeforces is down! Please try again later.")

        list_file_path = files_path / "problem_list.txt"
        list_file = open(list_file_path, "w")

        for submission in data["result"]:
            if count == 0:
                break

            if not submission["problem"].get("rating"):
                continue

            submission_id = str(submission["id"])
            submission_verdict = submission["verdict"]
            contest_id = str(submission["contestId"])
            problem_tags = submission["problem"]["tags"]
            problem_index = submission["problem"]["index"]
            problem_rating = submission["problem"]["rating"]

            if (
                submission_verdict != "OK"
                or not (min_rating <= problem_rating and problem_rating <= max_rating)
                or not valid_tags(problem_tags, tags, combine_by_or)
            ):
                continue

            count -= 1
            list_file.write(
                get_problem_link(problem_index, contest_id)
                + " "
                + get_submission_link(submission_id, contest_id)
                + "\n"
            )

            if list_only:
                continue

            contest_folder = files_path / contest_id
            if not os.path.exists(contest_folder):
                os.mkdir(contest_folder)

            submission_code = get_submission_code(submission_id, contest_id)
            problem_name = contest_id + problem_index
            if not accepted_submissions_count.get(problem_name):
                accepted_submissions_count[problem_name] = 1

            submission_folder = contest_folder / (
                problem_name
                + "_%d%s" % (accepted_submissions_count[problem_name], ".txt")
            )
            accepted_submissions_count[problem_name] += 1
            with open(submission_folder, "w") as code_file:
                code_file.write(submission_code)


def get_gym_list(user_handles: list[str]):
    for user_handle in user_handles:
        if requests.get(codeforces + "/profile/" + user_handle).url == codeforces:
            raise Exception("Invalid user handle! User doesn't exist.")

        files_path = Path("problems") / user_handle
        if not os.path.exists(files_path):
            os.makedirs(files_path)

        try:
            data = json.loads(requests.get(user_status, {"handle": user_handle}).text)
        except:
            raise Exception("Codeforces is down! Please try again later.")

        gym_list = {}
        for submission in data["result"]:
            contest_id = str(submission["contestId"])
            if int(contest_id) >= minimum_gym_id and not gym_list.get(contest_id):
                gym_list[contest_id] = True

        gym_list_file_path = files_path / "gym_list.txt"
        gym_list_file = open(gym_list_file_path, "w")
        for gym_id in gym_list.keys():
            gym_list_file.write(codeforces_gym + "/" + gym_id + "\n")
        gym_list_file.close()


### END Sub Commands

### START Command Line Argument Parser

parser = argparse.ArgumentParser(
    prog="cf_util",
    description="Utility to get information " "from the Codeforces website.",
)
subparser = parser.add_subparsers(title="Sub Commands", dest="command")
subparser.required = True

parser_contests_downloader = subparser.add_parser(
    "contests-downloader",
    description="Downloads the in-contest submissions of a specified user "
    "in order from last participated in, optionally takes a second argument "
    "to specify the number of contests to download.",
)
parser_contests_downloader.add_argument(
    "user_handles", type=str, help="Codeforces user(s) handle.", nargs="+"
)
parser_contests_downloader.add_argument(
    "-c",
    "--count",
    dest="count",
    type=int,
    nargs="?",
    default=10_000,
    help="Number of contests to download. Maximum of 5.",
)

parser_problems_downloader = subparser.add_parser(
    "problems-downloader",
    description="Downloads a user's submissions in order from last sent "
    "to first sent, optionally can specify the minimum/maximum rating of "
    "of a problem and can specify the allowed tags.",
)
parser_problems_downloader.add_argument(
    "user_handles",
    type=str,
    nargs="+",
    help="Codeforces user(s) handle." "At least one handle must be provided.",
)
parser_problems_downloader.add_argument(
    "-c",
    "--count",
    dest="count",
    type=int,
    nargs="?",
    default=10_000,
    help="Number of submissions to download. Default of 10'000.",
)
parser_problems_downloader.add_argument(
    "-m",
    "--min-rating",
    dest="min_rating",
    type=int,
    nargs="?",
    default=0,
    help="Minumum rating of problem's submission allowed to be downloaded. Default of 0.",
)
parser_problems_downloader.add_argument(
    "-M",
    "--max-rating",
    dest="max_rating",
    type=int,
    nargs="?",
    default=3500,
    help="Maximum rating of problem's submission allowed to be downloaded. Default of 3500.",
)
parser_problems_downloader.add_argument(
    "-t",
    "--tags",
    dest="tags",
    type=str,
    choices=codeforces_tags,
    nargs="+",
    help="List of problem tags allowed to be downloaded.Note that the tags must be "
    "worded exactly how they are worded on codeforces, tags made up from multiple "
    "words then they must separated by a dash '-'. At least one tag must be provided.",
    metavar="TAGS",
)
parser_problems_downloader.add_argument(
    "-o",
    "--combine-by-or",
    dest="combine_by_or",
    action="store_true",
    help="This option specifies whether all tags must be present for a problem to be inculded.",
)
parser_problems_downloader.add_argument(
    "-l",
    "--list-only",
    dest="list_only",
    action="store_true",
    help="This option saves a list of problem links and submission links without "
    "downloading any codes.",
)

parser_get_gym_list = subparser.add_parser(
    "get-gym-list",
    description="Returns a text file containing a list of links to all gym contests the user has sent a submission in.",
)
parser_get_gym_list.add_argument(
    "user_handles", type=str, help="Codeforces user(s) handle.", nargs="+"
)

### END Command Line Argument Parser


def main():
    if len(sys.argv) == 1:
        raise Exception("Must specify command!")

    argv = sys.argv[1:]
    args = parser.parse_args(argv)
    match args.command:
        case "contests-downloader":
            command_contests_downloader(args)
        case "problems-downloader":
            command_problems_downloader(args)
        case "get-gym-list":
            command_get_gym_list(args)
        case _:
            raise Exception("Incorrect command!")


def command_contests_downloader(args):
    user_handles = args.user_handles
    count = args.count
    contests_downloader(user_handles, count)


def command_problems_downloader(args):
    user_handles = args.user_handles
    count = args.count
    min_rating = args.min_rating
    max_rating = args.max_rating
    combine_by_or = args.combine_by_or
    list_only = args.list_only

    tags = []
    if args.tags:
        for tag in args.tags:
            if tag == "meet-in-the-middle" or tag == "2-sat":
                tags.append(tag.lower())
            else:
                tags.append(tag.replace("-", " ").lower())
    problems_downloader(
        user_handles, count, min_rating, max_rating, tags, combine_by_or, list_only
    )


def command_get_gym_list(args):
    user_handles = args.user_handles
    get_gym_list(user_handles)
