---
description: Migrate the frontend from NPM to PNPM for faster, stricter dependency management.
---

# Migrate to PNPM

This workflow will convert your project to use PNPM, which is faster and more disk-efficient than NPM.

## Steps

1.  **Install PNPM** (if not already installed):
    ```powershell
    npm install -g pnpm
    ```

2.  **Clean old artifacts**:
    Remove the existing `node_modules` and lockfile to avoid conflicts.
    ```powershell
    cd frontend
    Remove-Item -Recurse -Force node_modules
    Remove-Item package-lock.json
    ```

3.  **Install dependencies with PNPM**:
    This generates a `pnpm-lock.yaml`.
    ```powershell
    pnpm install
    ```

4.  **Verify the build**:
    Ensure everything still works.
    ```powershell
    pnpm run dev
    ```

## Benefits
*   **Speed**: PNPM is up to 2x faster than NPM.
*   **Disk Space**: Dependencies are stored centrally on your machine, saving GBs of space across projects.
*   **Sophistication**: PNPM enforces strict dependency access, preventing "phantom dependencies" (bugs caused by using packages you didn't explicitly install).
