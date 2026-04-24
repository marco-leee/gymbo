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