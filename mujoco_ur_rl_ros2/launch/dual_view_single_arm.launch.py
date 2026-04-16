from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.substitutions import FindPackageShare


def _find_repo_root():
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "README.md").exists() and (parent / "mujoco_ur_rl_ros2" / "train_gazebo_single_arm.py").exists():
            return parent
    raise RuntimeError("Could not locate workspace root for dual_view_single_arm.launch.py")


def generate_launch_description():
    repo_root = _find_repo_root()
    trainer_script = repo_root / "mujoco_ur_rl_ros2" / "train_gazebo_single_arm.py"
    gazebo_launch = Path(FindPackageShare("mujoco_ur_rl_ros2").find("mujoco_ur_rl_ros2")) / "launch" / "gazebo_shared_arm_policy.launch.py"

    model_path = LaunchConfiguration("model_path")
    launch_gazebo = LaunchConfiguration("launch_gazebo")
    launch_training = LaunchConfiguration("launch_training")
    training_render = LaunchConfiguration("training_render")
    training_timesteps = LaunchConfiguration("training_timesteps")
    training_n_envs = LaunchConfiguration("training_n_envs")
    training_curriculum = LaunchConfiguration("training_curriculum")
    use_rviz = LaunchConfiguration("use_rviz")
    use_move_group = LaunchConfiguration("use_move_group")

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(gazebo_launch)),
        condition=IfCondition(launch_gazebo),
        launch_arguments={
            "model_path": model_path,
            "launch_policy": "true",
            "use_rviz": use_rviz,
            "use_move_group": use_move_group,
        }.items(),
    )

    training_cmd = [
        "python3",
        str(trainer_script),
        "--timesteps",
        training_timesteps,
        "--n-envs",
        training_n_envs,
        "--curriculum",
        training_curriculum,
        "--resume",
        model_path,
    ]
    training_cmd_with_render = training_cmd + ["--render"]

    training = ExecuteProcess(
        cmd=training_cmd,
        cwd=str(repo_root),
        condition=IfCondition(
            PythonExpression(
                ["'", launch_training, "' == 'true' and '", training_render, "' == 'false'"]
            )
        ),
        output="screen",
    )

    training_with_render = ExecuteProcess(
        cmd=training_cmd_with_render,
        cwd=str(repo_root),
        condition=IfCondition(
            PythonExpression(
                ["'", launch_training, "' == 'true' and '", training_render, "' == 'true'"]
            )
        ),
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "model_path",
                default_value=str(
                    repo_root
                    / "models"
                    / "gazebo_single_arm"
                    / "gazebo_single_arm_20260415_1430"
                    / "best_model.zip"
                ),
                description="Checkpoint used for Gazebo playback and as the resume point for training.",
            ),
            DeclareLaunchArgument("launch_gazebo", default_value="true"),
            DeclareLaunchArgument("launch_training", default_value="false"),
            DeclareLaunchArgument("training_render", default_value="true"),
            DeclareLaunchArgument("training_timesteps", default_value="2000000"),
            DeclareLaunchArgument("training_n_envs", default_value="1"),
            DeclareLaunchArgument("training_curriculum", default_value="grasp_focus"),
            DeclareLaunchArgument("use_rviz", default_value="false"),
            DeclareLaunchArgument("use_move_group", default_value="false"),
            gazebo,
            training,
            training_with_render,
        ]
    )
