# SFG Vicon Object Calibration

Tools for calibrating objects tracked by the Vicon motion capture system.

## Marker Trees

### Background

Vicon tracks a rigid object through the passive IR markers attached to it. To tell agents apart, each agent carries a **marker tree** with its own marker layout:

1. Each marker tree uses the same 3D printed [**base**](assets/marker_tree_base.step), a half-sphere with many holes:
   ![Marker Tree Base](assets/marker_tree_base.png)
2. For each agent, a unique set of 4 holes is chosen, threaded inserts are melted into each, and a threaded rod of unique length with a passive IR marker on its end is screwed in.

Vicon only sees the markers, so the coordinate frame of a tracked object is defined by the markers and not by the base. Because every marker tree uses a different layout, the pose Vicon reports would sit somewhere different relative to the agent for each tree. To fix this, the bottom of the base has **3 spherical cutouts**. They are the same on every base, regardless of which holes are used, and they define the **base coordinate frame**:

| Element | Definition                                                                              |
| ------- | --------------------------------------------------------------------------------------- |
| Origin  | Center of the origin sphere.                                                            |
| +X axis | Points toward the center of the x-axis alignment sphere.                                |
| +Y axis | Points toward the center of the y-axis alignment sphere, made orthogonal to the x-axis. |
| +Z axis | Completes the right-handed frame.                                                       |

### Workflow

1. **Assemble** the marker tree with its unique marker layout.
2. **3D scan** the fully assembled marker tree and export the scan as an STL.
3. **Fit spheres** in [CloudCompare](https://www.cloudcompare.org/): Import the STL and fit spheres to the 4 markers and to the 3 spherical cutouts on the bottom of the base. The sphere centers give all positions in the scan's coordinate frame.
4. **Write a config** file in [`config/`](config/) containing these sphere centers (see [Marker Tree Config Format](#marker-tree-config-format)).
5. **Compute the transform** between the marker frame and the base frame with [`compute_marker_tree_transform.py`](#compute_marker_tree_transformpy).
6. **Apply the transform** in Vicon as the origin offset of the tracked object. Vicon then reports the pose of the base, regardless of the marker layout.

## Origin Calibration Object

### Background

The **origin calibration object** is a CNC machined plate with 4 passive IR markers attached to it, all lying in the same plane. It is used to set the Vicon volume origin.

![Origin Calibration Object](assets/origin_calibration_object.png)

In Vicon Tracker, any tracked object can be selected as a calibration object. Tracker then stores the object's marker positions in world coordinates, i.e. relative to the volume origin at that moment. Setting the volume origin with this calibration object restores exactly that volume origin. The object origin defined in Tracker has no effect. To set the volume origin to a frame defined by the plate itself, the marker positions in the calibration object file have to be expressed in that frame instead:

| Element        | Definition                                                                                            |
| -------------- | ----------------------------------------------------------------------------------------------------- |
| Origin         | Center of the origin marker.                                                                          |
| Primary axis   | Points toward the center of the primary axis alignment marker.                                        |
| Secondary axis | Points toward the center of the secondary axis alignment marker, made orthogonal to the primary axis. |
| Tertiary axis  | Completes the right-handed frame.                                                                     |

### Workflow

1. **3D scan** the plate including its markers and export the scan as an STL.
2. **Fit spheres** in [CloudCompare](https://www.cloudcompare.org/): Import the STL and fit spheres to the 4 markers. The sphere centers give the marker positions in the scan's coordinate frame.
3. **Write a config** file in [`config/`](config/) containing these sphere centers (see [Origin Calibration Object Config Format](#origin-calibration-object-config-format)).
4. **Compute the marker positions** in the desired frame with [`compute_origin_calibration_object_markers.py`](#compute_origin_calibration_object_markerspy).
5. **Create the calibration object** in Vicon Tracker: Create an object from the 4 markers and select it as a calibration object. Tracker saves it as a `.vsk` file under `Users/Public/Documents/Vicon/.../Calibration Objects`.
6. **Replace the marker positions** in this `.vsk` file with the computed ones. For each marker, set both `VALUE` and `PRIOR` of its `_x`, `_y` and `_z` parameters.
7. **Set the volume origin** with the calibration object. Tracking the position of the origin marker should now report approximately `(0, 0, 0)`.

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

#### Marker Tree Config Format

All positions are sphere centers in the coordinate frame of the 3D scan, in millimeters. Please refer to [`sfg_go2_01.yaml`](config/sfg_go2_01.yaml) for an example. The required keys are:

| Key                              | Description                                                  |
| -------------------------------- | ------------------------------------------------------------ |
| `markers`                        | Centers of the IR markers.                                   |
| `base.origin`                    | Center of the spherical cutout that defines the base origin. |
| `base.x_axis_alignment_position` | Center of the spherical cutout that sets the base +X axis.   |
| `base.y_axis_alignment_position` | Center of the spherical cutout that sets the base +Y axis.   |

#### Defining the Marker Frame

The marker frame has to match the object frame defined in Vicon. When executing the script you will be asked for the origin marker and axis alignment. Use the same origin marker and axis alignment markers when defining the object's frame in Vicon. Otherwise the computed offset will be incorrect.

### `compute_origin_calibration_object_markers.py`

Computes the positions of the origin calibration object's markers in a frame defined by the markers themselves. The result can be entered directly into the calibration object's `.vsk` file in Vicon Tracker.

#### Origin Calibration Object Config Format

All positions are sphere centers in the coordinate frame of the 3D scan, in millimeters. The required keys are:

| Key       | Description                |
| --------- | -------------------------- |
| `markers` | Centers of the IR markers. |

#### Defining the Marker Frame

When executing the script you will be asked for the origin marker and axis alignment. The marker positions are then printed in this frame, i.e. the origin marker is at `(0, 0, 0)`, the primary axis alignment marker lies on the primary axis and the secondary axis alignment marker lies in the plane spanned by the primary and secondary axes. Once the volume origin is set with the calibration object, this frame becomes the Vicon world frame.
