#!/bin/bash
# Status of the v4 GPU campaign: queue, finished jobs, and result folders.
squeue -u $USER -o "%.10i %.28j %.9T %.10M %.22E" | sort
echo; sacct -S 2026-09-24 -u $USER --format=JobID%12,JobName%30,State,Elapsed,ExitCode -X | grep lumiv4
echo; ls -d results/lumiere_v4_*_image_* results/lumiere_v4_*_context_* results/lumiere_*_v4_nogate* 2>/dev/null
