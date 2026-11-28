# Failure analysis, MTC 2F-140 5 cm cylinder, 50 trials (simulation only)

Withdrawn (2026-11-28): the 5 cm cylinder placement and toppling numbers below (including 12/20, 27/50, 25/50 and 4/18 with 13 topples) are not a measure of the pipeline. With no robot, Gazebo Harmonic with Bullet-featherstone topples a slightly tilted cylinder on its own: 60 of 60 trials started at 5 to 15 degrees fell, 0 of 20 at 2 degrees, although this shape should tip only past about 32 degrees. The results have not been re-measured.

Earlier scoring caveat (2026-11-26): the 12/20, 27/50 and 25/50 results read the object pose 2 s after MTC reported its result. One later trial wobbled and rolled off the table after that, so these numbers may be optimistic. A later 20-trial run with a 12 s wait, at a different place point (y 0.10), scored 4 successes in 18 executed trials with 13 toppled (trials 19 and 20 timed out), so treat the 2 s figures as likely too high; the y 0.20 setup has not been rerun with the longer wait.

Source: testing/_out/mtc_140_cyl5_n50.csv (run 2026-11-23, domain 91, padding 0.0 via overlay). Success means final xy error within 20 mm. All 50 trials executed, and every trial's retry wrapper ended "MTC retry: SUCCESS", so MTC reported success on all 50: the failures are execution outcomes, not planning failures.

## Counts (23 failures of 50)
| Class (from the notes column) | Trials | Count |
|---|---|---|
| Toppled, final xy 61 to 258 mm | 1, 5, 14, 15, 19, 28, 43, 47 | 8 |
| Upright but outside 20 mm, 20 to 27 mm ("near", within 30 mm) | 2, 3, 7, 10, 27, 39, 46 | 7 |
| Upright, 32 to 48 mm | 8, 13, 21, 33, 34, 35, 42 | 7 |
| False success: object unmoved, 200 mm from the target | 24 | 1 |

Within 30 mm: 34/50, so 7 of the 23 failures are near misses (20 to 27 mm), one of them at 20.3 mm.

## Error distribution
- All 50 trials, xy error: median 17.1 mm, 25th percentile 11.1 mm, 75th percentile 38.1 mm, maximum 258 mm.
- 27 successes: mean error 10.4 mm, maximum 18.1 mm, mean signed offset dx +1.4 mm, dy -1.5 mm (no systematic bias).
- 23 failures, sorted (mm): 20, 22, 23, 23, 24, 27, 27, 32, 34, 37, 38, 40, 47, 48, 61, 90, 132, 179, 190, 200, 210, 213, 258.
- Lift height: median lifted_m 0.129 for failures vs 0.130 for successes, so failures are not explained by a failed lift; the objects were carried and then lost or displaced at release or settling.

## What this supports and what it does not
- Supported by the CSV: about a third of failures (8) are toppled objects, and about 60% (14) are upright objects landing 20 to 48 mm off target.
- Not confirmed: the cause of the topples and of the 20 to 48 mm offsets (slip in the grasp, release drop, rolling after release, or place-pose error). The notes column does not separate these; the frame review below covers only the 8 toppled trials and trial 24, not the 14 upright misses.
- The single false success (trial 24) is the only trial where the grasp apparently never moved the object.

## Frame review (testing/_out/frames_n50, viewed 2026-11-23)
Each trial has two PNG contact sheets (the "FAIL" sheet and the "FAIL_tail" sheet), each a 4 by 6 grid of 24 camera frames labelled with seconds since recording start. There are no numbered frame files, so times below are the on-image seconds. I viewed the tail sheet for all 8 toppled trials and both sheets for trial 24 and trial 14.

### Toppled trials (1, 5, 14, 15, 19, 28, 43, 47)
Same sequence in every sheet I viewed:
1. The arm reaches the cylinder from above, the pads close on it and it is lifted and carried a short distance to the place point, which is further up the table slab than the pick point (for example trial 1: closed on it by about 25 s, carried 27.0 to 30.0 s; trial 15: carried 29.7 to 33.3 s).
2. The cylinder is released at the place point, near the far edge of the light table slab, and the arm leaves. In the first frames after release the cylinder is standing upright (trial 1 at 31.2 s, trial 5 at 34.5 s, trial 19 at 37.2 s, trial 28 at 35.1 s, trial 43 at 34.2 s).
3. After the arm has left the view and is back at its home pose, the cylinder tips over or rolls on its own: trial 1 tilted in the last two frames (about 36 s), trial 5 tilted in the last two frames (the sheet ends at about 36.9 s), trial 15 gone to the table edge by 41.4 s, trial 19 lying at 40.2 s, trial 28 tilting 36.9 s and lying at 38.1 s, trial 43 tilting at 36.0 s and lying at 36.6 s.
Not seen in any of these sheets: a knock-over during the approach, finger slip during the lift, or a drop in flight. The cylinder is held through the whole carry.

### What the frames do not show
- Why it tips after release. The upright cylinder appears to stand at the table edge and then fall; candidates (release too high, finger motion on release, a tilted placement, placement point too close to the edge) cannot be separated from these frames. Not confirmed.
- Trial 14: the cylinder is released by about 39 s and is upright at 39.3 to 41.7 s, then lies near the far edge from 43.5 s; same pattern as above.
- Trial 47: the final frame (39.0 s) still shows the cylinder standing at the far edge, so the sheet does not show the topple that the CSV notes record (final xy 179 mm TOPPLED). It may have tipped after the recording ended. Not confirmed.
- The sheets only start about 20 to 28 s into each trial, so the pick approach itself is not visible for the toppled trials (trial 14's FAIL sheet starts at 0 s and shows the whole run).

### Trial 24 (false success)
Both sheets show the red cylinder at the same place in every frame from 0 s to 78 s. The arm moves (a raised pose near the top of the frame around 50 to 75 s, gripper open) but never comes down to the cylinder, and it returns to home. So MTC reported success for a pick that never touched the object; the frames show no grasp attempt at the cylinder. Why the executed motion went elsewhere is not confirmed.

### Take-away, limited to what the frames support
In 8 of 8 toppled trials the object is grasped and carried correctly and falls over after release, so the failure is in the place and release step, not the grasp. This is observation of 8 sheets, not a measured cause.
