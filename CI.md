# Continuous Integration and Automation (CI/CD)

This document outlines the GitHub Actions workflows and related automation configurations used in this repository. Understanding these is crucial for maintaining the project and for any agents tasked with modifying or replicating this setup.

## Table of Contents

1.  [Workflow Overview](#workflow-overview)
2.  [Test Execution Workflow (`run-tests.yml`)](#test-execution-workflow-run-testsyml)
3.  [Build and Release Container Image Workflow (`release.yml`)](#build-and-release-container-image-workflow-releaseyml)
4.  [Dependabot Configuration (`dependabot.yml`)](#dependabot-configuration-dependabotyml)

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
