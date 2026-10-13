#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy
import typer
import yaml
from common import Axis, compute_coordinate_frame, render_frames, select_marker_frame
from scipy.spatial.transform import Rotation as R  # type: ignore

app = typer.Typer()


@dataclass(frozen=True)
class Config:
    """
    Configuration for the transform computation.
    """

    markers: list[numpy.ndarray]
    base_origin: numpy.ndarray
    base_x_axis_alignment_position: numpy.ndarray
    base_y_axis_alignment_position: numpy.ndarray

    @classmethod
    def read(cls, config_filepath: Path) -> Config:
        """
        Reads the configuration from a YAML file.
        """
        try:
            with open(config_filepath, "r") as file:
                config = yaml.safe_load(file)

            return cls(
                markers=[numpy.array(marker) for marker in config["markers"]],
                base_origin=numpy.array(config["base"]["origin"]),
                base_x_axis_alignment_position=numpy.array(
                    config["base"]["x_axis_alignment_position"]
                ),
                base_y_axis_alignment_position=numpy.array(
                    config["base"]["y_axis_alignment_position"]
                ),
            )
        except FileNotFoundError:
            typer.echo(
                f"Error: Configuration file not found at {config_filepath}", err=True
            )
            raise typer.Exit(code=1)
        except yaml.YAMLError:
            typer.echo("Error: Invalid YAML format.", err=True)
            raise typer.Exit(code=1)
        except KeyError as exception:
            typer.echo(f"Error: Missing key in configuration: {exception}", err=True)
            raise typer.Exit(code=1)


def output_transform(
    marker_frame: numpy.ndarray,
    base_frame: numpy.ndarray,
) -> None:
    """
    Outputs the translation and rotation that needs to be applied to the marker frame to align it with the base frame.

    Args:
        marker_frame: 4x4 transformation matrix representing the marker frame.
        base_frame: 4x4 transformation matrix representing the base frame.
    """
    # Transforms are applied in reverse order.
    base_frame_relative_to_marker_frame = numpy.dot(
        numpy.linalg.inv(marker_frame),
        base_frame,
    )
    translation = base_frame_relative_to_marker_frame[0:3, 3]
    # We need to compute the intrinsic Euler angles from the rotation matrix.
    # Therefore, we use "XYZ" (note the capitalization).
    rotation = R.from_matrix(base_frame_relative_to_marker_frame[0:3, 0:3]).as_euler(
        "XYZ",
        degrees=True,
    )

    for heading, value in [
        ("Translation [mm]:", translation),
        ("Rotation [deg]:", rotation),
    ]:
        typer.echo(heading)
        typer.echo(
            "  "
            + numpy.array2string(
                value,
                precision=3,
                floatmode="fixed",
                formatter={"float_kind": lambda x: f"{x:.3f}"},
            ).replace("\n", "\n  ")
        )


@app.command()
def main(config_filepath: Path, mesh_filepath: Path | None = None) -> None:
    """
    Main entry point for the script.
    """
    config = Config.read(config_filepath)
    (
        marker_frame_origin,
        marker_frame_primary_axis,
        marker_frame_primary_axis_alignment_position,
        marker_frame_secondary_axis,
        marker_frame_secondary_axis_alignment_position,
    ) = select_marker_frame(config.markers)

    # Compute the marker and base frames. Both frames' coordinates
    # are defined relative to the mesh coordinate frame.
    marker_frame = compute_coordinate_frame(
        marker_frame_origin,
        marker_frame_primary_axis,
        marker_frame_primary_axis_alignment_position,
        marker_frame_secondary_axis,
        marker_frame_secondary_axis_alignment_position,
    )

    base_frame = compute_coordinate_frame(
        config.base_origin,
        Axis.POS_X,
        config.base_x_axis_alignment_position,
        Axis.POS_Y,
        config.base_y_axis_alignment_position,
    )

    output_transform(marker_frame, base_frame)
    render_frames(
        [marker_frame, base_frame],
        config.markers
        + [
            config.base_origin,
            config.base_x_axis_alignment_position,
            config.base_y_axis_alignment_position,
        ],
        [f"Marker {index}" for index in range(len(config.markers))]
        + ["Base Origin", "Base X Alignment Position", "Base Y Alignment Position"],
        mesh_filepath,
    )


if __name__ == "__main__":
    app()
