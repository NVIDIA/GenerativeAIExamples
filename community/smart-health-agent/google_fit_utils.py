# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from google.auth.transport.requests import Request

# Scopes for Google Fit
SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.heart_rate.read',
    'https://www.googleapis.com/auth/fitness.sleep.read'
]

def authorize_google_fit() -> Credentials:
    """
    Authorizes with the Google Fit API and saves credentials to token.json.
    """
    flow = InstalledAppFlow.from_client_secrets_file('client_secret_gfit.json', SCOPES)
    credentials = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(credentials.to_json())
    return credentials

def get_google_fitness_data() -> dict:
    """
    Fetches real user fitness data from Google Fit (Steps, HR, Sleep) for the last 7 days and computes daily averages.
    """
    credentials = None
    
    # Try to load existing credentials
    try:
        credentials = Credentials.from_authorized_user_file('token.json', SCOPES)
    except Exception as e:
        print(f"Could not load token file: {e}")
        credentials = None
    
    # Check if credentials exist and are valid
    if credentials and credentials.valid:
        print("Using existing valid credentials")
    else:
        # If credentials expired, try to refresh them
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                print("Attempting to refresh expired credentials")
                credentials.refresh(Request())
                # Save refreshed credentials
                with open('token.json', 'w') as token:
                    token.write(credentials.to_json())
            except Exception as refresh_error:
                print(f"Error refreshing token: {refresh_error}")
                credentials = None
        
        # If still no valid credentials, authorize from scratch
        if not credentials or not credentials.valid:
            print("Getting new authorization")
            credentials = authorize_google_fit()
    
    service = build('fitness', 'v1', credentials=credentials)

    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    end_time_ms = int(end_time.timestamp() * 1000)
    start_time_ms = int(start_time.timestamp() * 1000)
    
    # Steps, calories, heart rate
    body = {
        "aggregateBy": [
            {
                "dataTypeName": "com.google.step_count.delta",
                "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
            },
            {
                "dataTypeName": "com.google.calories.expended"
            },
            {
                "dataTypeName": "com.google.heart_rate.bpm",
                "dataSourceId": "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm"
            }
        ],
        "bucketByTime": {"durationMillis": 86400000},  # 1 day buckets
        "startTimeMillis": start_time_ms,
        "endTimeMillis": end_time_ms
    }
    resp = service.users().dataset().aggregate(userId="me", body=body).execute()

    # Sleep data - try multiple approaches
    # 1. First try sleep segments
    sleep_body = {
        "aggregateBy": [{"dataTypeName": "com.google.sleep.segment"}],
        "bucketByTime": {"durationMillis": 86400000},  # 1 day buckets
        "startTimeMillis": start_time_ms,
        "endTimeMillis": end_time_ms
    }
    sleep_resp = service.users().dataset().aggregate(userId="me", body=sleep_body).execute()
    
    # 2. Also try to get sleep sessions data 
    sleep_sessions = get_sleep_sessions(service, start_time_ms, end_time_ms)
    
    return process_fitness_data(resp, sleep_resp, sleep_sessions)

def get_sleep_sessions(service, start_time_ms, end_time_ms):
    """
    Gets sleep sessions from Google Fit which often has more complete sleep data.
    """
    try:
        # List all available data sources to find sleep data
        datasources = service.users().dataSources().list(userId="me").execute()
        
        # Try to find sleep sources and session data
        sleep_sources = []
        for source in datasources.get('dataSource', []):
            if 'sleep' in source.get('dataType', {}).get('name', '').lower():
                sleep_sources.append(source.get('dataStreamId'))
        
        # Get session data 
        sessions_response = service.users().sessions().list(
            userId="me",
            startTime=datetime.fromtimestamp(start_time_ms / 1000).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            endTime=datetime.fromtimestamp(end_time_ms / 1000).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            includeDeleted=False
        ).execute()
        
        # Filter for sleep sessions
        sleep_sessions = []
        for session in sessions_response.get('session', []):
            if session.get('activityType', 0) == 72:  # Sleep activity type
                sleep_duration_ms = session.get('endTimeMillis', 0) - session.get('startTimeMillis', 0)
                sleep_hours = sleep_duration_ms / (1000 * 60 * 60)
                
                session_date = datetime.fromtimestamp(int(session.get('startTimeMillis', 0)) / 1000).date()
                sleep_sessions.append({
                    'date': session_date.strftime("%Y-%m-%d"),
                    'sleep_hours': round(sleep_hours, 2)
                })
                
        return sleep_sessions
    except Exception as e:
        print(f"Error getting sleep sessions: {e}")
        return []

