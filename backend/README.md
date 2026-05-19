- [x] import test video
- [x] Run object detection on each frame <- yolov26
- [x] Run pose estimation and segmentation on it <- mediapipe and yolov26
- [x] Save the result to the file
- [x] Develop a reps, sets counter
- [x] Combine pose and seg results to segmentise the body

> ![NOTE] For next pick up
>
> - [ ] Tidy up the code so that pipeline works with video
> - [ ] The back analysis one works okay. Still need to improve the line drawn on the back, now it's connected to the reference line
> - [ ] Set counter is not okay. Not accurate and also failed to separate the sets properly. Focus on rep counting first. Not a priority for now. Do back and angles first
> - [ ] Force on analysis layer first. Forget feedback for now
>
> - [ ] Take a video from path
> - [ ] Switch from inference to stream
> - [ ] Calculate the angles of interest
> - [ ] Calculate the back straightness / hinges monitoring, normalise it
> - [ ] Design the schema for both angle and back straightness / hinges monitoring
> - [ ] Draw on frame
> - [ ] Save the results to the DB

Flow

1. Download the video
2. Get the frames
3. Run the entire perception pipeline
4. Run the entire analysis pipeline
   1. Count the sets and reps
   2. For each set, calculate the angle of interest
   3. Back straightness / hinges monitoring
5. Run the feedback pipeline
6. Format the results
7. Save to DB

For each frame in video
    Run object detection
    Filter to only person boxes
    Get best person box by confidence score, largest area and ratio of bounding box to frame (at least 50% of the frame)
    If no person box
        Write the frame to the output video
        Continue to the next frame
    Crop the frame to the person box
    Run pose estimation
    Run segmentation
    Run joint angles calculation
        Calculate all the angles of interest
    Run set and reps counter
        Keep a list of float of the joint
        Pass the signal joint keypoint to the set and reps counter
        Append to the float list
        Detect 
    Run back straightness / hinges monitoring
    Run feedback
        Placeholder for now
    Save the results to context

Save the results to the output video
Save the results to the DB


Need a list of analysis, measurement. 

Back analysis:
    1. Loosely fitted shirt lowers accuracy

## Context

Everything below is **session context**: who is training, what they are doing, how input arrives, what the perception stack produces, what we measure, what we tell the user, and what we persist.

### Who and what

- **User** — Identity and preferences that apply across sessions (accounts, units, thresholds when those exist).
- **Exercise** — The movement being analysed (exercise type, rules for reps/segments, cues specific to that lift).
- **Sets** — Planned or inferred structure within the session (set index, boundaries, optional target reps). The counter and angle logic run **per set** where relevant.

### Input

How frames enter the pipeline (same perception stack applies once frames are normalised):

- **Video file** — Offline clip; typical batch path (download → extract frames → run pipeline).
  - **Camera view** — Where the camera is relative to the athlete (e.g. side vs front) affects which joints and hinge angles are trustworthy; should be captured as metadata where possible.
- **Live stream** — Real-time or chunked stream; latency and buffering constraints differ from files.
  - **Camera view** — Same as above; important for reproducible angles and back/hinge checks.

### Perceptions

Model outputs consumed by measurements (not necessarily all used on every path):

| Layer | Role |
|--------|------|
| **Providers** | **YOLO** (e.g. v26 pose / detection), **Mediapipe** (pose, landmarks, segmentation helpers depending on wiring). |
| **Object detection** | Scene objects (equipment, person boxes) when the pipeline uses them for ROI or cues. |
| **Pose estimation** | Keypoints / skeleton per frame for angles and kinematics. |
| **Segmentation** | Instance or body-region masks when combining pose + segmentation for overlays or torso/back analysis. |

### Measurements

Derived from perceptions + exercise rules:

- **Reps and sets** — Boundary detection and counting from pose trajectories or defined phases.
- **Joint angles** — Angles of interest **per set** (exercise-dependent definitions).
- **Back straightness / hinge monitoring** — Torso vs hip hinge signals; clothing (e.g. loose shirt) can reduce reliability (see back analysis notes above).

### Feedback

Interpretation surfaced to the user: qualitative or scored cues tied to reps/sets (form warnings, completions, summaries). Depends on measurements and optionally raw perception artefacts.

### Output (persist to DB)

Artifacts and aggregates to store for history, dashboards, and retraining/debug:

- **Updated exercises** — Session or profile updates reflecting what was logged.
- **Annotated video** — Rendered overlays (pose, segmentation, angles, rep markers).
- **Raw perception results** — Detections, keypoints, masks, per-frame payloads as stored (schema TBD).
- **Measurement results** — Reps, sets, angles, hinge/back metrics aligned to time or rep index.
- **Feedback results** — What was shown or generated as coaching output for audit and UX iteration.

