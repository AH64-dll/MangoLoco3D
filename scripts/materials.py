"""Portable physically based materials for the Mango Loco can asset.

Interface: build_materials(root_path) -> dict with aluminum, label, tab,
liquid, dark_metal and condensation. Texture paths are resolved from the
project root and stored relative to Blender's // project path where possible.

The aluminum, label and condensation shaders are the enhanced production set:
two-scale brushed aluminum, inked print relief on the wrap, and a water-bead
glass shader used by scripts/condensation.py.
"""
from pathlib import Path


def _principled(name, color, metallic=0.0, roughness=0.35):
    import bpy

    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (-260, 40)
    out.location = (40, 40)
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    inputs = bsdf.inputs
    for key, value in (("Base Color", (*color, 1.0)), ("Metallic", metallic), ("Roughness", roughness)):
        if key in inputs:
            inputs[key].default_value = value
    return mat, bsdf


def _set_if_present(node, names, value):
    for name in names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return


def _make_aluminum():
    import bpy

    mat, bsdf = _principled("Mango Loco | brushed aluminum", (0.70, 0.73, 0.75), 1.0, 0.27)
    _set_if_present(bsdf, ("Anisotropic IOR Level", "Anisotropic"), 0.35)
    _set_if_present(bsdf, ("Specular IOR Level", "Specular"), 0.5)

    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-1100, -180)
    # Two stacked grain layers: a fine isotropic draw grain plus a faint
    # vertical brushing streak. Both feed one bump so aluminum never reads as
    # perfect chrome, while the silhouette stays clean.
    fine = nodes.new("ShaderNodeTexNoise")
    fine.location = (-860, -60)
    fine.inputs["Scale"].default_value = 5200.0
    fine.inputs["Detail"].default_value = 3.0
    fine.inputs["Roughness"].default_value = 0.68
    links.new(texcoord.outputs["Object"], fine.inputs["Vector"])

    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-860, -320)
    mapping.inputs["Scale"].default_value = (60.0, 60.0, 3.0)
    links.new(texcoord.outputs["Object"], mapping.inputs["Vector"])
    streak = nodes.new("ShaderNodeTexNoise")
    streak.location = (-620, -320)
    streak.inputs["Scale"].default_value = 1.0
    streak.inputs["Detail"].default_value = 2.0
    streak.inputs["Roughness"].default_value = 0.55
    links.new(mapping.outputs["Vector"], streak.inputs["Vector"])

    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.location = (-380, -180)
    mix.inputs["Factor"].default_value = 0.45
    links.new(fine.outputs["Fac"], mix.inputs["A"])
    links.new(streak.outputs["Fac"], mix.inputs["B"])

    bump = nodes.new("ShaderNodeBump")
    bump.location = (-180, -190)
    bump.inputs["Strength"].default_value = 0.045
    bump.inputs["Distance"].default_value = 0.000002
    links.new(mix.outputs["Result"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    # Very restrained directional roughness breakup keeps the aluminium from
    # reading as perfect chrome without imprinting a large-scale noise pattern.
    rough = nodes.new("ShaderNodeMapRange")
    rough.location = (-180, -380)
    rough.inputs["From Min"].default_value = 0.0
    rough.inputs["From Max"].default_value = 1.0
    rough.inputs["To Min"].default_value = 0.225
    rough.inputs["To Max"].default_value = 0.295
    links.new(mix.outputs["Result"], rough.inputs["Value"])
    links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    return mat


def _make_label(root_path):
    import bpy

    mat, bsdf = _principled("Mango Loco | printed turquoise wrap", (0.0, 0.42, 0.55), 0.0, 0.34)
    _set_if_present(bsdf, ("Coat Weight", "Clearcoat"), 0.22)
    _set_if_present(bsdf, ("Coat Roughness", "Clearcoat Roughness"), 0.14)

    image_path = Path(root_path) / "assets" / "textures" / "mango_loco_wrap.png"
    if image_path.is_file():
        image = bpy.data.images.load(str(image_path), check_existing=True)
        image.name = "Mango Loco | deprojected front / interim wrap"
        # The master .blend is saved under blender/, so this path stays portable
        # when that file is moved with the project folder.
        image.pack()
        image.filepath = "//../assets/textures/mango_loco_wrap.png"
        image_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        image_node.name = "Replace with licensed full-wrap art"
        image_node.label = "Front deprojection; rear intentionally blank"
        image_node.image = image
        image_node.interpolation = "Linear"
        image_node.extension = "REPEAT"
        image_node.location = (-570, 180)
        mat.node_tree.links.new(image_node.outputs["Color"], bsdf.inputs["Base Color"])

        # Ink relief: print darkness reads as a faint physical step under the
        # clearcoat, so the lettering and claw catch grazing light realistically.
        to_bw = mat.node_tree.nodes.new("ShaderNodeRGBToBW")
        to_bw.location = (-360, 400)
        mat.node_tree.links.new(image_node.outputs["Color"], to_bw.inputs["Color"])
        relief = mat.node_tree.nodes.new("ShaderNodeBump")
        relief.location = (-170, 400)
        relief.inputs["Strength"].default_value = 0.055
        relief.inputs["Distance"].default_value = 0.000004
        mat.node_tree.links.new(to_bw.outputs["Val"], relief.inputs["Height"])
        mat.node_tree.links.new(relief.outputs["Normal"], bsdf.inputs["Normal"])
    else:
        mat["artwork_status"] = "Interim color only: run scripts/prepare_artwork.py to build the front deprojection."
    return mat


def _make_condensation():
    """Water-bead glass for the condensation droplets. Noise varies the
    roughness microscopically so beads glint with slightly different focus."""
    import bpy

    mat, bsdf = _principled("Mango Loco | condensation droplet", (0.94, 0.985, 0.99), 0.0, 0.035)
    _set_if_present(bsdf, ("IOR",), 1.333)
    _set_if_present(bsdf, ("Transmission Weight", "Transmission"), 1.0)
    _set_if_present(bsdf, ("Coat Weight", "Clearcoat"), 0.5)
    _set_if_present(bsdf, ("Coat Roughness", "Clearcoat Roughness"), 0.03)

    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-620, -220)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-420, -220)
    noise.inputs["Scale"].default_value = 900.0
    noise.inputs["Detail"].default_value = 2.0
    links.new(texcoord.outputs["Object"], noise.inputs["Vector"])
    rough = nodes.new("ShaderNodeMapRange")
    rough.location = (-220, -220)
    rough.inputs["To Min"].default_value = 0.015
    rough.inputs["To Max"].default_value = 0.06
    links.new(noise.outputs["Fac"], rough.inputs["Value"])
    links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    mat["note"] = "Water bead shader for CAN_Condensation; regenerate beads with scripts/condensation.py."
    return mat


