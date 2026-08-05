1. Set up the local venv and confirm dependencies install cleanly
bash shell/install.sh
This is the thing that failed silently in my testing today (missing Pillow, openai) — worth confirming it installs clean now rather than discovering a requirements.txt gap once you're on a shared cluster.

2. Download the OmniBrainBench dataset
bash shell/download_data.sh
~734MB, one-time, doesn't need HiPerGator — can do it now on this machine.

3. Run the smoke test against whichever model you actually have an API key for
bash shell/smoke_test.sh GPT-5   # or whatever you have credentials for


This is the important one. Today's changes — 
- real KB loading, 
- the xml:lang fix,
- the required-path constructor, 
- the Wilson CI additions to analysis.py 
— have only been exercised with synthetic data and stubbed imports. 

They've never run through an actual live model call. The smoke test is ~150 API calls across all multi-phase cases at 3 questions/phase — cheap, fast, and it's the thing that will surface any integration bug (a KeyError in _phase_aggregate's new q_correct tracking, a mismatched field name, whatever) before you're burning HiPerGator allocation on it.

4. Check report.txt from that run for two specific things:
- The 95% CI / N columns actually populate and look sane (not None or a crash).
- KBAlign scores look meaningfully different from what stub-KB runs would have produced — confirms the real ontologies are actually in the loop, not silently falling back to something wrong.

5. Once HiPerGator lands: re-run install.sh + download_data.sh there (dataset caching is local per-machine), then move to run_proprietary.sh → run_opensource.sh → run_medical.sh for the real 12-model sweep.

Want me to walk through the smoke test with you now if you've got an API key handy, or are you waiting until HiPerGator to run anything at all?


<!-- ls -la /blue/so589980.ucf/$USER/
cd /blue/so589980.ucf/$USER/
pwd -->
-m 