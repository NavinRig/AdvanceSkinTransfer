# Advanced Skin Transfer Tool v01 – NvN Tools
 A powerful and intuitive Maya tool for skin weight transfer and skinCluster management, designed for riggers and technical artists. This tool simplifies skin weight workflows, joint management, and skinCluster operations, saving time and improving precision.
![SkinTransferTool](https://github.com/user-attachments/assets/3f5f3d43-ae08-45ad-a83c-8bf265f78ea4)

# AdvanceSkinTransfer
 Skin Transfer
 Transfer Skin Weights
- Select Source Mesh → Click Add Source Mesh
- Select Target Mesh → Click Add Target Mesh

# Choose Transfer Mode:
- One-to-One → Straight cop
- One-to-Many → Transfer to multiple targets
- Many-to-One → Combine multiple sources into one target
- Automatically creates target skinClusters if not present
- Click Transfer Weights → Done!

# Export & Import Skin Data
- Export skin weights to JSON files for versioning or backup.
- Import skin weights back to any mesh with automatic missing joint creation.

# SkinCluster Management
- Select skinClusters of selected meshes or all in the scene.
- Enable or disable all skinClusters.

# Joint Management
- Skin Joints: Select all joints influencing a mesh.
- Influence Joints: Select joints that actively influence skin weights.
- End Joints: Select all end joints of the skeleton.
- Non-Influence Joints: Select joints that do not affect the mesh
- Remove Non-Influence Joints: Remove joints from skinClusters if they have zero influence (without deleting them).

# UI Features
- Auto-clear placeholder text for source/target fields.
- Multi-selection support for meshes and skinClusters.
- Clean and organized frame layout for easy workflow

# Requirements
- Autodesk Maya 2018 or later
- Python 3.x (built-in with Maya)
- No external libraries required
