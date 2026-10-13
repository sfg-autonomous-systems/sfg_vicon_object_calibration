#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy
import typer
import yaml
from common import compute_coordinate_frame, render_frames, select_marker_frame

app = typer.Typer()


@dataclass(frozen=True)
class Config:
    """
    Configuration for the marker position computation.
    """

    markers: list[numpy.ndarray]

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


def output_marker_positions(
    marker_frame: numpy.ndarray,
    markers: list[numpy.ndarray],
) -> None:
    """
    Outputs the marker positions expressed in the marker frame.

    Args:
        marker_frame: 4x4 transformation matrix representing the marker frame.
        markers: Marker positions in the mesh coordinate frame.
    """
    # Transform the marker positions from the mesh coordinate frame into the marker frame.
    mesh_frame_relative_to_marker_frame = numpy.linalg.inv(marker_frame)

    typer.echo("Marker positions [mm]:")

    for index, marker in enumerate(markers):
        position = numpy.dot(
            mesh_frame_relative_to_marker_frame, numpy.append(marker, 1)
        )[0:3]
        typer.echo(
            f"  {index}: "
            + numpy.array2string(
                position,
                precision=6,
                floatmode="fixed",
                formatter={"float_kind": lambda x: f"{x:.6f}"},
            )
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

    # Compute the marker frame. Its coordinates are defined relative
    # to the mesh coordinate frame.
    marker_frame = compute_coordinate_frame(
        marker_frame_origin,
        marker_frame_primary_axis,
        marker_frame_primary_axis_alignment_position,
        marker_frame_secondary_axis,
        marker_frame_secondary_axis_alignment_position,
    )

    typer.echo("")
    output_marker_positions(marker_frame, config.markers)
    render_frames(
        [marker_frame],
        config.markers,
        [f"Marker {index}" for index in range(len(config.markers))],
        mesh_filepath,
    )


if __name__ == "__main__":
    app()
