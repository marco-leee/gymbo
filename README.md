# Exercise Analyser

Check out the doc for architecture and design details.

## Functional Requirements

1. Through mobile, user can set up camera to capture client performing exercise.
   1. Pose detection should be done in real-time with visual shown on the screen.
2. Detected pose and data should save to the database.
   1. App should be able to retrieve the data and show it to the user.
3. User should be able to see the history of the exercises.
4. Physio-assessment should be saved to the database.

google client id: 33626232293-v0b0jv1afj5h4ihej7e79cao1ina8gos.apps.googleusercontent.com
google client secret: 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

You may feel like it's a lot of work but you should be eyeing on attention free money after the system is up and running.

Three priorities:
1. Complete the login part
2. Async worker
   1. Complete the entire flow
   2. Allow to write to DB
   3. Allow to write to S3
   4. Allow to pull job from queue
3. Complete the exercise UI
   1. Display the exercise
   2. Display the data chart
4. Show all data at once, no need to separate organisation context
5. The rest
   1. Assessment
   2. Dashboard
   3. Settings
   4. Client management
   5. Organisation management
   6. Trainer management
   7. Admin management
   8. User management
   9. Role management
   10. Permission management
   11. Audit log
   12. Notification
   13. Email
   14. Invitation
6.  


QAfSpcl0Fgn-P9uu9GWiikdRM4ykOaoHhtMWs6BBp cloudflare gymbo api key auth

TODO: 

- [x] Fix the rotated video problem on production
- [x] Draw the angle as well on the video
- [x] Align the colour of the angle on the video and UI chart
- [x] Change video preview on run page back to having theme
- [ ] On analysis tab, update the chart so it displays all the data in one chart
- [ ] Tidy up the code
- [ ] Design subscription plan and integrate with stripe
- [ ] Spend 4 pomodoros on extracting reusable code and components. Put those in a separate repo

Right now, have a problem with plate blocking most of the human body. When passed to object detection, failed to detect the person. Also need tracking of the same person across frames.

Apply Kalman filter to the pose estimation
   1. OpenCV has a function to do this
   2. In some frames, the pose estimation is not detected so we need to use the previous frame to predict the current frame

1. Run object detection
2. Run weight detection
3. Update tracker and smoother
4. Get the most confident, largest area of person in frame
5. Filter weights by IoU with the person box and those in close proximity with the person box, with at least 50% overlap and in 30 pixels distance from all edges of the person box (let say). Merge all box with the person box.
6. Run segmentation on the merged box
   1. If person has segmented, move on
   2. If no, run Kalman filter to predict the person mask
7. Run pose estimation on the merged box
   1. If pose estimation is detected, move on
   2. If no, run Kalman filter to predict the pose keypoints

8. On first login, show the tour guide
9. First go to client page and add a client
10. Then go to session page and create a session
11. Navigate into the session page and start the session

Hi [First name] — saw your work with [detail] and thought you might be interested in gearing up your career with data driven coaching.

I’m building Gymbo, a free demo for PTs tired of eyeballing form and trying to remember what a client looked like 3 weeks ago.

Record a set on your phone → live pose overlay → review later with charts and session history. Makes it easier to back up your coaching with data, and clients tend to trust the process more when progress is visible over time.

Early stage — happy for you to try it and tell me what you think: https://gymbo.stixman.co

Cheers,
Marco