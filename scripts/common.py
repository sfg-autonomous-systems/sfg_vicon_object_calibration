from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import cast

import numpy
import pyvista
import typer


class Axis(str, Enum):
    """
    Enumeration for axis directions.
    """

    NEG_X = "-x"
    POS_X = "+x"
    NEG_Y = "-y"
    POS_Y = "+y"
    NEG_Z = "-z"
    POS_Z = "+z"

    def to_index(self) -> int:
        return {
            Axis.POS_X: 0,
            Axis.NEG_X: 0,
            Axis.POS_Y: 1,
            Axis.NEG_Y: 1,
            Axis.POS_Z: 2,
            Axis.NEG_Z: 2,
        }[self]

    def to_direction(self) -> int:
        return {
            Axis.POS_X: 1,
            Axis.NEG_X: -1,
            Axis.POS_Y: 1,
            Axis.NEG_Y: -1,
            Axis.POS_Z: 1,
            Axis.NEG_Z: -1,
        }[self]


def print_available_markers(markers: list) -> None:
    """
    Prints the available markers with their indices.

    Args:
        markers: List of available markers.
    """
    typer.echo("Available markers:")

    for idx, marker in enumerate(markers):
        typer.echo(f"  {idx}: {marker}")


def select_axis(primary: bool = True) -> Axis:
    """
    Prompts the user to select an axis.

    Args:
        primary: Whether to select the primary axis or secondary axis.
    """
    axis_type = "primary" if primary else "secondary"
    axis = typer.prompt(
        f"Enter the {axis_type} axis. Possible values are "
        + ", ".join([e.value for e in Axis]),
        type=Axis,
        default=Axis.POS_X if primary else Axis.POS_Y,
    )
    return axis


def select_marker(markers: list, entity: str) -> numpy.ndarray:
    """
    Prompts the user to select a marker by its index.

    Args:
        markers: List of available markers.
        entity: Description of the entity for which the marker is being selected.

    Returns:
        The selected marker's position as a numpy array.
    """
    marker_index = typer.prompt(
        f"Enter the index of the marker representing the {entity}", type=int
    )

    if marker_index < 0 or marker_index >= len(markers):
        typer.echo("Error: Invalid marker index.", err=True)
        raise typer.Exit(code=1)

    return numpy.array(markers[marker_index])


def validate_input(
    marker_frame_origin: numpy.ndarray,
    marker_frame_primary_axis: Axis,
    marker_frame_primary_axis_alignment_position: numpy.ndarray,
    marker_frame_secondary_axis: Axis,
    marker_frame_secondary_axis_alignment_position: numpy.ndarray,
) -> None:
    """
    Validates the user input for coordinate frame definition. This checks that the primary and secondary axes are not the same,
    and that the selected markers are different.

    Args:
        marker_frame_origin: The origin position of the marker frame.
        marker_frame_primary_axis: The primary axis of the marker frame.
        marker_frame_primary_axis_alignment_position: A position defining the direction of the primary axis.
        marker_frame_secondary_axis: The secondary axis of the marker frame.
        marker_frame_secondary_axis_alignment_position: A position defining the direction of the secondary axis.
    """
    # Validate that primary and secondary axes are not the same.
    if marker_frame_primary_axis.to_index() == marker_frame_secondary_axis.to_index():
        typer.echo("Error: Primary and secondary axes cannot be the same.", err=True)
        raise typer.Exit(code=1)

    # Validate that the selected markers are not the same.
    if (
        numpy.array_equal(
            marker_frame_origin, marker_frame_primary_axis_alignment_position
        )
        or numpy.array_equal(
            marker_frame_origin, marker_frame_secondary_axis_alignment_position
        )
        or numpy.array_equal(
            marker_frame_primary_axis_alignment_position,
            marker_frame_secondary_axis_alignment_position,
        )
    ):
        typer.echo("Error: Selected markers must be different.", err=True)
        raise typer.Exit(code=1)


def select_marker_frame(
    markers: list[numpy.ndarray],
) -> tuple[numpy.ndarray, Axis, numpy.ndarray, Axis, numpy.ndarray]:
    """
    Prompts the user to define the marker frame by selecting an origin marker and two axis alignment markers.

    Args:
        markers: List of available markers.

    Returns:
        The origin, primary axis, primary axis alignment position, secondary axis and secondary axis
        alignment position of the marker frame.
    """
    print_available_markers(markers)

    typer.echo("")
    marker_frame_origin = select_marker(markers, "origin")

    typer.echo("")
    marker_frame_primary_axis = select_axis(primary=True)
    marker_frame_primary_axis_alignment_position = select_marker(
        markers, "position to align the primary axis with"
    )

    typer.echo("")
    marker_frame_secondary_axis = select_axis(primary=False)
    marker_frame_secondary_axis_alignment_position = select_marker(
        markers, "position to align the secondary axis with"
    )

    validate_input(
        marker_frame_origin,
        marker_frame_primary_axis,
        marker_frame_primary_axis_alignment_position,
        marker_frame_secondary_axis,
        marker_frame_secondary_axis_alignment_position,
    )

    return (
        marker_frame_origin,
        marker_frame_primary_axis,
        marker_frame_primary_axis_alignment_position,
        marker_frame_secondary_axis,
        marker_frame_secondary_axis_alignment_position,
    )


