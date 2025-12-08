"""
Unit tests for pattern matching and DSL recognition.

Tests code pattern identification, DSL parsing,
and transformation pattern recognition.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

# Import the skills we're testing
from parseltongue.skills.pattern_matching import PatternMatchingSkill


class TestPatternMatchingSkill:
    """Test suite for PatternMatchingSkill."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        self.skill = PatternMatchingSkill()

    @pytest.mark.unit
    def test_recognizes_test_patterns(self, sample_test_patterns):
        """Given test patterns, when skill analyzes, then recognizes testing structures."""
        # Arrange
        test_code = sample_test_patterns["pytest_fixture"]

        # Act
        result = self.skill.recognize_test_patterns(test_code)

        # Assert
        assert "test_pattern" in result["recognized_patterns"]
        assert result["confidence"] > 0.8

        # Should detect pytest fixture
        assert any("fixture" in pattern for pattern in result["patterns"]["pytest"])

        # Should detect test class
        assert "test_class" in result["structures"]
        assert "TestUserService" in result["test_classes"]

        # Should detect setup method
        assert "setup_method" in result["lifecycle_methods"]

    @pytest.mark.unit
    def test_identifies_ddd_patterns(self):
        """Given Domain-Driven Design code, when skill analyzes, then identifies DDD patterns."""
        # Arrange
        ddd_code = '''
from dataclasses import dataclass
from typing import List
from abc import ABC, abstractmethod

# Entity
@dataclass
class Order:
    id: str
    items: List[OrderItem]
    status: str

    def add_item(self, item: OrderItem) -> None:
        self.items.append(item)

# Value Object
@dataclass(frozen=True)
class Money:
    amount: float
    currency: str

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

# Repository Interface
class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> None:
        pass

    @abstractmethod
    def find_by_id(self, order_id: str) -> Order:
        pass

# Domain Service
class OrderService:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    def place_order(self, order_data: dict) -> Order:
        order = Order(
            id=generate_id(),
            items=[],
            status="pending"
        )
        self.repository.save(order)
        return order

# Aggregate Root
class Customer:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.orders: List[Order] = []

    def place_order(self, order: Order) -> None:
        self.orders.append(order)
        # Domain logic
        if len(self.orders) > 10:
            # Business rule
            raise ValueError("Too many orders")
        '''

        # Act
        result = self.skill.recognize_ddd_patterns(ddd_code)

        # Assert
        ddd_patterns = result["ddd_patterns"]

        # Should detect Entity pattern
        assert "entity" in ddd_patterns
        assert "Order" in ddd_patterns["entities"]

        # Should detect Value Object pattern
        assert "value_object" in ddd_patterns
        assert "Money" in ddd_patterns["value_objects"]

        # Should detect Repository pattern
        assert "repository" in ddd_patterns
        assert "OrderRepository" in ddd_patterns["repositories"]

        # Should detect Domain Service pattern
        assert "domain_service" in ddd_patterns
        assert "OrderService" in ddd_patterns["domain_services"]

    @pytest.mark.unit
    def test_identifies_gof_patterns(self):
        """Given Gang of Four patterns, when skill analyzes, then identifies GoF patterns."""
        # Arrange
        gof_code = '''
from abc import ABC, abstractmethod

# Factory Method
class Animal(ABC):
    @abstractmethod
    def make_sound(self) -> str:
        pass

class Dog(Animal):
    def make_sound(self) -> str:
        return "Woof!"

class Cat(Animal):
    def make_sound(self) -> str:
        return "Meow!"

class AnimalFactory:
    @staticmethod
    def create_animal(animal_type: str) -> Animal:
        if animal_type == "dog":
            return Dog()
        elif animal_type == "cat":
            return Cat()
        else:
            raise ValueError("Unknown animal type")

# Observer Pattern
class Event:
    def __init__(self, data: dict):
        self.data = data

class Observer(ABC):
    @abstractmethod
    def notify(self, event: Event) -> None:
        pass

class EventManager:
    def __init__(self):
        self._observers: List[Observer] = []

    def subscribe(self, observer: Observer) -> None:
        self._observers.append(observer)

    def notify_observers(self, event: Event) -> None:
        for observer in self._observers:
            observer.notify(event)

# Strategy Pattern
class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount: float) -> bool:
        pass

class CreditCardPayment(PaymentStrategy):
    def pay(self, amount: float) -> bool:
        # Process credit card payment
        return True

class PayPalPayment(PaymentStrategy):
    def pay(self, amount: float) -> bool:
        # Process PayPal payment
        return True
        '''

        # Act
        result = self.skill.recognize_gof_patterns(gof_code)

        # Assert
        gof_patterns = result["gof_patterns"]

        # Should detect Factory Method pattern
        assert "factory_method" in gof_patterns
        assert "AnimalFactory" in gof_patterns["factories"]

        # Should detect Observer pattern
        assert "observer" in gof_patterns
        assert "Observer" in gof_patterns["observers"]

        # Should detect Strategy pattern
        assert "strategy" in gof_patterns
        assert len(gof_patterns["strategies"]) >= 2

    @pytest.mark.unit
    def test_identifies_async_patterns(self, sample_async_code):
        """Given async code, when skill analyzes, then identifies async patterns."""
        # Arrange
        code = sample_async_code

        # Act
        result = self.skill.recognize_async_patterns(code)

        # Assert
        async_patterns = result["async_patterns"]

        # Should detect Async Context Manager pattern
        assert "async_context_manager" in async_patterns
        assert "__aenter__" in code and "__aexit__" in code

        # Should detect Retry pattern
        assert "retry_pattern" in async_patterns
        assert "fetch_with_retry" in result["pattern_instances"]

        # Should detect Concurrent Processing pattern
        assert "concurrent_processing" in async_patterns
        assert "asyncio.gather" in code

    @pytest.mark.unit
    def test_identifies_performance_patterns(self, sample_test_patterns):
        """Given performance code, when skill analyzes, then identifies optimization patterns."""
        # Arrange
        performance_code = sample_test_patterns["performance_pattern"]

        # Act
        result = self.skill.recognize_performance_patterns(performance_code)

        # Assert
        perf_patterns = result["performance_patterns"]

        # Should detect optimization opportunities
        assert "optimization_opportunity" in perf_patterns

        # Should identify O(n) vs O(n²) patterns
        assert "find_duplicates_slow" in result["anti_patterns"]
        assert "find_duplicates_fast" in result["good_patterns"]

        # Should detect memory-efficient patterns
        assert "memory_efficient" in perf_patterns
        assert "process_large_file" in result["pattern_instances"]

    @pytest.mark.unit
    def test_detects_architectural_patterns(self):
        """Given architectural code, when skill analyzes, then identifies architectural patterns."""
        # Arrange
        arch_code = '''
# MVC Pattern
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

class UserController:
    def __init__(self, model: UserModel, view: UserView):
        self.model = model
        self.view = view

    def update_user(self, user_id: int, name: str):
        user = self.model.get_user(user_id)
        user.name = name
        self.model.save_user(user)
        self.view.display_user(user)

class UserModel:
    def get_user(self, user_id: int) -> User:
        # Database logic
        pass

    def save_user(self, user: User):
        # Database logic
        pass

class UserView:
    def display_user(self, user: User):
        print(f"User: {user.name} ({user.email})")

# Repository Pattern with Unit of Work
class UnitOfWork:
    def __init__(self):
        self.users = UserRepository()
        self.products = ProductRepository()
        self._new_objects = []
        self._dirty_objects = []

    def register_new(self, obj):
        self._new_objects.append(obj)

    def register_dirty(self, obj):
        self._dirty_objects.append(obj)

    def commit(self):
        for obj in self._new_objects:
            self.users.add(obj)
        for obj in self._dirty_objects:
            self.users.update(obj)
        '''

        # Act
        result = self.skill.recognize_architectural_patterns(arch_code)

        # Assert
        arch_patterns = result["architectural_patterns"]

        # Should detect MVC pattern
        assert "mvc" in arch_patterns
        assert "Controller" in result["pattern_instances"]

        # Should detect Repository pattern
        assert "repository" in arch_patterns
        assert "UserRepository" in result["pattern_instances"]

        # Should detect Unit of Work pattern
        assert "unit_of_work" in arch_patterns

    @pytest.mark.unit
    def test_identifies_anti_patterns(self, performance_issues):
        """Given problematic code, when skill analyzes, then identifies anti-patterns."""
        # Arrange
        anti_patterns = performance_issues

        # Act & Assert for each anti-pattern
        for pattern_name, code in anti_patterns.items():
            result = self.skill.identify_anti_patterns(code)

            if "nested_loops" in pattern_name:
                assert "nested_loops" in result["anti_patterns"]
                assert "performance_issue" in result["severity"]
                assert "O(n²)" in result["description"]

            elif "memory_leak" in pattern_name:
                assert "memory_leak" in result["anti_patterns"]
                assert "growing_collection" in result["description"]

            elif "blocking_io" in pattern_name:
                assert "blocking_async" in result["anti_patterns"]
                assert "event_loop_blocking" in result["description"]

    @pytest.mark.unit
    def test_matches_dsl_patterns(self):
        """Given DSL code, when skill analyzes, then matches DSL patterns."""
        # Arrange
        dsl_code = '''
# Configuration DSL
database {
    host: "localhost"
    port: 5432
    name: "myapp"
    pools {
        size: 10
        timeout: 30
    }
}

# Routing DSL
routes {
    "/api/users" -> UserController.index with {
        method: GET
        auth: true
    }

    "/api/users/{id}" -> UserController.show with {
        method: GET
        params: [id]
    }
}

# Validation DSL
validate User {
    name: required, string, min_length: 2
    email: required, email
    age: optional, integer, min_value: 0
}
        '''

        # Act
        result = self.skill.match_dsl_patterns(dsl_code)

        # Assert
        dsl_patterns = result["dsl_patterns"]

        # Should detect configuration DSL pattern
        assert "configuration_dsl" in dsl_patterns
        assert result["structures"]["nested_blocks"] >= 2

        # Should detect routing DSL pattern
        assert "routing_dsl" in dsl_patterns
        assert result["structures"]["route_definitions"] >= 2

        # Should detect validation DSL pattern
        assert "validation_dsl" in dsl_patterns
        assert result["structures"]["validation_rules"] >= 3

    @pytest.mark.unit
    def test_suggests_pattern_improvements(self, performance_issues):
        """Given code with anti-patterns, when skill analyzes, then suggests improvements."""
        # Arrange
        bad_code = performance_issues["nested_loops"]

        # Act
        result = self.skill.suggest_improvements(bad_code)

        # Assert
        suggestions = result["suggestions"]

        # Should suggest optimization
        assert len(suggestions) >= 1

        # Should provide before/after comparison
        for suggestion in suggestions:
            assert "issue" in suggestion
            assert "improvement" in suggestion
            assert "before" in suggestion
            assert "after" in suggestion

        # Should suggest set-based approach for O(n²) problem
        optimization_suggestion = next(
            (s for s in suggestions if "set" in s["improvement"].lower()),
            None
        )
        assert optimization_suggestion is not None

    @pytest.mark.unit
    def test_validates_pattern_consistency(self):
        """Given multiple patterns, when skill analyzes, then validates consistency."""
        # Arrange
        mixed_patterns_code = '''
class InconsistentPattern:
    def __init__(self):
        self.data = []

    def add_item(self, item):
        # Repository-like naming but not really a repository
        self.data.append(item)
        return self

    def find_item(self, predicate):
        # Mixed responsibilities
        result = []
        for item in self.data:
            if predicate(item):
                result.append(item)
        return result

    def save_to_database(self):
        # Adding persistence breaks single responsibility
        db.execute("INSERT INTO items VALUES (?)", self.data)
        '''
        # Act
        result = self.skill.validate_pattern_consistency(mixed_patterns_code)

        # Assert
        consistency = result["consistency_analysis"]

        # Should detect mixed patterns
        assert "mixed_patterns" in consistency
        assert "single_responsibility_violation" in consistency["issues"]

        # Should provide recommendations
        assert "recommendations" in consistency
        assert len(consistency["recommendations"]) >= 1

    @pytest.mark.unit
    def test_detects_pattern_variations(self):
        """Given pattern variations, when skill analyzes, then recognizes different implementations."""
        # Arrange
        singleton_variations = '''
# Classic Singleton
class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# Thread-safe Singleton
import threading

class ThreadSafeSingleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

# Metaclass Singleton
class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Logger(metaclass=SingletonMeta):
    pass
        '''

        # Act
        result = self.skill.detect_pattern_variations(singleton_variations, "singleton")

        # Assert
        variations = result["pattern_variations"]

        # Should detect all three singleton variations
        assert len(variations) == 3
        assert "classic_singleton" in variations
        assert "thread_safe_singleton" in variations
        assert "metaclass_singleton" in variations

        # Should analyze trade-offs
        assert "trade_offs" in result
        for variation in variations.values():
            assert "advantages" in variation
            assert "disadvantages" in variation

    @pytest.mark.unit
    def test_handles_incomplete_patterns(self):
        """Given incomplete patterns, when skill analyzes, then handles gracefully."""
        # Arrange
        incomplete_patterns = [
            "class Observer:",  # Incomplete class
            "def factory_method(",  # Incomplete method
            "interface Strategy {",  # Mixed language syntax
        ]

        # Act & Assert
        for pattern in incomplete_patterns:
            result = self.skill.recognize_patterns(pattern)

            # Should not crash and should provide partial analysis
            assert "recognized_patterns" in result or "error" in result
            if "error" not in result:
                assert result["confidence"] < 0.8  # Lower confidence for incomplete

    @pytest.mark.unit
    def test_generates_pattern_documentation(self):
        """Given recognized patterns, when skill analyzes, then generates documentation."""
        # Arrange
        well_structured_code = '''
class UserRepository:
    def save(self, user: User) -> None:
        """Save user to database."""
        pass

    def find_by_id(self, user_id: str) -> User:
        """Find user by ID."""
        pass

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_user(self, name: str, email: str) -> User:
        user = User(name=name, email=email)
        self.repository.save(user)
        return user
        '''

        # Act
        result = self.skill.generate_pattern_documentation(well_structured_code)

        # Assert
        docs = result["documentation"]

        # Should provide pattern descriptions
        assert "repository_pattern" in docs
        assert "service_pattern" in docs

        # Should provide usage examples
        for pattern_doc in docs.values():
            assert "description" in pattern_doc
            assert "usage" in pattern_doc
            assert "benefits" in pattern_doc

    @pytest.mark.unit
    def test_compares_pattern_alternatives(self):
        """Given multiple approaches, when skill analyzes, then compares alternatives."""
        # Arrange
        factory_alternatives = '''
# Simple Factory
def create_notification(type: str) -> Notification:
    if type == "email":
        return EmailNotification()
    elif type == "sms":
        return SMSNotification()
    else:
        raise ValueError("Unknown notification type")

# Abstract Factory
class NotificationFactory(ABC):
    @abstractmethod
    def create_email_notification(self) -> EmailNotification:
        pass

    @abstractmethod
    def create_sms_notification(self) -> SMSNotification:
        pass

class ModernNotificationFactory(NotificationFactory):
    def create_email_notification(self) -> EmailNotification:
        return ModernEmailNotification()

    def create_sms_notification(self) -> SMSNotification:
        return ModernSMSNotification()
        '''

        # Act
        result = self.skill.compare_pattern_alternatives(factory_alternatives, "factory")

        # Assert
        comparison = result["comparison"]

        # Should identify multiple factory patterns
        assert len(comparison["alternatives"]) >= 2

        # Should provide comparison matrix
        assert "comparison_matrix" in comparison
        matrix = comparison["comparison_matrix"]
        assert "flexibility" in matrix[0]
        assert "complexity" in matrix[0]

        # Should provide recommendations
        assert "recommendations" in comparison
        assert "when_to_use" in comparison["recommendations"]