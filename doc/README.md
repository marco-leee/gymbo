# System Design

## Backend

### Real time processing

1. Users initiate a session for real time pose estimation analysis
2. Virtual room implemented on backend and check for the current capacity
   1. If full
      1. Assign a user with a token
      2. Add user to the waiting list in the room
      3. Response with the token
      4. On frontend, redirect to the waiting page with SSE to notify when a slot is available
   2. If not full
      1. Initiate the room from client side with socketio, stream video to the room
      2. On socket connection, join analyser to the room
      3. On analyser connection, start the pose estimation analysis
         1. On each frame, run analysis
         2. Stream video and metrics to the client
      4. On close, save the analysis result to the database and video to the storage

### Async processing

1. Users upload a video for pose estimation analysis
2. Backend creates a job and push to queue for processing
3. Response with the job object
4. Worker receive job from queue
5. Worker download the video from storage
6. Worker process the video
7. Worker save the analysis result to the database and video to the storage