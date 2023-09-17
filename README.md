# cf_util

cf_util is a simple Python-based command line script that allows the user to get information about submissions for a specific user from the codeforces website easily.

# Usage
##### Install using

	pip install cf_util
    
##### Update using

	pip install --upgrade cf_util
    
##### Contests Downloader
	
    cf_util contests-downloader tourist
    
Downloads all in-contest **accepted** submissions for the specified user in order from newest to oldest.

Can use the optional argument `-c` or `--count` to specify how many contests to download, e.g, `cf_util contests-downloader tourist -c 5`.

##### Problems Downloader

	cf_util problems-downloader tourist
   	
Downloads all **accepted** submissions for the specified user in order from newest to oldest.

Can use the following optional arguments:
1. `-c` or `--count` to specify the number of submissions to download.
2. `-m` or `--min-rating` to specify the minimum problem rating for a problem to be downloaded, set by default to 0.
3. `-M` or `--max-rating` to specify the maximum problem rating for a problem to be downloaded, set by default to 3500.
4. `-t` or `--tags` to specify the allowed problem tags. Tags must be written in the same way they are written on the *codeforces* website, tags with multiple words must be separated by `-` instead of spaces. Note that by default if you specify multiple tags then they must all be present in a problem.
5. `-o` or `--combine-by-or` in order to allow the presence of only one tag for a problem submission to be downloaded.