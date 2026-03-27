"""Tests for RustReviewSkill safety analysis.

Covers:
- TestRustReviewSafety: unsafe code, ownership, data races,
  memory safety, panic propagation, async/await patterns
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from pensive.skills.rust_review import RustReviewSkill


@pytest.mark.unit
class TestRustReviewSafety:
    """Test suite for Rust safety and memory analysis."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.skill = RustReviewSkill()
        self.mock_context = Mock()
        self.mock_context.repo_path = Path(tempfile.gettempdir()) / "test_repo"
        self.mock_context.working_dir = Path(tempfile.gettempdir()) / "test_repo"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_unsafe_code_blocks(self, mock_skill_context) -> None:
        """Given unsafe code, skill identifies and validates unsafe blocks."""
        # Arrange
        unsafe_code = """
        use std::ffi::CStr;

        fn process_string(data: *const u8) -> String {
            unsafe {
                // Unsafe block without safety documentation
                let c_str = CStr::from_ptr(data as *const i8);
                c_str.to_string_lossy().into_owned()
            }
        }

        fn create_raw_pointer() -> *mut i32 {
            unsafe {
                // Creating raw pointer without proper justification
                let mut value = 42;
                let raw_ptr = &mut value as *mut i32;
                raw_ptr
            }
        }

        // Safe version with proper documentation
        /// # Safety
        /// This function is safe because:
        /// 1. The pointer is guaranteed to be valid
        /// 2. The memory is not mutated elsewhere
        unsafe fn safe_raw_pointer_ops(ptr: *const i32) -> i32 {
            *ptr
        }
        """

        mock_skill_context.get_file_content.return_value = unsafe_code

        # Act
        unsafe_analysis = self.skill.analyze_unsafe_code(
            mock_skill_context,
            "raw_ops.rs",
        )

        # Assert
        assert "unsafe_blocks" in unsafe_analysis
        assert len(unsafe_analysis["unsafe_blocks"]) >= 3
        assert any(
            block.get("lacks_documentation")
            for block in unsafe_analysis["unsafe_blocks"]
        )
        assert any(
            not block.get("lacks_documentation")
            for block in unsafe_analysis["unsafe_blocks"]
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzes_ownership_patterns(self, mock_skill_context) -> None:
        """Given ownership code, skill detects ownership violations."""
        # Arrange
        ownership_code = """
        use std::rc::Rc;
        use std::cell::RefCell;

        struct Data {
            value: i32,
        }

        fn ownership_violations() {
            let data = Data { value: 42 };

            // Move after use - compilation error but we should catch it
            let moved_data = data;
            println!("{}", data.value);  // Use after move

            // Potential reference cycles
            struct Node {
                next: Option<Rc<RefCell<Node>>>,
                value: i32,
            }

            let node1 = Rc::new(RefCell::new(Node { next: None, value: 1 }));
            let node2 = Rc::new(
                RefCell::new(Node { next: Some(node1.clone()), value: 2 })
            );
            node1.borrow_mut().next = Some(node2);  // Reference cycle
        }

        fn proper_ownership() {
            let data = Data { value: 42 };

            // Proper borrowing
            let data_ref = &data;
            println!("{}", data_ref.value);

            // Proper moving
            let owned_data = data;
            process_data(owned_data);
        }

        fn process_data(data: Data) {
            println!("Processing: {}", data.value);
        }
        """

        mock_skill_context.get_file_content.return_value = ownership_code

        # Act
        ownership_analysis = self.skill.analyze_ownership(
            mock_skill_context,
            "ownership.rs",
        )

        # Assert
        assert "violations" in ownership_analysis
        assert "reference_cycles" in ownership_analysis
        assert "borrow_checker_issues" in ownership_analysis
        assert len(ownership_analysis["violations"]) >= 1
        assert len(ownership_analysis["reference_cycles"]) >= 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_data_races(self, mock_skill_context) -> None:
        """Given concurrent code, when skill analyzes, then flags data race risks."""
        # Arrange
        concurrent_code = """
        use std::thread;
        use std::sync::{Arc, Mutex};

        fn data_race_example() {
            // Safe: using Mutex
            let counter = Arc::new(Mutex::new(0));
            let mut handles = vec![];

            for _ in 0..10 {
                let counter_clone = Arc::clone(&counter);
                let handle = thread::spawn(move || {
                    *counter_clone.lock().unwrap() += 1;
                });
                handles.push(handle);
            }

            for handle in handles {
                handle.join().unwrap();
            }
        }

        use std::cell::RefCell;

        fn potential_data_race() {
            // Unsafe: using RefCell across threads
            let counter = RefCell::new(0);
            let counter_ptr = &counter as *const RefCell<i32>;

            let handle = thread::spawn(move || {
                // This would be unsafe if we could dereference the pointer
                // RefCell is not Send + Sync
            });
        }

        use std::sync::atomic::{AtomicI32, Ordering};

        fn atomic_operations() {
            // Safe: using atomics
            let counter = AtomicI32::new(0);

            let handles: Vec<_> = (0..10)
                .map(|_| {
                    thread::spawn(|| {
                        counter.fetch_add(1, Ordering::SeqCst);
                    })
                })
                .collect();

            for handle in handles {
                handle.join().unwrap();
            }
        }
        """

        mock_skill_context.get_file_content.return_value = concurrent_code

        # Act
        race_analysis = self.skill.analyze_data_races(
            mock_skill_context,
            "concurrent.rs",
        )

        # Assert
        assert "data_races" in race_analysis
        assert "thread_safety_issues" in race_analysis
        assert "safe_patterns" in race_analysis
        assert (
            len(race_analysis["thread_safety_issues"]) >= 1
        )  # Should detect RefCell usage

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzes_memory_safety(self, mock_skill_context) -> None:
        """Given memory management code, skill detects safety issues."""
        # Arrange
        memory_code = """
        use std::ptr;

        fn memory_safety_issues() {
            // Unsafe: raw pointer operations without bounds checking
            let mut data = [1, 2, 3, 4, 5];
            let ptr = data.as_mut_ptr();

            unsafe {
                // Buffer overflow risk
                *ptr.offset(10) = 100;  // Out of bounds access

                // Use after free (simulated)
                let raw_ptr = Box::into_raw(Box::new(42));
                let value = *raw_ptr;
                Box::from_raw(raw_ptr);  // Free
                // *raw_ptr = 10;  // Use after free - commented out for compilation

                // Double free risk
                let ptr2 = Box::into_raw(Box::new(10));
                Box::from_raw(ptr2);
                // Box::from_raw(ptr2);  // Double free - commented out
            }
        }

        fn safe_memory_operations() {
            let data = vec![1, 2, 3, 4, 5];

            // Safe: bounds checked access
            if let Some(value) = data.get(2) {
                println!("{}", value);
            }

            // Safe: using iterators
            for item in &data {
                println!("{}", item);
            }
        }

        fn lifetime_issues<'a>() {
            // Returning reference to local data - won't compile but good to detect
            let local_data = String::from("Hello");
            // &local_data  // Can't return this
        }
        """

        mock_skill_context.get_file_content.return_value = memory_code

        # Act
        memory_analysis = self.skill.analyze_memory_safety(
            mock_skill_context,
            "memory.rs",
        )

        # Assert
        assert "unsafe_operations" in memory_analysis
        assert "buffer_overflows" in memory_analysis
        assert "use_after_free" in memory_analysis
        assert "lifetime_issues" in memory_analysis
        assert len(memory_analysis["unsafe_operations"]) >= 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_panic_propagation(self, mock_skill_context) -> None:
        """Given error handling code, skill flags improper panic usage."""
        # Arrange
        panic_code = """
        fn bad_error_handling() {
            // Panicking in library code
            let config = load_config().unwrap();  // Might panic

            // Explicit panic
            if some_condition() {
                panic!("This should not happen!");  // Bad in library
            }

            // Index access without checking
            let data = vec![1, 2, 3];
            let value = data[10];  // Will panic
        }

        fn good_error_handling() -> Result<String, Box<dyn std::error::Error>> {
            // Proper error propagation
            let config = load_config()?;  // Use ? operator

            // Return error instead of panic
            if some_condition() {
                return Err("Invalid condition".into());
            }

            // Safe index access
            let data = vec![1, 2, 3];
            if let Some(value) = data.get(10) {
                Ok(value.to_string())
            } else {
                Err("Index out of bounds".into())
            }
        }

        fn some_condition() -> bool {
            false
        }

        fn load_config() -> Result<String, std::io::Error> {
            Ok("config".to_string())
        }
        """

        mock_skill_context.get_file_content.return_value = panic_code

        # Act
        panic_analysis = self.skill.analyze_panic_propagation(
            mock_skill_context,
            "error_handling.rs",
        )

        # Assert
        assert "panic_points" in panic_analysis
        assert "unwrap_usage" in panic_analysis
        assert "index_panics" in panic_analysis
        assert len(panic_analysis["panic_points"]) >= 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzes_async_await_patterns(self, mock_skill_context) -> None:
        """Given async code, when skill analyzes, then detects async pattern issues."""
        # Arrange
        async_code = """
        use std::future::Future;
        use tokio::time::{sleep, Duration};

        async fn bad_async_patterns() {
            // Blocking operation in async context
            std::thread::sleep(Duration::from_secs(1));  // Bad

            // Not awaiting async function
            let result = fetch_data();  // Missing .await

            // Mixing blocking and async without proper handling
            let sync_result = blocking_operation();
            let async_result = async_operation().await;
        }

        async fn good_async_patterns() -> Result<String, Box<dyn std::error::Error>> {
            // Proper async waiting
            tokio::time::sleep(Duration::from_secs(1)).await;  // Good

            // Proper error handling with async
            let result = fetch_data().await?;
            Ok(result)
        }

        async fn fetch_data() -> Result<String, std::error::Error> {
            // Simulated async operation
            Ok("data".to_string())
        }

        fn blocking_operation() -> String {
            "sync".to_string()
        }

        async fn async_operation() -> String {
            "async".to_string()
        }

        // Send + Sync considerations
        async fn send_sync_issues<T: Send + Sync>(data: T) -> T {
            // This is fine
            data
        }

        async fn non_send_sync_issues() {
            // Rc is not Send + Sync
            use std::rc::Rc;
            let rc_data = Rc::new(42);
            // Can't use rc_data across await points safely
            tokio::time::sleep(Duration::from_millis(10)).await;
            // println!("{}", *rc_data);  // This would be problematic
        }
        """

        mock_skill_context.get_file_content.return_value = async_code

        # Act
        async_analysis = self.skill.analyze_async_patterns(
            mock_skill_context,
            "async_code.rs",
        )

        # Assert
        assert "blocking_operations" in async_analysis
        assert "missing_awaits" in async_analysis
        assert "send_sync_issues" in async_analysis
        assert len(async_analysis["blocking_operations"]) >= 1
