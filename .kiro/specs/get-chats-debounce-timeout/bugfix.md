# Bugfix Requirements Document

## Introduction

After creating a chat with document upload (POST /chats) in the RFQ screen, the app navigates through a processing screen and then to the landing screen, which immediately calls GET /chats to populate the chat grid. This GET /chats call frequently times out because backend document chunking is still running asynchronously, causing the correlated subqueries in `get_chats_paginated` to be slow or the endpoint to be unresponsive during heavy processing. The current 30-second axios timeout causes the UI to hang for too long before retrying, and there is no delay between chat creation and the first GET /chats call to allow the backend to settle.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a chat is created via POST /chats with document upload and the app navigates to the landing screen THEN the system immediately invokes GET /chats without any delay, hitting the backend while document chunking is still in progress, causing frequent timeouts

1.2 WHEN GET /chats times out THEN the system waits the full 30-second default axios timeout before detecting the failure and retrying, causing the user to experience long unresponsive periods

1.3 WHEN GET /chats times out and retries occur THEN each retry also uses the 30-second timeout, meaning the user could wait up to 90 seconds (3 retries × 30s) before seeing an error or successful response

### Expected Behavior (Correct)

2.1 WHEN a chat is created via POST /chats with document upload and the app navigates to the landing screen THEN the system SHALL wait 5 seconds (debounce delay) before invoking the first GET /chats call, giving the backend time to complete initial processing

2.2 WHEN GET /chats is called after chat creation THEN the system SHALL use a dedicated axios client with a 10-second timeout (instead of the default 30-second timeout) so that timeout failures are detected quickly and retries happen sooner

2.3 WHEN GET /chats times out and retries occur with the shorter timeout THEN the total maximum wait time SHALL be reduced (3 retries × 10s = 30s worst case instead of 90s), providing faster feedback to the user

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the landing screen is loaded directly (not after a fresh chat creation) THEN the system SHALL CONTINUE TO call GET /chats immediately without any debounce delay

3.2 WHEN other API calls are made (POST /chats, GET /chats/{id}, DELETE, etc.) THEN the system SHALL CONTINUE TO use the default 30-second timeout via the existing apiClient

3.3 WHEN GET /chats is called and the backend responds within the timeout period THEN the system SHALL CONTINUE TO display the chat grid correctly with all chat summaries

3.4 WHEN GET /chats times out THEN the existing retry logic (MAX_RETRIES = 3) SHALL CONTINUE TO function, retrying on timeout errors
