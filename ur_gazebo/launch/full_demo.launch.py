"""
Full pipeline launch: Gazebo + MoveIt + Perception + Grasp + selectable brain.

brain options:
  llm      — LLM planner (Ollama, natural-language commands via /llm_planner/command)
  rl       — Trained SAC policy node (needs model_path)
  openvla  — OpenVLA/SmolVLA end-to-end VLA inference
  act      — ACT (Action Chunking Transformer) policy (needs act_model_path)
  none     — Perception + grasp only, no autonomous brain

Usage:
    # LLM planner (default):
    ros2 launch ur_gazebo full_demo.launch.py brain:=llm

    # RL policy:
    ros2 launch ur_gazebo full_demo.launch.py brain:=rl model_path:=/path/to/best_model.zip

    # ACT policy:
    ros2 launch ur_gazebo full_demo.launch.py brain:=act act_model_path:=~/act_policy/best_act_policy.pt

    # OpenVLA:
    ros2 launch ur_gazebo full_demo.launch.py brain:=openvla task:="pick the red block"

    # Perception + grasp only:
    ros2 launch ur_gazebo full_demo.launch.py brain:=none
"""

import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
    LogInfo,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


def _pkg(name: str) -> str:
    return FindPackageShare(name).find(name)


def _launch(pkg: str, file: str) -> str:
    return os.path.join(_pkg(pkg), "launch", file)