def compute_coordinate_frame(
    origin: numpy.ndarray,
    primary_axis: Axis,
    primary_axis_alignment_position: numpy.ndarray,
    secondary_axis: Axis,
    secondary_axis_alignment_position: numpy.ndarray,
) -> numpy.ndarray:
    """
    Computes a 4x4 transformation matrix representing a coordinate frame defined by an origin and two axes.

    Args:
        origin: The origin position of the coordinate frame.
        primary_axis: The primary axis of the coordinate frame.
        primary_axis_alignment_position: A position defining the direction of the primary axis.
        secondary_axis: The secondary axis of the coordinate frame.
        secondary_axis_alignment_position: A position defining the direction of the secondary axis.

    Returns:
        A 4x4 transformation matrix of the coordinate frame.
    """
    # Compute primary vector.
    primary_vector = primary_axis_alignment_position - origin
    primary_vector /= numpy.linalg.norm(primary_vector)
    primary_vector *= primary_axis.to_direction()

    # Compute secondary vector.
    secondary_vector = secondary_axis_alignment_position - origin
    secondary_vector /= numpy.linalg.norm(secondary_vector)
    secondary_vector *= secondary_axis.to_direction()

    # Use Gram-Schmidt process to orthogonalize secondary vector against primary vector.
    secondary_vector -= (
        cast(float, numpy.dot(primary_vector, secondary_vector)) * primary_vector
    )
    secondary_vector = secondary_vector / numpy.linalg.norm(secondary_vector)

    # Retrieve indices for axes.
    primary_index = primary_axis.to_index()
    secondary_index = secondary_axis.to_index()
    tertiary_index = ({0, 1, 2} - {primary_index, secondary_index}).pop()

    frame = numpy.eye(4)
    frame[0:3, primary_index] = primary_vector
    frame[0:3, secondary_index] = secondary_vector

    # Compute tertiary vector as cross product of primary and secondary vectors. In order to
    # ensure a right-handed coordinate frame, the tertiary vector is computed as the cross
    # product of the other two.
    frame[0:3, tertiary_index] = numpy.cross(
        frame[0:3, (tertiary_index + 1) % 3],
        frame[0:3, (tertiary_index + 2) % 3],
    )
    frame[0:3, 3] = origin

    return frame


def render_frames(
    frames: list[numpy.ndarray],
    positions: list[numpy.ndarray],
    labels: list[str],
    mesh_filepath: Path | None = None,
) -> None:
    """
    Renders coordinate frames and labeled positions along with the mesh.

    Args:
        frames: 4x4 transformation matrices of the coordinate frames to render.
        positions: Positions to label.
        labels: Labels of the positions.
        mesh_filepath: Path to the mesh file or None if no mesh should be rendered.
    """
    plotter = pyvista.Plotter()

    if mesh_filepath is not None:
        mesh = pyvista.wrap(pyvista.read(mesh_filepath.as_posix()))
        extents = [
            mesh.bounds[1] - mesh.bounds[0],
            mesh.bounds[3] - mesh.bounds[2],
            mesh.bounds[5] - mesh.bounds[4],
        ]
        plotter.add_mesh(mesh, color="lightgray", opacity=0.9)
    else:
        # Compute the hull of the labeled positions to determine the scale of the axes.
        all_positions = numpy.vstack(positions)
        extents = [
            numpy.max(all_positions[:, 0]) - numpy.min(all_positions[:, 0]),
            numpy.max(all_positions[:, 1]) - numpy.min(all_positions[:, 1]),
            numpy.max(all_positions[:, 2]) - numpy.min(all_positions[:, 2]),
        ]

    scale = numpy.max(extents)

    for transform in frames:
        axes = pyvista.AxesAssembly(
            user_matrix=transform,
            shaft_length=0.15 * scale,
            shaft_radius=0.002 * scale,
            tip_radius=0.006 * scale,
            tip_length=0.03 * scale,
            show_labels=False,
        )  # type: ignore
        plotter.add_actor(axes)  # type: ignore[arg-type]

    plotter.add_point_labels(
        positions,
        labels,  # type: ignore[arg-type]
        show_points=False,
        font_size=12,
        text_color="white",
        shape=None,
        always_visible=True,
        justification_horizontal="center",
        justification_vertical="center",
    )
    plotter.set_background("black")  # type: ignore[arg-type]
    plotter.view_vector((1, 1, 1), viewup=(0, 1, 0))  # type: ignore[arg-type]
    plotter.enable_terrain_style()  # type: ignore[call-arg]
    plotter.show()
