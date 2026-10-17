# Benchmark protocol

Task: recreate the "forest warden" monster (assets/reference.png) as a textured, skinned, animated GLB,
using the prepared PBR maps in assets/textures/. Same task text for both arms; only the PIPELINE
paragraph differs.

- Arm A (baseline): Blender 5.2 headless CLI (--background --python), 4 parallel subagents (runs/baseline-1..4).
- Arm B (skill): glb-creator skill (private copy per agent with deps preinstalled), 4 parallel subagents (runs/skill-1..4).
- Subagent model: sonnet (same in both arms). Host: Windows 11, Ryzen 9 9950X3D (32 threads), RTX 5090, Bun 1.4.4.
- Agents may not read other repos/directories (anti-contamination: the monster recipe exists in sibling repos).
- Metrics per run: total tokens (from agent telemetry), wall-clock duration, tool-call count where available,
  deliverable validity (Khronos errors), triangles, texture/clip/joint inventory, and a visual quality score
  (1-10, judged against the reference from a uniform contact sheet rendered after the fact).
- Both arms run 4-at-once, so machine contention is comparable. Confounds: different renderers,
  model nondeterminism across runs.
