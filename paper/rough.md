For right now — installing vLLM and pulling medgemma:4b — use hpg-turin. 

Neither step needs serious VRAM, L4's 22.5GB is plenty, and with 195 nodes available it'll start almost instantly instead of sitting in a priority queue.

Save hpg-b200 for later, specifically when we test whether the 30B+ models (Qwen3-VL-30B, InternVL3-38B, Lingshu-32B, HuatuoGPT-V-34B) actually fit on a single GPU — that's the only step that needs B200-class VRAM, 

and it's worth reserving that scarce resource just for that test rather than tying it up for routine setup work.


 Everything else is either vLLM (HuatuoGPT-V-34B, Lingshu-32B, Llava-Med-7B, Qwen3-VL-30B, InternVL3-38B) or a proprietary API (Gemini-2.5-Pro, GPT-5, Claude-4.5-Sonnet).

 Yes — on HiPerGator, QOS (Quality of Service) is the mechanism that caps resource usage per SLURM account, and so589980.ucf is Prof. Song Wang's group allocation — shared by everyone in the lab who has access to it, not just you.

So so589980.ucf's QOS sets a group-wide limit of 16 concurrent GPUs (any type, any partition) that applies across all labmates submitting jobs under that account at the same time. Right now something is pushing that pool to its cap — could be your own earlier jobs still cleaning up, or a labmate running something. It's not a per-user limit, it's shared.