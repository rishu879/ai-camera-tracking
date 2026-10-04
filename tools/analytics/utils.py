"""Plotting and PDF document compilation utilities for Analytics."""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def plot_tracking_error(
    timestamps: List[float], errors: List[float], output_path: Path, dpi: int = 150
) -> str:
    """Generate Tracking Error (pixels) vs Time plot with 10px threshold line."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4), dpi=dpi)

    time_arr = np.array(timestamps) if len(timestamps) > 0 else np.arange(len(errors)) * 0.0333
    err_arr = np.array(errors)

    ax.plot(time_arr, err_arr, color="#007acc", linewidth=1.5, label="Instantaneous Error (px)")
    # ISRO SIH threshold line
    ax.axhline(
        y=10.0,
        color="#e74c3c",
        linestyle="--",
        linewidth=1.8,
        label="ISRO Max Error Threshold (10 px)",
    )

    rmse = float(np.sqrt(np.mean(err_arr**2))) if len(err_arr) > 0 else 0.0
    ax.axhline(
        y=rmse,
        color="#27ae60",
        linestyle=":",
        linewidth=1.5,
        label=f"RMSE ({rmse:.2f} px)",
    )

    ax.set_title("FSOC Coarse Tracking Centroid Error", fontsize=12, fontweight="bold")
    ax.set_xlabel("Time (seconds)", fontsize=10)
    ax.set_ylabel("Centroid Error (pixels)", fontsize=10)
    ax.set_ylim(bottom=0.0, top=max(15.0, float(np.max(err_arr)) * 1.1) if len(err_arr) > 0 else 15.0)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", fontsize=9)

    fig.tight_layout()
    fig.savefig(str(output_path))
    plt.close(fig)
    return str(output_path)


def plot_fps(
    timestamps: List[float], fps_list: List[float], output_path: Path, dpi: int = 150
) -> str:
    """Generate Processing FPS vs Time plot with 20 FPS requirement."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4), dpi=dpi)

    time_arr = np.array(timestamps) if len(timestamps) > 0 else np.arange(len(fps_list)) * 0.0333
    fps_arr = np.array(fps_list)

    ax.plot(time_arr, fps_arr, color="#8e44ad", linewidth=1.5, label="Processing Speed (FPS)")
    ax.axhline(
        y=20.0,
        color="#e67e22",
        linestyle="--",
        linewidth=1.8,
        label="ISRO Minimum Requirement (20 FPS)",
    )

    mean_fps = float(np.mean(fps_arr)) if len(fps_arr) > 0 else 0.0
    ax.axhline(
        y=mean_fps,
        color="#2980b9",
        linestyle=":",
        linewidth=1.5,
        label=f"Average FPS ({mean_fps:.1f})",
    )

    ax.set_title("System Processing Throughput (FPS)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Time (seconds)", fontsize=10)
    ax.set_ylabel("Frames Per Second", fontsize=10)
    ax.set_ylim(bottom=0.0, top=max(35.0, float(np.max(fps_arr)) * 1.1) if len(fps_arr) > 0 else 35.0)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower right", fontsize=9)

    fig.tight_layout()
    fig.savefig(str(output_path))
    plt.close(fig)
    return str(output_path)


