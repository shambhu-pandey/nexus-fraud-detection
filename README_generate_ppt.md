This README explains how to generate a project PPTX for the FRAUD_DETECTION project.

Files created:
- generate_project_ppt.py : Python script that builds `Shambhu_Pandey_Project.pptx` with the project content and a placeholder for the demo screenshot.

Requirements
-----------
Run in the project's Python virtual environment. Install:

```bash
pip install python-pptx
```

Generate the PPT
----------------
From the project root (where `generate_project_ppt.py` is located) run:

```bash
python generate_project_ppt.py
```

This writes `Shambhu_Pandey_Project.pptx` into the same folder.

Notes
-----
- The script sets the student name, reg no, and guide name as requested. Edit the constants at the top of `generate_project_ppt.py` if you need to change them.
- The slide titled "Demo — Project Screenshot" contains a large textbox that serves as a placeholder; open the generated PPT and paste or insert your screenshot there.
- If you prefer to use an existing PPT template, provide the template file path and I can update the script to load the template and replace placeholder text directly.
