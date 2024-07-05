# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Import necessary libraries
import argparse
import arxiv
import requests
import os
from datetime import datetime, timedelta
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import time

# Define a function to download a paper
def download_paper(result, download_dir, max_retries=3, retry_delay=5):
    # Get the URL to download the paper
    pdf_url = result.entry_id + '.pdf'
    pdf_url = pdf_url.split("/")[-1] 
    pdf_url = f"https://arxiv.org/pdf/{pdf_url}"
    retries = 0

    # Try downloading the paper with retries
    while retries < max_retries:
        try:
            pdf_response = requests.get(pdf_url)
            print(pdf_response, pdf_url)
            if pdf_response.status_code == 200:
                # Save the paper to the download directory
                pdf_filename = result.title.replace(' ', '_') + '.pdf'
                pdf_filepath = os.path.join(download_dir, pdf_filename)
                with open(pdf_filepath, 'wb') as f:
                    f.write(pdf_response.content)
                print(f"Downloaded: {result.entry_id} - {result.title}")
                return  # Exit the function if download is successful
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {result.entry_id}: {e}")

        # Retry logic
        retries += 1
        print(f"Retrying download for {result.entry_id} in {retry_delay} seconds...")
        time.sleep(retry_delay)

    print(f"Failed to download: {result.entry_id} - {result.title} (after {max_retries} retries)")

# Define a function to download papers based on search criteria
def download_papers(search_terms, start_date, end_date, max_results=10, download_dir='papers', num_threads=4, max_retries=3, retry_delay=5):
    # Create the search query based on search terms and dates
    search_query = f"({search_terms}) AND submittedDate:[{start_date.strftime('%Y%m%d')} TO {end_date.strftime('%Y%m%d')}]"

    search = arxiv.Search(
        query=search_query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )

    # Create the download directory if it doesn't exist
    os.makedirs(download_dir, exist_ok=True)

    # Use a thread pool to download papers in parallel
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for result in tqdm(search.results(), total=max_results, unit='paper'):
            # Submit download tasks to the executor
            future = executor.submit(download_paper, result, download_dir, max_retries, retry_delay)
            futures.append(future)

# Main function to parse arguments and execute the download
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download research papers from arXiv.org')
    parser.add_argument('-s', '--search-terms', required=True, help='A comma-separated list of search terms')
    parser.add_argument('-sd', '--start-date', help='Start date in the format YYYY-MM-DD (default: 10 years ago)')
    parser.add_argument('-ed', '--end-date', help='End date in the format YYYY-MM-DD (default: today)')
    parser.add_argument('-n', '--max-results', type=int, default=10, help='Maximum number of papers to download (default: 10)')
    parser.add_argument('-d', '--download-dir', default='papers', help='Directory to save the downloaded papers (default: papers)')
    parser.add_argument('-t', '--num-threads', type=int, default=4, help='Number of threads to use for parallel downloads (default: 4)')
    parser.add_argument('-r', '--max-retries', type=int, default=3, help='Maximum number of retries for each download (default: 3)')
    parser.add_argument('-rd', '--retry-delay', type=int, default=5, help='Delay in seconds between retries (default: 5)')

    args = parser.parse_args()

    # Handle the start date
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        except ValueError:
            print(f"Invalid start date format. Please use YYYY-MM-DD. Provided: {args.start_date}")
            exit(1)
    else:
        start_date = datetime.now() - timedelta(days=365 * 10)  # Default to 10 years ago

    # Handle the end date
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError:
            print(f"Invalid end date format. Please use YYYY-MM-DD. Provided: {args.end_date}")
            exit(1)
    else:
        end_date = datetime.now()  # Default to today

    # Call the download_papers function with the provided arguments
    download_papers(args.search_terms, start_date, end_date, args.max_results, args.download_dir, args.num_threads, args.max_retries, args.retry_delay)

