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
#Functions
def select_skincluster_of_selected():
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning("Please select a mesh.")
        return
    skins = []
    for s in sel:
        skin = get_skin_cluster(s)
        if skin:
            skins.append(skin)
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

# UI
def show_skin_transfer_ui():
    if cmds.window("skinTransferWin", exists=True):
        cmds.deleteUI("skinTransferWin")

    window = cmds.window("skinTransferWin", title="Skin Transfer Tool", widthHeight=(400, 500))
    main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=6)

    #SOURCE/TARGET SECTION
    cmds.text(label="Source Mesh:")
    src_field = cmds.textFieldButtonGrp(label="", buttonLabel="Add Selected", cw3=[1, 240, 100])
    src_skin_label = cmds.text(label="SkinCluster: (none)", align="left")
    def set_source():
        sel = cmds.ls(sl=True)
        if sel:
            cmds.textFieldButtonGrp(src_field, e=True, text=", ".join(sel))
            skin = get_skin_cluster(sel[0])
            cmds.text(src_skin_label, e=True, label=f"SkinCluster: {skin}" if skin else "SkinCluster: None")
    cmds.textFieldButtonGrp(src_field, e=True, bc=set_source)

    cmds.text(label="Target Mesh:")
    tgt_field = cmds.textFieldButtonGrp(label="", buttonLabel="Add Selected", cw3=[1, 240, 100])
    tgt_skin_label = cmds.text(label="SkinCluster: (none)", align="left")
    def set_target():
        sel = cmds.ls(sl=True)
        if sel:
            cmds.textFieldButtonGrp(tgt_field, e=True, text=", ".join(sel))
            skin = get_skin_cluster(sel[0])
            cmds.text(tgt_skin_label, e=True, label=f"SkinCluster: {skin}" if skin else "SkinCluster: None")
    cmds.textFieldButtonGrp(tgt_field, e=True, bc=set_target)

    cmds.separator(h=10, style="in")

    #TRANSFER SKIN WEIGHTS SECTION (collapsible)
    transfer_frame = cmds.frameLayout(label="Transfer Skin Weights", collapsable=True, collapse=False, marginHeight=5)
    cmds.rowLayout(numberOfColumns=3, adjustableColumn=3, columnWidth3=(130, 130, 130), columnAttach3=("both", "both", "both"))
    cmds.button(label="One to One", c=lambda *args: transfer_skin_weights(
        cmds.textFieldButtonGrp(src_field, q=True, text=True),
        cmds.textFieldButtonGrp(tgt_field, q=True, text=True)))
    cmds.button(label="One to Many", c=lambda *args: [transfer_skin_weights(cmds.textFieldButtonGrp(src_field, q=True, text=True), t) for t in cmds.ls(sl=True)])
    cmds.button(label="Many to One", c=lambda *args: [transfer_skin_weights(s, cmds.textFieldButtonGrp(tgt_field, q=True, text=True)) for s in cmds.ls(sl=True)])
    cmds.setParent("..")
    cmds.setParent("..")

    #EXPORT / IMPORT SECTION (collapsible)
    export_frame = cmds.frameLayout(label="Export / Import Skin Data", collapsable=True, collapse=True, marginHeight=5)
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnWidth2=(200, 200), columnAttach2=("both", "both"))
    cmds.button(label="Export Skin Data", c=lambda *args: export_skin_data(cmds.textFieldButtonGrp(src_field, q=True, text=True)))
    cmds.button(label="Import Skin Data", c=lambda *args: import_skin_data(cmds.textFieldButtonGrp(tgt_field, q=True, text=True)))
    cmds.setParent("..")
    cmds.setParent("..")

    #SKINCLUSTER MANAGEMENT SECTION (collapsible)
    sc_frame = cmds.frameLayout(label="SkinCluster Management", collapsable=True, collapse=True, marginHeight=5)
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnWidth2=(200, 200), columnAttach2=("both", "both"))
    cmds.button(label="Select SkinCluster of Selected", c=lambda *args: select_skincluster_of_selected())
    cmds.button(label="Select All SkinClusters", c=lambda *args: select_all_skinclusters_in_scene())
    cmds.setParent("..")
    cmds.button(label="Enable All SkinClusters", c=lambda *args: enable_all_skinclusters())
    cmds.button(label="Disable All SkinClusters", c=lambda *args: disable_all_skinclusters())
    cmds.setParent("..")  # End sc_frame

    #CLOSE BUTTON
    cmds.separator(h=10, style="in")
    cmds.rowLayout(numberOfColumns=1, adjustableColumn=1)
    cmds.button(label="Close", c=lambda *args: cmds.deleteUI(window, window=True))
    cmds.setParent("..")

    cmds.showWindow(window)

# Launch UI
show_skin_transfer_ui()
