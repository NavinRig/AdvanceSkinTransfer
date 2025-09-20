''' 
Navin Kamal
Advance Skin Transfer Tool.v01
Free Licence
Dont forget to give credit :)
'''

import maya.cmds as cmds
import json

# Utility Functions
def get_skin_cluster(mesh):
    history = cmds.listHistory(mesh)
    skins = cmds.ls(history, type="skinCluster")
    return skins[0] if skins else None

def transfer_skin_weights(source, target):
    if not cmds.objExists(source) or not cmds.objExists(target):
        cmds.warning("Source or target mesh does not exist.")
        return

    src_skin = get_skin_cluster(source)
    if not src_skin:
        cmds.warning("Source mesh has no skinCluster.")
        return

    tgt_skin = get_skin_cluster(target)
    if not tgt_skin:
        joints = cmds.skinCluster(src_skin, q=True, inf=True)
        tgt_skin = cmds.skinCluster(joints, target, toSelectedBones=True)[0]

    cmds.copySkinWeights(
        sourceSkin=src_skin,
        destinationSkin=tgt_skin,
        noMirror=True,
        surfaceAssociation="closestPoint",
        influenceAssociation="closestJoint"
    )
    cmds.inViewMessage(amg=f"<hl>Skin weights transferred:</hl> {source} → {target}", pos='midCenter', fade=True)

def export_skin_data(mesh):
    if not mesh:
        sel = cmds.ls(sl=True)
        if not sel:
            cmds.warning("Please select a mesh or enter one in Source field.")
            return
        mesh = sel[0]

    skin = get_skin_cluster(mesh)
    if not skin:
        cmds.warning("Selected mesh has no skinCluster.")
        return

    joints = cmds.skinCluster(skin, q=True, inf=True)
    weights = []
    vtx_count = cmds.polyEvaluate(mesh, vertex=True)
    for i in range(vtx_count):
        per_joint_weights = []
        for j, joint in enumerate(joints):
            w = cmds.getAttr(f"{skin}.weightList[{i}].weights[{j}]")
            per_joint_weights.append(w)
        weights.append(per_joint_weights)

    file_path = cmds.fileDialog2(fileMode=0, caption="Export Skin Data", fileFilter="JSON Files (*.json)")
    if not file_path:
        return
    with open(file_path[0], "w") as f:
        json.dump({"joints": joints, "weights": weights}, f, indent=4)
    cmds.inViewMessage(amg=f"<hl>Skin data exported:</hl> {file_path[0]}", pos='midCenter', fade=True)

def import_skin_data(mesh):
    if not mesh:
        sel = cmds.ls(sl=True)
        if not sel:
            cmds.warning("Please select a mesh or enter one in Target field.")
            return
        mesh = sel[0]

    file_path = cmds.fileDialog2(fileMode=1, caption="Import Skin Data", fileFilter="JSON Files (*.json)")
    if not file_path:
        return

    with open(file_path[0], "r") as f:
        data = json.load(f)

    joints = data["joints"]
    weights = data["weights"]

    missing = [j for j in joints if not cmds.objExists(j)]
    for j in missing:
        cmds.joint(name=j, p=(0, 0, 0))

    tgt_skin = get_skin_cluster(mesh)
    if not tgt_skin:
        tgt_skin = cmds.skinCluster(joints, mesh, toSelectedBones=True)[0]

    for i, w_list in enumerate(weights):
        for j, w in enumerate(w_list):
            try:
                cmds.setAttr(f"{tgt_skin}.weightList[{i}].weights[{j}]", w)
            except:
                pass

    cmds.inViewMessage(amg=f"<hl>Skin data imported:</hl> {file_path[0]}", pos='midCenter', fade=True)

# SkinCluster Management
def select_skincluster_of_selected():
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning("Please select a mesh.")
        return
    skins = []
    for s in sel:
        sc = get_skin_cluster(s)
        if sc:
            skins.append(sc)
    if skins:
        cmds.select(skins, r=True)
        cmds.inViewMessage(amg=f"<hl>Selected SkinClusters:</hl> {', '.join(skins)}", pos='midCenter', fade=True)
    else:
        cmds.warning("No skinCluster found on selected mesh(es).")

def select_all_skinclusters_in_scene():
    skins = cmds.ls(type="skinCluster")
    if skins:
        cmds.select(skins, r=True)
        cmds.inViewMessage(amg=f"<hl>All SkinClusters selected:</hl> {len(skins)} found", pos='midCenter', fade=True)
    else:
        cmds.warning("No skinClusters found in the scene.")

def disable_all_skinclusters():
    skins = cmds.ls(type="skinCluster")
    for sc in skins:
        cmds.setAttr(f"{sc}.envelope", 0)
    cmds.inViewMessage(amg="<hl>All skinClusters disabled</hl>", pos='midCenter', fade=True)

