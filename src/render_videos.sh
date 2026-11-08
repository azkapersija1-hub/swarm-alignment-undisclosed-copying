#!/bin/bash
cd "/d/kerjaan baru/SWARM_ALIGNMENT_2026_FINAL" || exit 1
export SWARM_DATASET=tls SWARM_METRICS_TAG=_alllabels
PY="py -3.12 -I -B -X utf8"
rm -f 08_VISUAL_EVIDENCE/video_documentation/*_fast.mp4
$PY src/animate_performance.py > 06_RAW_RESULTS/video_performance.log 2>&1
$PY src/animate_process.py > 06_RAW_RESULTS/video_process.log 2>&1
echo VIDEOS_DONE > 06_RAW_RESULTS/videos.done
