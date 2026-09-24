


<!-- ls -la /blue/so589980.ucf/$USER/
cd /blue/so589980.ucf/$USER/
pwd -->
-m 


blue_quota -  check storage

sinfo -o "%P %G %D" | grep -i gpu - check GPU



squeue -j 38868089 -o "%L %l %M" - check time



squeue -u ta117847.ucf - check status 
squeue -A so589980.ucf -o "%.10i %.12j %.10u %.10T %.6D %.12b %.10M"


claude --resume
claude --continue/bt


## Benchmark 

Hi [Professor's name],

Attached is the review file for the LUMIERE causal-chain dataset: lumiere_chain_review.html (~2.5MB, self-contained — no install needed).

How to open it:
1. Save the attachment to your computer.
2. Double-click it (or drag it into a browser window). It opens in Chrome, Firefox, Safari, or Edge — no login, no account, no internet connection needed once it's open.

What it is:
269 draft multiple-choice questions across 54 real GBM patients, spanning 5 clinical phases (imaging → lesion tracking → diagnosis → prognosis → treatment). Each question was auto-drafted from real patient data (imaging, RANO response ratings, survival, treatment) and needs a clinical accuracy check before it goes into the dataset.

How to review each item:
- The left panel shows the relevant MRI slice(s) and the underlying facts the question was drafted from.
- The right panel shows the drafted question, answer choices (the correct one is highlighted), and the reasoning for why the other choices are wrong.
- You can edit the question text or any answer choice directly, and change which option is marked correct, before saving.
- Three actions per item:
  - Approve — the question is accurate as-is.
  - Save edits & approve — you changed something, then approve.
  - Reject — the question is unusable (a short reason is required in the notes field).
- Items flagged with a ⚠ banner are ones the drafting process marked as needing your judgment call (ambiguous case or a low-confidence distractor) — worth a closer look.
- Fill in your name once at the top (Reviewer field) — it's saved with your decisions.

Progress and finishing up:
- Your progress saves automatically in your browser as you go — you can close it and come back later on the same computer/browser without losing anything.
- When you're done (or want to send a partial progress checkpoint), click "Download review file" at the top. This saves an updated copy of the same file with your decisions included — please send that file back the same way you received this one (email/reply).
- If you switch to a different computer partway through, use "Load review file…" to pick up your last downloaded copy instead of starting over.

No need to review everything in one sitting — take breaks anytime, just download before you stop for the day if you're on a shared or different machine next time.

Let me know if anything looks off or the file won't open — happy to fix it.


-----


Queue status:

squeue -u $USER -o "%.10i %.28j %.8T %.10M %.10l %R"

Recent job history (finished and running):

sacct -u $USER -S $(date -d '2 days ago' +%F) -X --format=JobID%12,JobName%30,State%12,Elapsed,End -n

Live progress of a running job (swap in the job name):

tail -f logs/lumigcabl_MedGemma-4B_43118917.out

To refresh the queue every 30 seconds:

watch -n 30 'squeue -u $USER -o "%.10i %.28j %.8T %.10M %R"'


----


squeue -A so589980.ucf -o "%.10i %.10u %.28j %.8T %.10M %.10l %.10b %R"

The %b column shows the GPUs each job requested, which is what matters for the cap.

Group usage against the account limits:

sshare -A so589980.ucf -l

If HiPerGator has the RC helper loaded, this shows group GPU and CPU usage and limits:

module load ufrc && slurmInfo so589980.ucf

The account name is so589980.ucf, not so589980.

Add -t RUNNING to squeue to hide pending jobs. Add -h | wc -l to count them.
