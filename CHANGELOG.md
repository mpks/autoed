# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-03-20

### Added

- CHANGELOG.md based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
- A command to plot figures showing diffraction spots in different
  parts of a dataset (`autoed_plot_spots`).
- An automatic plotting of spots figures (also included in the HTML report).
- Global configuration file (generated with autoed_generate_config).
- Automatic report generation. Previously, the user needed to run a
  separate command to generate a report.
- Textual report generated along with the HTML report.
- An option for the user to choose which pipelines to run.
- Pipelines are now defined in the default configuration file.
- Multiplex processing.


### Fixed
- Internal structure of the report directory. Report data is
  now separated from the report.html file.
- A pipeline will now clear the processed directory before
  processing again.
- AutoED will now catch exceptions from the beam center 
  calculations. If the method fails now, the default beam position
  will be saved to the NeXus file (and a warning will be saved in
  the AutoED log).

## [0.2.0] - 2024-08-27

### Added

- A command to generate HTML report (`autoed_generate_report`)
- REST API so that AutoED can be run on a local server instead of
  cluster.
- Processing pipelines (default, user, ice, max lattices, and 
  real space indexing).

### Fixed

- Beam position method now logs the error in the case of a failure.


## [0.1.0] - 2024-02-19

### Added

- First release of the AutoED package.

[unreleased]: https://github.com/mpks/autoed/compare/v0.2.2.post2...HEAD
[0.3.0]: https://github.com/mpks/autoed/compare/v0.2.0...v0.3.0
[0.2.2.post2]: https://github.com/mpks/autoed/compare/v0.2.0...v0.2.2.post2
[0.2.0]: https://github.com/mpks/autoed/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/mpks/autoed/releases/tag/v0.1.0