def process_fitness_data(response: dict, sleep_response: dict, sleep_sessions: list) -> dict:
    """
    Converts raw Google Fit response to a cleaned dictionary with 7-day averages.
    """
    days = 0
    steps_list = []
    hr_list = []
    sleep_list = []
    sleep_sessions_by_date = {}
    
    # Organize sleep sessions by date
    for session in sleep_sessions:
        sleep_sessions_by_date[session['date']] = session['sleep_hours']

    # Steps, calories, heart rate (per day)
    for bucket in response.get('bucket', []):
        day_steps = 0
        day_hr = []
        # Extract date from bucket start time
        bucket_date = datetime.fromtimestamp(int(bucket.get('startTimeMillis', 0)) / 1000).date().strftime("%Y-%m-%d")
        
        for dataset in bucket.get('dataset', []):
            data_source_id = dataset.get('dataSourceId', '')
            for point in dataset.get('point', []):
                if 'step_count' in data_source_id:
                    day_steps += point['value'][0]['intVal']
                elif 'heart_rate' in data_source_id:
                    day_hr.append(point['value'][0]['fpVal'])
        steps_list.append(day_steps)
        if day_hr:
            hr_list.append(sum(day_hr) / len(day_hr))
        else:
            hr_list.append(0)
            
        # Try to get sleep from sessions first
        if bucket_date in sleep_sessions_by_date and sleep_sessions_by_date[bucket_date] > 0:
            sleep_list.append(sleep_sessions_by_date[bucket_date])
        else:
            # Fallback to sleep segments if no session data
            sleep_hours = process_sleep_bucket(bucket_date, sleep_response)
            if sleep_hours > 0:
                sleep_list.append(sleep_hours)
            else:
                # If we have neither, assume average adult sleep (for demo)
                sleep_list.append(7.0)

    # Compute averages (ignore days with 0 data)
    avg_steps = round(sum(steps_list) / max(len([s for s in steps_list if s > 0]), 1), 2)
    avg_hr = round(sum([h for h in hr_list if h > 0]) / max(len([h for h in hr_list if h > 0]), 1), 2)
    avg_sleep = round(sum(sleep_list) / max(len(sleep_list), 1), 2)

    fitness_data = {
        'steps_avg_7d': avg_steps,
        'heart_rate_avg_7d': avg_hr,
        'sleep_hours_avg_7d': avg_sleep
    }
    return fitness_data

def process_sleep_bucket(date_str, sleep_response):
    """Process a sleep bucket from the segment data."""
    for bucket in sleep_response.get('bucket', []):
        bucket_date = datetime.fromtimestamp(int(bucket.get('startTimeMillis', 0)) / 1000).date().strftime("%Y-%m-%d")
        if bucket_date == date_str:
            total_sleep_ms = 0
            for dataset in bucket.get('dataset', []):
                for point in dataset.get('point', []):
                    if point['value'][0]['intVal'] in [1, 2, 3, 4]:  # valid sleep states
                        diff = int(point['endTimeMillis']) - int(point['startTimeMillis'])
                        total_sleep_ms += diff
            sleep_hours = round(total_sleep_ms / (1000 * 60 * 60), 2)
            return sleep_hours
    return 0 