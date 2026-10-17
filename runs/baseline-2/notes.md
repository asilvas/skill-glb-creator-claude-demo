# Forest warden (baseline-2)

- Built procedurally in Blender 5.2 headless (`build.py`): ~20k-poly hunched bipedal warden, braided bark-root limbs/torso (twisted strand tubes), faceted fractured stone plates (planar-cut icospheres) for pauldrons, bracers, chest, thigh/knee plates and feet, moss caps, ivory fungal shelves, curved ivory claws, amber emissive eyes, branching antlers.
- Materials: stone/bark/moss/ivory use the supplied albedo/normal/roughness maps (embedded in the GLB) with box/cylindrical UVs scaled to world size; eyes are emissive amber.
- Rig: 20-bone armature (root, hips, spine, chest, neck, head, shoulders, arms, hands, legs, feet), rigid vertex-group skinning; one clip "attack" (1.2 s): anticipation wind-up with torso counter-twist, overhead arc, forward impact slash around 0.63 s, follow-through and recovery to rest pose.
- Size/grounding: min Y = 0, height about 5.2 m including antlers (body about 4.5 m); facing +Z in glTF.
- Visual iterations: 3 render-and-review passes (front/side/back/wind-up/impact views). Fixes: pose axis signs (torso leaned the wrong way), arm slash trajectory, claws and antlers sized up, below-ground claw tips clamped to ground, antler height trimmed.
