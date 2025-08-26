import maya.cmds as cmds
from maya import OpenMaya
from maya import OpenMayaAnim
from maya import OpenMayaUI
from shiboken2 import wrapInstance
from PySide2 import QtWidgets, QtCore

import json
import os

def get_maya_window():
    """Get Maya main window as QWidget."""
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QtWidgets.QWidget)

class SkinTransferTool(QtWidgets.QDialog):
    def __init__(self, parent=get_maya_window()):
        super(SkinTransferTool, self).__init__(parent)
        self.setWindowTitle("Skin Transfer Tool")
        self.setMinimumWidth(400)
        
        self.source_field = QtWidgets.QLineEdit()
        self.target_field = QtWidgets.QLineEdit()
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setValue(0)
        
        self.build_ui()
    
    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Source
        src_layout = QtWidgets.QHBoxLayout()
        src_layout.addWidget(QtWidgets.QLabel("Source Mesh:"))
        src_layout.addWidget(self.source_field)
        src_btn = QtWidgets.QPushButton("Add Selected")
        src_btn.clicked.connect(self.set_source_mesh)
        src_layout.addWidget(src_btn)
        layout.addLayout(src_layout)

        # Target
        tgt_layout = QtWidgets.QHBoxLayout()
        tgt_layout.addWidget(QtWidgets.QLabel("Target Mesh:"))
        tgt_layout.addWidget(self.target_field)
        tgt_btn = QtWidgets.QPushButton("Add Selected")
        tgt_btn.clicked.connect(self.set_target_mesh)
        tgt_layout.addWidget(tgt_btn)
        layout.addLayout(tgt_layout)

        # Transfer Buttons
        layout.addWidget(QtWidgets.QLabel("Transfer Skin Weights:"))
        one_to_one_btn = QtWidgets.QPushButton("One to One Transfer")
        one_to_one_btn.clicked.connect(self.transfer_one_to_one)
        layout.addWidget(one_to_one_btn)

        one_to_many_btn = QtWidgets.QPushButton("One to Many Transfer")
        one_to_many_btn.clicked.connect(self.transfer_one_to_many)
        layout.addWidget(one_to_many_btn)

        many_to_one_btn = QtWidgets.QPushButton("Many to One Transfer")
        many_to_one_btn.clicked.connect(self.transfer_many_to_one)
        layout.addWidget(many_to_one_btn)

        # Export / Import
        layout.addWidget(QtWidgets.QLabel("Export / Import Skin Data:"))
        export_btn = QtWidgets.QPushButton("Export Skin Data")
        export_btn.clicked.connect(self.export_skin_data)
        layout.addWidget(export_btn)

        import_btn = QtWidgets.QPushButton("Import Skin Data")
        import_btn.clicked.connect(self.import_skin_data)
        layout.addWidget(import_btn)

        # Progress bar
        layout.addWidget(QtWidgets.QLabel("Progress:"))
        layout.addWidget(self.progress_bar)

    # --------------------------
    # Utility Functions
    # --------------------------

    def set_source_mesh(self):
        sel = cmds.ls(sl=True)
        if sel:
            self.source_field.setText(sel[0])

    def set_target_mesh(self):
        sel = cmds.ls(sl=True)
        if sel:
            self.target_field.setText(", ".join(sel))

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        QtWidgets.QApplication.processEvents()

    # --------------------------
    # Transfer Functions
    # --------------------------

    def transfer_one_to_one(self):
        src = self.source_field.text().strip()
        tgt = self.target_field.text().strip()
        if not src or not tgt:
            cmds.warning("Please set source and target mesh.")
            return
        self.transfer_skin_weights(src, tgt)

    def transfer_one_to_many(self):
        src = self.source_field.text().strip()
        tgts = self.target_field.text().strip().split(", ")
        for i, tgt in enumerate(tgts):
            self.transfer_skin_weights(src, tgt)
            self.update_progress(int(((i+1)/len(tgts))*100))

    def transfer_many_to_one(self):
        srcs = self.source_field.text().strip().split(", ")
        tgt = self.target_field.text().strip()
        for i, src in enumerate(srcs):
            self.transfer_skin_weights(src, tgt)
            self.update_progress(int(((i+1)/len(srcs))*100))

    def transfer_skin_weights(self, source, target):
        """Core transfer method"""
        if not cmds.objExists(source) or not cmds.objExists(target):
            cmds.warning("Source or target mesh does not exist.")
            return

        # get or create skinCluster
        def get_skin_cluster(mesh):
            history = cmds.listHistory(mesh)
            skin = cmds.ls(history, type="skinCluster")
            if skin:
                return skin[0]
            return None

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
        cmds.inform("Skin weights transferred: {} -> {}".format(source, target))

    # --------------------------
    # Export / Import Functions
    # --------------------------

    def export_skin_data(self):
        src = self.source_field.text().strip()
        if not src:
            cmds.warning("Please set source mesh.")
            return
        
        skin = self.get_skin_cluster(src)
        if not skin:
            cmds.warning("Source has no skinCluster.")
            return

        joints = cmds.skinCluster(skin, q=True, inf=True)
        weights = cmds.getAttr(skin + ".weightList[0].weights[0:]")

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Skin Data", "", "JSON Files (*.json)")
        if file_path:
            data = {"joints": joints, "weights": weights}
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
            cmds.inform("Skin data exported to {}".format(file_path))

    def import_skin_data(self):
        tgt = self.target_field.text().strip()
        if not tgt:
            cmds.warning("Please set target mesh.")
            return

        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import Skin Data", "", "JSON Files (*.json)")
        if not file_path:
            return

        with open(file_path, "r") as f:
            data = json.load(f)

        joints = data["joints"]
        missing = [j for j in joints if not cmds.objExists(j)]

        if missing:
            choice = QtWidgets.QMessageBox.question(self, "Missing Joints",
                "These joints are missing:\n{}\n\nCreate them at origin?".format("\n".join(missing)),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            
            if choice == QtWidgets.QMessageBox.Yes:
                for j in missing:
                    cmds.joint(name=j, p=(0,0,0))

        tgt_skin = self.get_skin_cluster(tgt)
        if not tgt_skin:
            tgt_skin = cmds.skinCluster(joints, tgt, toSelectedBones=True)[0]

        # Apply weights (very simple approach here, can be extended for all verts)
        for i, w in enumerate(data["weights"]):
            try:
                cmds.setAttr("{}.weightList[{}].weights[0]".format(tgt_skin, i), w)
            except:
                pass

        cmds.inform("Skin data imported to {}".format(tgt))

    def get_skin_cluster(self, mesh):
        history = cmds.listHistory(mesh)
        skin = cmds.ls(history, type="skinCluster")
        if skin:
            return skin[0]
        return None

def show_ui():
    global skin_transfer_tool
    try:
        skin_transfer_tool.close()
        skin_transfer_tool.deleteLater()
    except:
        pass
    skin_transfer_tool = SkinTransferTool()
    skin_transfer_tool.show()

show_ui()
