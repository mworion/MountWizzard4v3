# Project Review Report

Date: 2026-05-03
Scope: Architecture, readability, and structural organization for the `mw4` application code.

## Executive View

The project has a clear domain split (`mountcontrol`, `logic`, `gui`) and broad unit test coverage, but orchestration is concentrated in a few large classes. The most urgent issues are two correctness risks in GUI/modeling paths.

## Findings (Ordered by Severity)

### High

1. **Potential runtime crash in dome slewing status message**
   - **Evidence:** `mw4/gui/mainWmixin/runBasic.py:285`
   - **Detail:** `azimuthT` is referenced in the format string but is not defined in scope.
   - **Impact:** Can raise `NameError` during modeling runs when dome logic is active.
   - **Recommendation:** Use a defined variable (`az`) or compute `azimuthT` before formatting.

2. **Wrong tab widget used when toggling tab visibility**
   - **Evidence:** `mw4/gui/mainWindow/mainW.py:670-671`
   - **Detail:** Tab index is derived from `imagingTabWidget`, but visibility is changed on `toolsTabWidget`.
   - **Impact:** Incorrect tab visibility behavior and possible index mismatch bugs.
   - **Recommendation:** Apply visibility changes to the same widget used for index lookup.

### Medium

3. **Extended window shutdown wait logic can exit too early**
   - **Evidence:** `mw4/gui/mainWindow/mainW.py:907-915`
   - **Detail:** Loop marks completion when one window is closed instead of waiting until all are closed.
   - **Impact:** Race conditions on shutdown; resources may still be alive while shutdown proceeds.
   - **Recommendation:** Invert completion logic to only exit when no `classObj` remains.

4. **Contradictory enable/disable flow for `runModel` button**
   - **Evidence:** `mw4/gui/mainWindow/mainW.py:603-616`
   - **Detail:** `runModel` is first gated by build points + pause state, then overwritten by modeling-ready state.
   - **Impact:** Hard-to-reason behavior and high maintenance burden for UI state logic.
   - **Recommendation:** Consolidate into one decision block with clear precedence.

5. **Over-centralized application coordinator (`MountWizzard4`)**
   - **Evidence:** `mw4/mainApp.py:58-195`
   - **Detail:** One class handles dependency creation, runtime state, timers, signals, and lifecycle.
   - **Impact:** High coupling and difficult isolated testing/refactoring.
   - **Recommendation:** Introduce a composition/bootstrap layer and smaller service coordinators.

6. **Large multi-responsibility main window class**
   - **Evidence:** `mw4/gui/mainWindow/mainW.py` (1000+ lines)
   - **Detail:** UI assembly, dynamic status updates, profile persistence, external window lifecycle, and command handling are all mixed.
   - **Impact:** Reduced readability and slower feature changes.
   - **Recommendation:** Extract focused controllers (e.g., `WindowManager`, `StatusPresenter`, `ProfileController`).

### Low

7. **Build-time side effect in packaging script**
   - **Evidence:** `setup.py:28-29`
   - **Detail:** `setup.py` writes `notes.txt` during execution.
   - **Impact:** Non-hermetic packaging behavior; surprise file writes in build contexts.
   - **Recommendation:** Move release note generation outside setup metadata execution.

8. **Tests excluded from linting**
   - **Evidence:** `tox.ini:29`
   - **Detail:** `tests/*` is excluded in `flake8` config.
   - **Impact:** Readability and style debt can accumulate in tests.
   - **Recommendation:** Re-enable linting for tests or apply targeted per-path relaxations.

## Structural Notes

- **Positive:** Domain folders are meaningful and align with functional concerns.
- **Positive:** Unit test tree mirrors package areas, which supports navigability.
- **Risk:** GUI and runtime orchestration layers currently carry too much cross-domain control logic.

## Prioritized Next Actions

1. Fix the two high-severity correctness issues in `runBasic.py` and `mainW.py`.
2. Refactor `waitClosedExtendedWindows()` to correctly wait for all windows.
3. Simplify `smartFunctionGui()` into a single state model for button enabling.
4. Start incremental decomposition of `MountWizzard4` and `MainWindow` into focused components.

