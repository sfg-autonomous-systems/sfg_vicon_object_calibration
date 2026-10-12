# SFG Vicon Object Calibration

Tools for calibrating objects tracked by the Vicon motion capture system.

## Background

Vicon tracks a rigid object through the passive IR markers attached to it. To tell agents apart, each agent carries a **marker tree** with its own marker layout:

1. Each marker tree uses the same 3D printed **base**, which has many threaded holes.
2. For each agent, a unique set of 4 holes is chosen. A threaded rod of unique length with a passive IR marker on its end is screwed into each of them.

Vicon only sees the markers, so the coordinate frame of a tracked object is defined by the markers and not by the base. Because every marker tree uses a different layout, the pose Vicon reports would sit somewhere different relative to the agent for each tree. To fix this, the bottom of the base has **3 spherical cutouts**. They are the same on every base, regardless of which holes are used, and they define the **base coordinate frame**:

| Element | Definition                                                                              |
| ------- | --------------------------------------------------------------------------------------- |
| Origin  | Center of the origin sphere.                                                            |
| +X axis | Points toward the center of the x-axis alignment sphere.                                |
| +Y axis | Points toward the center of the y-axis alignment sphere, made orthogonal to the x-axis. |
| +Z axis | Completes the right-handed frame.                                                       |

## Workflow

1. **Assemble** the marker tree with its unique marker layout.
2. **3D scan** the fully assembled marker tree and export the scan as an STL.
3. **Fit spheres** in [CloudCompare](https://www.cloudcompare.org/): Import the STL and fit spheres to the 4 markers and to the 3 spherical cutouts on the bottom of the base. The sphere centers give all positions in the scan's coordinate frame.
4. **Write a config** file in [`config/`](config/) containing these sphere centers (see [Config Format](#config-format)).
5. **Compute the transform** between the marker frame and the base frame with [`compute_marker_tree_transform.py`](#compute_marker_tree_transformpy).
6. **Apply the transform** in Vicon as the origin offset of the tracked object. Vicon then reports the pose of the base, regardless of the marker layout.

## Installation

The dependencies are listed in a conda environment file:

```bash
conda env create -f environment.yaml
conda activate sfg_vicon_object_calibration
```

## Scripts

Scripts are located in the [`scripts/`](scripts/) directory.

### `compute_marker_tree_transform.py`

Computes the transform from a marker tree's marker frame to its base frame. The result can be entered directly as the origin offset of the tracked object in Vicon.

#### Config Format

All positions are sphere centers in the coordinate frame of the 3D scan, in millimeters. Please refer to [`sfg_go2_01__tracker.yaml`](config/sfg_go2_01__tracker.yaml) for an example. The required keys are:

| Key                              | Description                                                  |
| -------------------------------- | ------------------------------------------------------------ |
| `markers`                        | Centers of the IR markers.                                   |
| `base.origin`                    | Center of the spherical cutout that defines the base origin. |
| `base.x_axis_alignment_position` | Center of the spherical cutout that sets the base +X axis.   |
| `base.y_axis_alignment_position` | Center of the spherical cutout that sets the base +Y axis.   |

#### Defining the Marker Frame

The marker frame has to match the object frame defined in Vicon. When executing the script you will be asked for the origin marker and axis alignment. Use the same origin marker and axis alignment markers when defining the object's frame in Vicon. Otherwise the computed offset will be incorrect.