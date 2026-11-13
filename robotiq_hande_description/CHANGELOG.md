# Changelog

All notable changes to the `robotiq_hande_driver` package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

* [PR-14](https://github.com/AGH-CEAI/robotiq_hande_description/pull/14) - Adds new parameters for the ros2_control: `frequency_hz`, `create_socat_tty`, `ip_adress` and `port`.

### Changed

* [PR-15](https://github.com/AGH-CEAI/robotiq_hande_description/pull/15) - Renamed `ip_adress` to `socat_ip_address` and `port` to `socat_port`.

* [PR-14](https://github.com/AGH-CEAI/robotiq_hande_description/pull/14) - Updated CMake version from `3.8` to `3.16`; changed ros2_control param name `tty` to `tty_port`.


### Deprecated
### Removed
### Fixed
### Security

## [0.1.1] - 2025-03-18

### Fixed

* [PR-6](https://github.com/AGH-CEAI/robotiq_hande_description/pull/6) - Added prefix to inertial macro name. Added descriptive names for params.


## [0.1.0] - 2025-03-13

### Added

* [PR-11](https://github.com/AGH-CEAI/robotiq_hande_description/pull/11) - Parametrized link transform for the gripper.
* [PR-1](https://github.com/AGH-CEAI/robotiq_hande_description/pull/1) - Configuration parameters for ModbusRTU.

### Changed

* [PR-3](https://github.com/AGH-CEAI/robotiq_hande_description/pull/3) & [PR-4](https://github.com/AGH-CEAI/robotiq_hande_description/pull/3) - Changed the coupler model and simplified URDF files by editing the models.

### Fixed

* [PR-2](https://github.com/AGH-CEAI/robotiq_hande_description/pull/2) - Removed unnecessary quotation marks from parameter values.
