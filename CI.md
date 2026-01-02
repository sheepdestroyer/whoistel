# Continuous Integration and Automation (CI/CD)

This document outlines the GitHub Actions workflows and related automation configurations used in this repository. Understanding these is crucial for maintaining the project and for any agents tasked with modifying or replicating this setup.

## Table of Contents

1.  [Workflow Overview](#workflow-overview)
2.  [Test Execution Workflow (`run-tests.yml`)](#test-execution-workflow-run-testsyml)
3.  [Build and Release Container Image Workflow (`release.yml`)](#build-and-release-container-image-workflow-releaseyml)
4.  [Dependabot Configuration (`dependabot.yml`)](#dependabot-configuration-dependabotyml)
5.  [Running Locally with Docker/Podman](#running-locally-with-dockerpodman)

## 1. Workflow Overview

Our CI/CD setup automates testing, building, releasing container images, and dependency management using GitHub Actions and Dependabot.

-   **Testing:** Ensures code quality and catches regressions.
-   **Building & Releasing:** Automates the creation of container images and manages GitHub Releases.
-   **Dependency Management:** Keeps dependencies up-to-date via Dependabot.

## 2. Test Execution Workflow (`run-tests.yml`)

-   **File:** `.github/workflows/run-tests.yml`
-   **Purpose:** Automatically runs the project's test suite to ensure code changes are valid and do not introduce regressions.
-   **Triggers:**
    -   On `push` to any branch (`**`).
    -   On `pull_request` targeting the `main` branch.
-   **Key Steps & Configuration:**
    1.  **Environment:** Runs on `ubuntu-latest`.
    2.  **Python Setup:** Sets up Python using `actions/setup-python@v5`.
        -   `python-version`: Currently configured for `3.11`.
        -   Caches `pip` dependencies for faster subsequent runs.
    3.  **Dependency Installation:**
        -   Upgrades `pip`.
        -   Installs dependencies from `requirements.txt` and `requirements-dev.txt`.
    4.  **Run Tests:** Executes `python -m pytest -v tests/` to run the test suite.

## 3. Build and Release Container Image Workflow (`release.yml`)

-   **File:** `.github/workflows/release.yml`
-   **Purpose:** Automates the building and publishing of a container image to GitHub Container Registry (ghcr.io) when a version tag is pushed.
-   **Triggers:**
    -   On `push` of a tag matching the pattern `v*.*` (e.g., `v1.0`, `v1.2.3`).
    -   Manual trigger via `workflow_dispatch` (allows specifying a tag name).
-   **Key Steps & Logic:**
    1.  **Determine Tag:**
        -   Identifies the Git tag to be used for the release, whether from a tag push event or manual input.
    2.  **Checkout Repository:** Checks out the repository at the specified tag.
    3.  **Log in to GitHub Container Registry:** Authenticates with `ghcr.io` using a GITHUB_TOKEN.
    4.  **Build Container Image:**
        -   Uses `podman build` with the `Containerfile` in the repository root.
        -   Tags the image with the Git tag (e.g., `ghcr.io/owner/repo:v1.0.0`) and `latest`.
        -   The image name is constructed using `ghcr.io/${{ github.repository_owner }}/${{ github.event.repository.name }}` (converted to lowercase).
    5.  **Push Container Image:**
        -   Pushes both the version-specific tag and the `latest` tag to `ghcr.io`.

## 4. Dependabot Configuration (`dependabot.yml`)

-   **File:** `.github/dependabot.yml`
-   **Purpose:** Configures Dependabot to automatically create Pull Requests for updating dependencies.
-   **Key Configurations:**
    1.  **`pip` (Python dependencies):**
        -   Checks for updates daily in the root directory (for `requirements.txt` and `requirements-dev.txt`).
        -   Targets the `main` branch.
        -   Default strategy is to allow all updates (patch, minor, major). Comments in the file suggest how to restrict this if needed.
    2.  **`github-actions` (GitHub Actions used in workflows):**
        -   Checks for updates daily in the root directory (for workflow files).
        -   Targets the `main` branch.
        -   Allows all updates, including major versions of actions.

## 5. Running Locally with Docker/Podman

You can build and run the `whoistel` application locally using Docker or Podman.

1.  **Build the Image:**
    Navigate to the project's root directory (where the `Containerfile` is located) and run:
    ```bash
    docker build -t whoistel-cli .
    ```
    (Replace `docker` with `podman` if you are using Podman. You can choose any tag instead of `whoistel-cli`.)

2.  **Run the Container:**
    The container is designed to behave like an executable.

    *   **To see the help message:**
        ```bash
        docker run --rm whoistel-cli
        ```
        (This will execute the default command, which is `--help`.)

    *   **To look up a phone number:**
        Pass the phone number as an argument after the image name:
        ```bash
        docker run --rm whoistel-cli <phone_number>
        ```
        For example:
        ```bash
        docker run --rm whoistel-cli +33740756315
        docker run --rm whoistel-cli 0140000000
        ```

    *   **Output:**
        *   Successful lookup information will be printed to `stdout`.
        *   Logs (operational messages, warnings, errors) will be printed to `stderr`.

    *   **Database:** The `Containerfile` is configured to run `updatearcep.sh` during the image build process. This means the necessary data files are downloaded and the `whoistel.sqlite3` database is generated and included within the image itself. No separate volume mounting for the database is required for basic CLI operation with the bundled database. If you need to use an external or updated database, you would need to manage that via Docker volumes and potentially adjust the script or container startup to point to it.

## 6. Agentic CI Standards

To ensure reproducible and clean builds during agent-driven development:

### Temporary Directory Strategy

When an Agent performs CI tasks (verification, review analysis):
1.  **Work in Isolation**: Use the **`agent-workspace/`** directory for all intermediate artifacts (JSON status files, logs).
2.  **No Pollution**: Do **not** write temporary status files (`pr_status_*.json`, `poll.log`) to the repository root. All tool outputs must be directed to `agent-workspace/`.
3.  **Clean Up**: The directory is ignored by git, so files can persist for debugging or be cleaned up.

### Review Cycle responsibility

The Agent is the "intelligent driver" of the CI process:
-   **Analysis**: It must interpret the *content* of Code Reviews, distinguishing between actionable feedback and "LGTM" noise.
-   **Decision**: It decides if a PR is ready to merge based on semantic understanding, not simple regex checks.
-   **Loop**: It persistently monitors for new feedback until the PR state is explicitly approved or changes are requested.
