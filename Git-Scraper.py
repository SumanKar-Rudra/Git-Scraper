import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
import pyfiglet

def print_git_cred_scraper_ascii_art():
    text = "Git Cred Scraper"
    ascii_art = pyfiglet.figlet_format(text)
    print(ascii_art)

# Call the function to print the ASCII art
print_git_cred_scraper_ascii_art()

def clone_repo(repo_url, destination):
    """
    Clones a Git repository to the specified destination.
    """
    try:
        subprocess.run(['git', 'clone', repo_url, destination], check=True)
        print("Repository cloned successfully:", repo_url)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

def clone_repos(repo_list_file, destination):
    """
    Clones Git repositories listed in a text file to the specified destination directory using multiple threads.
    """
    with open(repo_list_file, 'r') as f:
        repo_urls = [line.strip() for line in f.readlines() if line.strip()]

    if not os.path.exists(destination):
        os.makedirs(destination)

    with ThreadPoolExecutor(max_workers=5) as executor:
        for repo_url in repo_urls:
            executor.submit(clone_repo, repo_url, os.path.join(destination, repo_url.split('/')[-1]))

def search_keywords_in_repo(keyword, file_path):
    """
    Searches for a keyword within a file and returns two lines above and below containing the keyword.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

            results = []
            keyword_regex = re.compile(re.escape(keyword), re.IGNORECASE)
            for line_num, line in enumerate(lines, start=1):
                if keyword_regex.search(line):
                    start_line = max(0, line_num - 2)
                    end_line = min(len(lines), line_num + 3)
                    context_lines = [lines[i].strip() for i in range(start_line - 1, end_line)]
                    results.append((file_path, line_num, context_lines))

            return results
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []

def search_keywords_in_repos(keyword_file, repos_directory):
    """
    Searches for keywords listed in a text file within files in all repositories cloned in a directory.
    """
    with open(keyword_file, 'r') as f:
        keywords = [line.strip() for line in f.readlines() if line.strip()]

    results = []
    for root, dirs, files in os.walk(repos_directory):
        for file in files:
            file_path = os.path.join(root, file)
            with ThreadPoolExecutor(max_workers=5) as executor:
                for keyword in keywords:
                    results += executor.submit(search_keywords_in_repo, keyword, file_path).result()

    return results

def generate_html_output(results, output_file, keywords):
    """
    Generates an accordion-based HTML report with the search results, highlighting all keywords with red text background.
    """
    with open(output_file, 'w') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search Results</title>
    <style>
        .accordion {
            background-color: #f9f9f9;
            cursor: pointer;
            padding: 18px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 15px;
            transition: 0.4s;
            border-radius: 10px;
        }

        .active, .accordion:hover {
            background-color: #ddd;
        }

        .panel {
            padding: 0 18px;
            background-color: white;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.2s ease-out;
        }

        .highlight {
            background-color: red;
            color: white;
            padding: 3px;
            border-radius: 3px;
        }
    </style>
    <script>
        function filterKeywords(keyword) {
            var items = document.getElementsByClassName('accordion');
            for (var i = 0; i < items.length; i++) {
                var panel = items[i].nextElementSibling;
                if (panel.innerHTML.toLowerCase().includes(keyword.toLowerCase())) {
                    items[i].style.display = 'block';
                } else {
                    items[i].style.display = 'none';
                }
            }
        }
    </script>
</head>
<body>

<h1>Search Results</h1>
<input type="text" id="filterInput" onkeyup="filterKeywords(this.value)" placeholder="Filter by keyword..">
''')
        for keyword in keywords:
            f.write(f"<button onclick=\"filterKeywords('{keyword}')\">{keyword}</button>\n")
            for result in results:
                if keyword.lower() in result[2][0].lower():
                    f.write(f"<button class='accordion'>{result[0]} (Line: {result[1]})</button>\n")
                    f.write(f"<div class='panel'>\n")
                    f.write("<ul>\n")
                    for line in result[2]:
                        line = re.sub(re.escape(keyword), f'<span class="highlight">{keyword}</span>', line, flags=re.IGNORECASE)
                        f.write(f"<li>{line}</li>\n")
                    f.write("</ul>\n")
                    f.write("</div>\n")
    print(f"HTML output generated: {output_file}")

if __name__ == "__main__":
    repo_list_file = input("Enter the path to the text file containing Git repository URLs: ")
    keyword_file = input("Enter the path to the text file containing keywords to search: ")
    destination = input("Enter the destination directory to clone the repositories: ")
    output_file = input("Enter the path for the HTML output file: ")

    clone_repos(repo_list_file, destination)
    keywords = [line.strip() for line in open(keyword_file)]
    search_results = search_keywords_in_repos(keyword_file, destination)
    generate_html_output(search_results, output_file, keywords)

    # Clean up: Remove the cloned repositories
    shutil.rmtree(destination)
    print("Repository directory removed.")