def _make_liquid():
    import bpy

    mat, bsdf = _principled("Mango Loco | mango juice", (0.95, 0.24, 0.018), 0.0, 0.19)
    _set_if_present(bsdf, ("IOR",), 1.36)
    _set_if_present(bsdf, ("Transmission Weight", "Transmission"), 0.16)
    _set_if_present(bsdf, ("Subsurface Weight", "Subsurface"), 0.035)
    _set_if_present(bsdf, ("Subsurface Radius",), (0.8, 0.38, 0.08))

    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    absorption = nodes.new("ShaderNodeVolumeAbsorption")
    absorption.location = (-230, -210)
    absorption.inputs["Color"].default_value = (0.96, 0.39, 0.075, 1.0)
    absorption.inputs["Density"].default_value = 1.05
    output = next(node for node in nodes if node.type == "OUTPUT_MATERIAL")
    links.new(absorption.outputs["Volume"], output.inputs["Volume"])
    # No emission is used. A subtle transmission component and volume
    # absorption make thick juice darker while preserving bright edge glints.
    mat["note"] = "Orange juice shader with restrained transmission and absorption; no emission."
    return mat


def build_materials(root_path):
    """Create and return the shared material set used by geometry modules."""
    import bpy  # Keep bpy import local so the source can be inspected outside Blender.

    aluminum = _make_aluminum()
    label = _make_label(root_path)
    tab, tab_bsdf = _principled("Mango Loco | turquoise pull tab", (0.005, 0.44, 0.59), 0.72, 0.24)
    _set_if_present(tab_bsdf, ("Anisotropic IOR Level", "Anisotropic"), 0.18)
    liquid = _make_liquid()
    dark_metal, dark_bsdf = _principled("Mango Loco | dark stamped metal", (0.045, 0.055, 0.058), 0.86, 0.31)
    _set_if_present(dark_bsdf, ("Anisotropic IOR Level", "Anisotropic"), 0.12)
    condensation = _make_condensation()
    return {
        "aluminum": aluminum,
        "label": label,
        "tab": tab,
        "liquid": liquid,
        "dark_metal": dark_metal,
        "condensation": condensation,
    }
