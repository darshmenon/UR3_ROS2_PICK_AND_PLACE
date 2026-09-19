from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _create_node(context):
    """Build the Node with proper string conversions (mirrors
    ur_mtc_pick_place_demo/launch/pick_place_demo.launch.py's pattern).

    Needed so params_file can be conditionally omitted -- Node.parameters
    entries must be real paths, not an empty-string placeholder.
    """
    params_file_str = LaunchConfiguration("params_file").perform(context)

    parameters = [{
        "min_confidence": LaunchConfiguration("min_confidence"),
        "settle_time":    LaunchConfiguration("settle_time"),
        "prefix":         LaunchConfiguration("prefix"),
        "enable_workspace_split": LaunchConfiguration("enable_workspace_split"),
        "split_value":    LaunchConfiguration("split_value"),
        "split_keep_positive": LaunchConfiguration("split_keep_positive"),
    }]
    if params_file_str:
        parameters.append(params_file_str)

    return [Node(
        package="ur_sorting_demo",
        executable="sorting_node.py",
        name="sorting_node",
        namespace=LaunchConfiguration("namespace"),
        output="screen",
        parameters=parameters,
    )]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("min_confidence", default_value="0.5"),
        DeclareLaunchArgument("settle_time",    default_value="2.0",
                              description="Seconds to wait for perception before starting"),
        DeclareLaunchArgument("auto_start",     default_value="false",
                              description="Start sorting immediately on launch"),
        # Dual-arm support (see dual_sorting_demo.launch.py, which sets these
        # per instance). Defaults reproduce single-arm behaviour exactly.
        DeclareLaunchArgument("namespace", default_value="",
                              description="Node namespace (e.g. 'left'/'right' for dual-arm)"),
        DeclareLaunchArgument("prefix", default_value="",
                              description="Joint/link/controller name prefix (e.g. 'left_')"),
        DeclareLaunchArgument("params_file", default_value="",
                              description="Optional extra params YAML (e.g. bins_left.yaml)"),
        DeclareLaunchArgument("enable_workspace_split", default_value="false",
                              description="Filter /detected_objects to this instance's half"),
        DeclareLaunchArgument("split_value", default_value="0.0"),
        DeclareLaunchArgument("split_keep_positive", default_value="true"),
        OpaqueFunction(function=_create_node),
    ])
