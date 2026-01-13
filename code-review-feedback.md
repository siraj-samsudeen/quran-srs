## 4. Testing Strategy Review

### Strengths
*   **Pyramid Structure:** The project correctly separates `unit`, `integration`, and `e2e` tests.
*   **High-Value E2E:** The Playwright tests in `tests/e2e/` (e.g., `test_new_user_onboarding_journey.py`) are robust, using unique user generation to ensure isolation. They cover critical "money paths".
*   **Controller Integration:** Tests like `tests/integration/user_test.py` effectively verify endpoint behavior (redirects, session state, DB side effects) using `Starlette.testclient`, which is faster than E2E.
*   **Logic Isolation:** Unit tests correctly target complex boolean logic.

### Weaknesses
*   **SRS Logic Gap:** While visibility in SRS mode is tested (`test_mode_filtering.py`), the core SRS algorithm (calculating the next interval based on rating and prime number sequences) lacks dedicated unit/integration tests. This is a critical business logic component.
*   **Minor Misclassification:** Some "integration" tests (e.g., `test_graduatable_modes.py`) are technically unit tests (testing constants).
*   **Fixture Locality:** E2E fixtures define their own user creation logic. Standardizing "User Factories" in `conftest.py` would reduce duplication.

### Recommendations
*   **Add SRS Unit Tests:** Create `tests/unit/test_srs_logic.py` to verify the `start_srs` and interval calculation functions in `app/srs_reps.py`.
*   **Keep the E2E Pattern:** The "Journey" based testing is excellent.
*   **Expand Controller Tests:** Use the pattern in `user_test.py` to test the `hafiz_controller` and `home_controller` refactors.