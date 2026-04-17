---
name: CT Scan Analysis Helper
description: Provides guidelines and scripts for processing and analyzing 3D CT Scan data.
---

# CT Scan Analysis Helper

This skill gives me specific context and rules to follow when helping you process and review 3D volumetric images in your MedAI project. 

Whenever you ask me to work on CT Scan analysis, I will automatically refer to these instructions!

## Guidelines
1. **Normalization**: Always normalize the Hounsfield Units (HU) when loading DICOM files to ensure the contrast is consistent before running AI models.
2. **Backend**: Any new API endpoints for processing large imaging payloads must be placed in `backend/` and use async processes if the files are large to prevent timeout.
3. **Frontend**: When rendering slices in React, use WebGL rendering to handle the 3D performance.

## Useful Code Snippet Example
If you ask me to analyze the shape of a loaded matrix, I will default to using this format:

```python
import numpy as np

def check_volume_properties(volume):
    print("Shape:", volume.shape)
    print("Min val:", np.min(volume))
    print("Max val:", np.max(volume))
```