def enable_all_skinclusters():
    skins = cmds.ls(type="skinCluster")
    for sc in skins:
        cmds.setAttr(f"{sc}.envelope", 1)
    cmds.inViewMessage(amg="<hl>All skinClusters enabled</hl>", pos='midCenter', fade=True)

# Joint Section Functions
def select_skin_joints():
    sel = cmds.ls(sl=True)
    joints = []
    for s in sel:
        if cmds.nodeType(s) == "skinCluster":
            joints += cmds.skinCluster(s, q=True, inf=True)
        else:
            skin = get_skin_cluster(s)
            if skin:
                joints += cmds.skinCluster(skin, q=True, inf=True)
    joints = list(set(joints))
    if joints:
        cmds.select(joints, r=True)
    else:
        cmds.warning("No skin joints found in selection.")

def select_influence_joints():
    sel = cmds.ls(sl=True)
    joints = []
    for s in sel:
        skin = get_skin_cluster(s) if cmds.nodeType(s) != "skinCluster" else s
        if skin:
            all_joints = cmds.skinCluster(skin, q=True, inf=True)
            influenced_joints = []
            vtx_count = cmds.polyEvaluate(s, vertex=True) if cmds.nodeType(s) != "skinCluster" else 0
            for j, joint in enumerate(all_joints):
                total_weight = sum([cmds.getAttr(f"{skin}.weightList[{i}].weights[{j}]") for i in range(vtx_count)])
                if total_weight > 0:
                    influenced_joints.append(joint)
            joints += influenced_joints
    joints = list(set(joints))
    if joints:
        cmds.select(joints, r=True)
    else:
        cmds.warning("No influence joints found.")

def select_end_joints():
    sel = cmds.ls(sl=True)
    end_joints = []
    for s in sel:
        skin_joints = cmds.skinCluster(s, q=True, inf=True) if cmds.nodeType(s) != "joint" else [s]
        for j in skin_joints:
            if not cmds.listRelatives(j, c=True, type="joint"):
                end_joints.append(j)
    if end_joints:
        cmds.select(end_joints, r=True)
    else:
        cmds.warning("No end joints found.")

def select_non_influence_joints():
    sel = cmds.ls(sl=True)
    non_influencing_joints = []
    for s in sel:
        skin = get_skin_cluster(s) if cmds.nodeType(s) != "skinCluster" else s
        if skin:
            all_joints = cmds.skinCluster(skin, q=True, inf=True)
            vtx_count = cmds.polyEvaluate(s, vertex=True) if cmds.nodeType(s) != "skinCluster" else 0
            for j, joint in enumerate(all_joints):
                total_weight = sum([cmds.getAttr(f"{skin}.weightList[{i}].weights[{j}]") for i in range(vtx_count)])
                if total_weight == 0:
                    non_influencing_joints.append(joint)
    non_influencing_joints = list(set(non_influencing_joints))
    if non_influencing_joints:
        cmds.select(non_influencing_joints, r=True)
    else:
        cmds.warning("No non-influence joints found.")

def remove_non_influence_joints():
    sel = cmds.ls(sl=True)
    for s in sel:
        skin = get_skin_cluster(s) if cmds.nodeType(s) != "skinCluster" else s
        if skin:
            all_joints = cmds.skinCluster(skin, q=True, inf=True)
            vtx_count = cmds.polyEvaluate(s, vertex=True) if cmds.nodeType(s) != "skinCluster" else 0
            for j, joint in enumerate(all_joints):
                total_weight = sum([cmds.getAttr(f"{skin}.weightList[{i}].weights[{j}]") for i in range(vtx_count)])
                if total_weight == 0 and cmds.objExists(joint):
                    cmds.skinCluster(skin, e=True, ri=joint)