def plot_trajectory_comparison(
    target_path: List[List[float]],
    camera_path: List[List[float]],
    output_path: Path,
    canvas_size: Tuple[int, int] = (2048, 2048),
    dpi: int = 150,
) -> str:
    """Generate 2D World Trajectory Comparison: Ground-Truth Target Path vs Camera Optical Axis."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 7), dpi=dpi)

    if len(target_path) > 0:
        t_arr = np.array(target_path)
        ax.plot(t_arr[:, 0], t_arr[:, 1], color="#2980b9", linewidth=2.0, label="Target Ground-Truth Path")
        ax.scatter(t_arr[0, 0], t_arr[0, 1], color="#27ae60", s=60, label="Target Start", zorder=5)
        ax.scatter(t_arr[-1, 0], t_arr[-1, 1], color="#c0392b", s=60, label="Target End", zorder=5)

    if len(camera_path) > 0:
        c_arr = np.array(camera_path)
        ax.plot(c_arr[:, 0], c_arr[:, 1], color="#e67e22", linestyle="--", linewidth=1.8, label="Camera Boresight Track")

    ax.set_title("2D Spatial Trajectory Tracking", fontsize=12, fontweight="bold")
    ax.set_xlabel("World X (pixels)", fontsize=10)
    ax.set_ylabel("World Y (pixels)", fontsize=10)
    ax.set_xlim(0, canvas_size[0])
    ax.set_ylim(canvas_size[1], 0)  # Invert Y for image coordinate convention
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", fontsize=9)

    fig.tight_layout()
    fig.savefig(str(output_path))
    plt.close(fig)
    return str(output_path)


def generate_pdf_report(
    pdf_path: Path,
    session_name: str,
    metrics: Dict[str, Any],
    error_plot_path: Optional[str] = None,
    fps_plot_path: Optional[str] = None,
    traj_plot_path: Optional[str] = None,
) -> str:
    """Compile multi-page professional PDF benchmark report using ReportLab."""
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    story = []

    # Title & Subtitle
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0B3C5D"),
        spaceAfter=6,
    )
    sub_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#328CC1"),
        spaceAfter=14,
    )

    story.append(Paragraph("ISRO Smart India Hackathon (SIH) Evaluation Report", title_style))
    story.append(
        Paragraph(
            "AI-Based Virtual Camera Tracking System for Coarse Alignment of Mobile FSOC Terminals",
            sub_style,
        )
    )
    story.append(Spacer(1, 10))

    # Benchmark Compliance Table
    compliance = metrics.get("compliance", {})
    table_data = [
        ["Evaluation Parameter", "ISRO SIH Specification", "Measured Value", "Status"],
        ["Tracking Centroid Error (RMSE)", "≤ 10.0 pixels", f"{metrics.get('rmse_px', 0.0):.2f} px", "PASS" if compliance.get("tracking_error_pass", True) else "FAIL"],
        ["Processing Speed", "≥ 20.0 FPS", f"{metrics.get('mean_fps', 0.0):.1f} FPS", "PASS" if compliance.get("fps_pass", True) else "FAIL"],
        ["Lock Retention Rate", "> 95.0%", f"{metrics.get('lock_retention_rate', 1.0)*100.0:.1f}%", "PASS" if compliance.get("lock_retention_pass", True) else "FAIL"],
        ["Acquisition Time", "≤ 2.0 seconds", f"{metrics.get('acquisition_time_sec', 0.0) or 'N/A'} s", "PASS" if compliance.get("acquisition_time_pass", True) else "FAIL"],
        ["Re-acquisition Time", "≤ 1.0 second", f"{metrics.get('reacquisition_time_sec', 0.0) or 'N/A'} s", "PASS" if compliance.get("reacquisition_time_pass", True) else "FAIL"],
    ]

    t = Table(table_data, colWidths=[2.2 * inch, 1.8 * inch, 1.5 * inch, 1.0 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3C5D")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9B310")),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 1), (-1, -1), 8.5),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 15))

    # Embed Plots
    if error_plot_path and Path(error_plot_path).exists():
        story.append(Paragraph("<b>Tracking Error Analysis:</b>", styles["Heading3"]))
        story.append(RLImage(error_plot_path, width=6.5 * inch, height=2.8 * inch))
        story.append(Spacer(1, 10))

    if fps_plot_path and Path(fps_plot_path).exists():
        story.append(Paragraph("<b>Processing Throughput (FPS):</b>", styles["Heading3"]))
        story.append(RLImage(fps_plot_path, width=6.5 * inch, height=2.8 * inch))
        story.append(Spacer(1, 10))

    if traj_plot_path and Path(traj_plot_path).exists():
        story.append(Paragraph("<b>2D Spatial Trajectory Ground Truth vs Camera Boresight:</b>", styles["Heading3"]))
        story.append(RLImage(traj_plot_path, width=4.5 * inch, height=4.5 * inch))
        story.append(Spacer(1, 10))

    doc.build(story)
    return str(pdf_path)