def generate_launch_description():
    # ── Arguments ────────────────────────────────────────────────────────────
    args = [
        DeclareLaunchArgument("world",       default_value="colored_blocks.world",
                              description="Gazebo world file name."),
        DeclareLaunchArgument("robot_name",  default_value="ur"),
        DeclareLaunchArgument("use_sim_time",default_value="true"),
        DeclareLaunchArgument("ur_type",     default_value="ur3"),
        DeclareLaunchArgument("gripper",     default_value="robotiq_2f_85"),
        DeclareLaunchArgument(
            "brain",
            default_value="llm",
            description="Which controller brain to use: llm | rl | openvla | none",
        ),
        # RL-specific
        DeclareLaunchArgument("model_path",  default_value="",
                              description="Path to SAC .zip (required if brain:=rl)"),
        # ACT-specific
        DeclareLaunchArgument("act_model_path", default_value="",
                              description="Path to ACT .pt checkpoint (required if brain:=act)"),
        DeclareLaunchArgument("act_chunk_size",    default_value="10"),
        DeclareLaunchArgument("act_control_rate",  default_value="5.0"),
        DeclareLaunchArgument("act_temporal_gamma",default_value="0.01"),
        DeclareLaunchArgument("drop_x",      default_value="0.35"),
        DeclareLaunchArgument("drop_y",      default_value="0.20"),
        DeclareLaunchArgument("drop_z",      default_value="0.02"),
        DeclareLaunchArgument("phase",       default_value="1.0"),
        # LLM-specific
        DeclareLaunchArgument("ollama_model",    default_value="llama2:latest"),
        DeclareLaunchArgument("ollama_base_url", default_value="http://localhost:11434"),
        DeclareLaunchArgument("auto_demo",       default_value="false"),
        DeclareLaunchArgument(
            "auto_demo_command",
            default_value="pick up the red object and place it to the left of the robot",
        ),
        # OpenVLA-specific
        DeclareLaunchArgument("checkpoint",  default_value="openvla/openvla-7b"),
        DeclareLaunchArgument("task",        default_value="pick the red block and place it in the bin"),
        DeclareLaunchArgument("action_scale",default_value="0.05"),
        # Grasp node
        DeclareLaunchArgument("grasp_colour",  default_value="any"),
        DeclareLaunchArgument("grasp_backend", default_value="auto"),
    ]

    # ── Conditions ───────────────────────────────────────────────────────────
    brain = LaunchConfiguration("brain")
    use_sim = LaunchConfiguration("use_sim_time")

    is_llm    = IfCondition(PythonExpression(["'", brain, "' == 'llm'"]))
    is_rl     = IfCondition(PythonExpression(["'", brain, "' == 'rl'"]))
    is_openvla= IfCondition(PythonExpression(["'", brain, "' == 'openvla'"]))
    is_act    = IfCondition(PythonExpression(["'", brain, "' == 'act'"]))

    # ── Core simulation (Gazebo + MoveIt) ────────────────────────────────────
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(_launch("ur_gazebo", "ur.gazebo.launch.py")),
        launch_arguments={
            "world_file":  LaunchConfiguration("world"),
            "robot_name":  LaunchConfiguration("robot_name"),
            "use_sim_time":use_sim,
            "ur_type":     LaunchConfiguration("ur_type"),
            "gripper":     LaunchConfiguration("gripper"),
        }.items(),
    )

    # ── Perception node (delayed 60 s) ───────────────────────────────────────
    try:
        perception_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(_launch("ur_perception", "perception.launch.py")),
            launch_arguments={"use_sim_time": use_sim}.items(),
        )
        delayed_perception = TimerAction(period=60.0, actions=[perception_launch])
    except Exception:
        delayed_perception = TimerAction(
            period=60.0,
            actions=[LogInfo(msg="ur_perception not found — skipping perception node.")]
        )

    # ── Grasp node (delayed 62 s, always on) ────────────────────────────────
    grasp_node = Node(
        package="ur_grasp",
        executable="grasp_node",
        name="grasp_node",
        output="screen",
        parameters=[{
            "colour":      LaunchConfiguration("grasp_colour"),
            "backend":     LaunchConfiguration("grasp_backend"),
            "use_sim_time":use_sim,
        }],
    )
    delayed_grasp = TimerAction(period=62.0, actions=[grasp_node])

    # ── Brain nodes (delayed 65 s each) ──────────────────────────────────────

    # LLM planner
    try:
        llm_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(_launch("ur_llm_planner", "llm_planner.launch.py")),
            launch_arguments={
                "use_sim_time":       use_sim,
                "ollama_model":       LaunchConfiguration("ollama_model"),
                "ollama_base_url":    LaunchConfiguration("ollama_base_url"),
                "auto_demo":          LaunchConfiguration("auto_demo"),
                "auto_demo_command":  LaunchConfiguration("auto_demo_command"),
            }.items(),
            condition=is_llm,
        )
        delayed_llm = TimerAction(period=65.0, actions=[llm_launch])
    except Exception:
        delayed_llm = TimerAction(
            period=65.0,
            actions=[LogInfo(msg="ur_llm_planner not found — skipping LLM planner.")]
        )

    # RL policy node
    rl_node = Node(
        package="ur_rl_training",
        executable="policy_node",
        name="ur3_rl_policy_node",
        output="screen",
        condition=is_rl,
        parameters=[{
            "model_path":               LaunchConfiguration("model_path"),
            "drop_x":                   LaunchConfiguration("drop_x"),
            "drop_y":                   LaunchConfiguration("drop_y"),
            "drop_z":                   LaunchConfiguration("drop_z"),
            "phase":                    LaunchConfiguration("phase"),
            "use_sim_time":             use_sim,
            "arm_trajectory_topic":     "/arm_controller/joint_trajectory",
            "gripper_trajectory_topic": "/gripper_controller/joint_trajectory",
        }],
    )
    delayed_rl = TimerAction(period=65.0, actions=[rl_node])

    # ACT policy node
    act_node = Node(
        package="ur_act",
        executable="act_policy_node",
        name="act_policy_node",
        output="screen",
        condition=is_act,
        parameters=[{
            "model_path":       LaunchConfiguration("act_model_path"),
            "chunk_size":       LaunchConfiguration("act_chunk_size"),
            "control_rate_hz":  LaunchConfiguration("act_control_rate"),
            "temporal_gamma":   LaunchConfiguration("act_temporal_gamma"),
            "use_sim_time":     use_sim,
        }],
    )
    delayed_act = TimerAction(period=65.0, actions=[act_node])

    # OpenVLA node
    openvla_node = Node(
        package="ur_smolvla",
        executable="inference_node.py",
        name="openvla_inference",
        output="screen",
        condition=is_openvla,
        parameters=[{
            "checkpoint":   LaunchConfiguration("checkpoint"),
            "task":         LaunchConfiguration("task"),
            "action_scale": LaunchConfiguration("action_scale"),
            "use_sim_time": use_sim,
            "enabled":      True,
        }],
    )
    delayed_openvla = TimerAction(period=65.0, actions=[openvla_node])

    # ── Brain selection info log ──────────────────────────────────────────────
    brain_log = TimerAction(
        period=64.0,
        actions=[LogInfo(msg=["Starting brain: ", brain])],
    )

    # ── Assemble ─────────────────────────────────────────────────────────────
    ld = LaunchDescription(args)
    ld.add_action(gazebo_launch)
    ld.add_action(delayed_perception)
    ld.add_action(delayed_grasp)
    ld.add_action(brain_log)
    ld.add_action(delayed_llm)
    ld.add_action(delayed_rl)
    ld.add_action(delayed_act)
    ld.add_action(delayed_openvla)
    return ld
