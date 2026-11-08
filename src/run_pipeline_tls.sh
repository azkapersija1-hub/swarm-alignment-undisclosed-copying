#!/bin/bash
# Unattended pipeline for the TLS dataset. Each stage logs to 06_RAW_RESULTS/pipeline_tls/<stage>.log and writes a .done marker.
# Safe to re-run: finished stages are skipped (their .done marker exists).
cd "/d/kerjaan baru/SWARM_ALIGNMENT_2026_FINAL" || exit 1
export SWARM_DATASET=tls
LOGDIR=06_RAW_RESULTS/pipeline_tls
mkdir -p "$LOGDIR"
PY="py -3.12 -I -B -X utf8"

stage() {  # name, command...
  name="$1"; shift
  if [ -f "$LOGDIR/$name.done" ]; then echo "skip $name"; return 0; fi
  echo "[$(date +%H:%M:%S)] start $name" | tee -a "$LOGDIR/pipeline.log"
  if "$@" > "$LOGDIR/$name.log" 2>&1; then
    touch "$LOGDIR/$name.done"; echo "[$(date +%H:%M:%S)] done  $name" | tee -a "$LOGDIR/pipeline.log"
  else
    echo "[$(date +%H:%M:%S)] FAILED $name (see $LOGDIR/$name.log)" | tee -a "$LOGDIR/pipeline.log"
  fi
}

stage 1_score_monitors $PY src/compute_scores.py 06_RAW_RESULTS/llm_runs_tls
stage 2_evaluate $PY src/evaluate.py
stage 3_tracks_t1_t3 $PY src/tracks_t1_t3.py
stage 4_track2_networks $PY src/track2_networks.py gemma4:31b-cloud 20
echo "[$(date +%H:%M:%S)] PIPELINE FINISHED" | tee -a "$LOGDIR/pipeline.log"
