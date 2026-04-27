The monitoring in itself is great. The designing need more work than what it is right. 

1. Need layered design for the monitoring system.
2. Input layer
   1. Camera - 
   2. Network - local, bluetooth, 
3. Perception layer - raw data from the models
   1. Human detection
   2. Pose estimation
   3. Segmentation
      1. Combine the segmentation with the pose estimation to get the full body pose
      2. Maybe we can further segment the body into different parts to get the pose of each part
         1. Head, should upper arm, lower arm, upper leg, lower leg, torso etc.
4. Sense making layer - processing the raw data to make sense of the data
   1. Rep counting
   2. Angle calculation analysis
   3. Form analysis
5. Orchestration layer 
   1. Workout flow transition - warm up, main workout, cool down
   2. state transition - idle, exercising, resting, next exercise
6. Feedback layer - feedback to the user
   1. UI
   2. Voice feedback through headphone
7. Storage layer - storage of the data

AI models

1. https://github.com/facebookresearch/sapiens/blob/main/lite/README.md
   1. Body part segmentation
2. https://chuoling.github.io/mediapipe/solutions/holistic.html
   1. Detect face landmarks
      1. Useful to detect stress level during training
   2. Pose estimation
      1. Same old
   3. Detect hand landmarks
      1. Useful to detect grip