# UI
def show_skin_transfer_ui():
    if cmds.window("skinTransferWin", exists=True):
        cmds.deleteUI("skinTransferWin")

    window = cmds.window("skinTransferWin", title="NvN Tools", widthHeight=(400, 600))
    main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=6)
    
    # Header
    cmds.text(label="Advance Skin Transfer Tool.v01", h=30, w=400, fn="boldLabelFont", bgc=(0.188, 0.627, 0.627))
    cmds.separator(height=10, style='none')

    # SOURCE/TARGET SECTION
    sourceTarget_frame = cmds.frameLayout(label="Add Source and Target", collapsable=True, collapse=True, marginHeight=10)
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnWidth2=(100, 280), columnAttach2=("both", "both"))
    src_btn = cmds.button(label="Add Source")
    src_field = cmds.textField(text="")
    cmds.setParent("..")
    src_skin_label = cmds.text(label="SkinCluster: (none)", align="left")

    cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnWidth2=(100, 280), columnAttach2=("both", "both"))
    tgt_btn = cmds.button(label="Add Target")
    tgt_field = cmds.textField(text="")
    cmds.setParent("..")
    tgt_skin_label = cmds.text(label="SkinCluster: (none)", align="left")
    cmds.setParent("..")

    # Auto-clear placeholder text
    def clear_placeholder(field, default_text, *args):
        current_text = cmds.textField(field, q=True, text=True)
        if current_text == default_text:
            cmds.textField(field, e=True, text="", bgc=(0.2, 0.2, 0.2))

    cmds.textField(src_field, e=True, cc=lambda *args: clear_placeholder(src_field, "Source Mesh"))
    cmds.textField(tgt_field, e=True, cc=lambda *args: clear_placeholder(tgt_field, "Target Mesh"))

    def set_source(*args):
        sel = cmds.ls(sl=True)
        if sel:
            cmds.textField(src_field, e=True, text=", ".join(sel))
            skins = [get_skin_cluster(s) for s in sel if get_skin_cluster(s)]
            cmds.text(src_skin_label, e=True,
                      label=f"SkinCluster: {', '.join(skins)}" if skins else "SkinCluster: None")

    def set_target(*args):
        sel = cmds.ls(sl=True)
        if sel:
            cmds.textField(tgt_field, e=True, text=", ".join(sel))
            skins = [get_skin_cluster(s) for s in sel if get_skin_cluster(s)]
            cmds.text(tgt_skin_label, e=True,
                      label=f"SkinCluster: {', '.join(skins)}" if skins else "SkinCluster: None")

    cmds.button(src_btn, e=True, c=set_source)
    cmds.button(tgt_btn, e=True, c=set_target)

    cmds.separator(h=20, style="in")

    # TRANSFER SECTION
    transfer_frame = cmds.frameLayout(label="Transfer Skin Weights", collapsable=True, collapse=False, marginHeight=10)
    cmds.rowLayout(numberOfColumns=3, adjustableColumn=(1,2,3), columnWidth3=(130, 130, 130))
    cmds.button(label="One to One", h=30 ,c=lambda *args: transfer_skin_weights(cmds.textField(src_field, q=True, text=True),
                                                                         cmds.textField(tgt_field, q=True, text=True)))
    cmds.button(label="One to Many", h=30 ,c=lambda *args: [transfer_skin_weights(cmds.textField(src_field, q=True, text=True), t)
                                                      for t in cmds.ls(sl=True)])
    cmds.button(label="Many to One", h=30 ,c=lambda *args: [transfer_skin_weights(s,
                                                                           cmds.textField(tgt_field, q=True, text=True))
                                                      for s in cmds.ls(sl=True)])
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.separator(h=20, style="in")


    # Joint Section
    joint_frame = cmds.frameLayout(label="Joints Selection & Management", collapsable=True, collapse=False, marginHeight=10)
    cmds.rowLayout(numberOfColumns=3, adjustableColumn=(1,2,3), columnWidth3=(130, 130, 130))
    cmds.button(label="Skin joints", h=30 ,c=lambda *args: select_skin_joints())
    cmds.button(label="Influence joints", h=30 ,c=lambda *args: select_influence_joints())
    cmds.button(label="End joints", h=30 ,c=lambda *args: select_end_joints())
    cmds.setParent("..")
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=(1,2), columnWidth2=(200, 200))
    cmds.button(label="NonInfluence joints", h=30 ,c=lambda *args: select_non_influence_joints())
    cmds.button(label="Remove NonInfluence joints", h=30 ,c=lambda *args: remove_non_influence_joints())
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.separator(h=20, style="in")

    # Skin Cluster management Section
    sc_frame = cmds.frameLayout(label="Skin Cluster Management", collapsable=True, collapse=True, marginHeight=10)
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=(1,2), columnWidth2=(200, 200))
    cmds.button(label="Select SkinCluster of Selected", h=30 ,c=lambda *args: select_skincluster_of_selected())
    cmds.button(label="Select All SkinClusters", h=30 ,c=lambda *args: select_all_skinclusters_in_scene())
    cmds.setParent("..")
    cmds.button(label="Enable All SkinClusters", h=30 ,c=lambda *args: enable_all_skinclusters())
    cmds.button(label="Disable All SkinClusters", h=30 ,c=lambda *args: disable_all_skinclusters())
    cmds.setParent("..")

    cmds.separator(h=20, style="in")
    
    # Export/Import Section
    export_frame = cmds.frameLayout(label="Export / Import Skin Data", collapsable=True, collapse=True, marginHeight=10)
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=(1,2), columnWidth2=(200, 200))
    cmds.button(label="Export Skin Data", h=30 ,c=lambda *args: export_skin_data(cmds.textField(src_field, q=True, text=True)))
    cmds.button(label="Import Skin Data", h=30 ,c=lambda *args: import_skin_data(cmds.textField(tgt_field, q=True, text=True)))
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.separator(h=20, style="in")

    # CLOSE BUTTON
    cmds.rowLayout(numberOfColumns=1, adjustableColumn=1)
    cmds.button(label="Close", h=30, c=lambda *args: cmds.deleteUI(window, window=True))
    cmds.setParent("..")

    cmds.showWindow(window)

# Launch UI
show_skin_transfer_ui()
