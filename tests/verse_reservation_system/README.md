# Verse Reservation System Tests

Comprehensive test suite for the NGÜ Bible Verse Sponsoring App's verse selection and reservation system.

## Overview

This test suite covers the critical functionality of the verse selection algorithm and the 15-minute reservation system that prevents race conditions during the checkout process.

## Test Structure

```
tests/verse_reservation_system/
├── conftest.py                      # Shared fixtures and test configuration
├── test_helpers.py                  # Factory functions and helper utilities
├── test_verse_selection.py          # Verse selection algorithm tests
├── test_reservation_system.py       # Reservation system and race condition tests
├── test_integration_checkout.py     # End-to-end checkout flow tests
└── README.md                        # This documentation
```

## Test Categories

### 1. Verse Selection Tests (`test_verse_selection.py`)

Tests the intelligent verse selection algorithm that powers `/vers-auswaehlen`.

**Core Functionality:**
- ✅ Adaptive score fallback (90 → 80 → 70 → ... → 0)
- ✅ Keyword bonus calculation (+2 points per positive keyword)
- ✅ Exclude IDs functionality for "Andere Verse anzeigen"
- ✅ Session persistence across navigation
- ✅ URL slug generation (jesaja-43-1)

**Edge Cases:**
- ✅ No verses available
- ✅ Insufficient verses for requested count
- ✅ All verses sponsored
- ✅ Invalid session data recovery
- ✅ Large exclude lists performance

### 2. Reservation System Tests (`test_reservation_system.py`)

Tests the 15-minute reservation system that prevents race conditions.

**Core Functionality:**
- ✅ Reservation creation and expiry (15 minutes)
- ✅ Extension mechanism for active sessions
- ✅ Race condition protection
- ✅ Active reservation queries
- ✅ Session-based reservation management

**Edge Cases:**
- ✅ Expired reservation cleanup
- ✅ Multiple reservations per session
- ✅ Concurrent access attempts
- ✅ Time-based expiry behavior
- ✅ Invalid verse ID handling

### 3. Integration Tests (`test_integration_checkout.py`)

Tests the complete user journey from verse selection to checkout.

**End-to-End Flows:**
- ✅ Complete checkout flow (select → type → data → summary)
- ✅ Session persistence across navigation
- ✅ Reservation extension throughout checkout
- ✅ "Andere Verse anzeigen" integration
- ✅ Multiple verse exploration patterns

**Error Scenarios:**
- ✅ Expired reservations during checkout
- ✅ Verses becoming sponsored during flow
- ✅ Invalid verse IDs and malformed URLs
- ✅ Session timeout handling
- ✅ Browser back button simulation

## Key Test Features

### Time-Based Testing with freezegun
```python
def test_reservation_lifecycle(self):
    with freeze_time("2025-01-01 10:00:00") as frozen_time:
        # Create reservation
        reservation = create_reservation()
        assert not reservation.is_expired
        
        # Test at different time points
        frozen_time.move_to("2025-01-01 10:15:00")
        assert reservation.is_expired
```

### Race Condition Testing
```python
def test_concurrent_access(self):
    # Two users try to reserve same verse
    with app.test_client() as client1, app.test_client() as client2:
        response1 = client1.get('/vers/jesaja-43-1/spendenart')
        response2 = client2.get('/vers/jesaja-43-1/spendenart')
        
        # Only one should succeed
        assert [response1.status_code, response2.status_code] == [200, 302]
```

### Factory Pattern for Test Data
```python
# Create verses with specific properties
verse = VerseFactory.create(
    book='TEST', chapter=1, verse=1,
    text='Contains Liebe and Hoffnung keywords',
    positivity_score=75
)

# Create reservations with time control
reservation = ReservationFactory.create_expired(
    verse_id=verse.id,
    minutes_ago=5
)
```

## Running the Tests

### Prerequisites
```bash
# Install test dependencies
pip install -r requirements.txt
```

### Basic Test Execution
```bash
# Run all tests in this suite
pytest tests/verse_reservation_system/ -v

# Run specific test file
pytest tests/verse_reservation_system/test_verse_selection.py -v

# Run with coverage
pytest tests/verse_reservation_system/ --cov=app --cov=models --cov-report=html
```

### Advanced Test Options
```bash
# Run tests matching pattern
pytest tests/verse_reservation_system/ -k "reservation" -v

# Run tests with output capture disabled (see print statements)
pytest tests/verse_reservation_system/ -s

# Run in parallel (if pytest-xdist installed)
pytest tests/verse_reservation_system/ -n auto

# Stop on first failure
pytest tests/verse_reservation_system/ -x
```

## Test Configuration

### Database Setup
Tests use an isolated SQLite database for each test function:
- ✅ Automatic database creation and cleanup
- ✅ Transaction rollback between tests
- ✅ No interference with development database

### Session Management
Custom session manager for testing:
```python
def test_session_behavior(session_manager):
    session_manager.set_featured_verses([1, 2, 3])
    session_manager.set_selected_verse(verse.id, reservation.id)
    
    session_data = session_manager.get_session_data()
    assert 'selected_verse_id' in session_data
```

### Response Parsing
HTML response parsing utilities:
```python
def test_verse_display(client):
    response = client.get('/vers-auswaehlen')
    verses = ResponseParser.get_verses_from_response(response)
    
    assert len(verses) == 3
    assert all('reference' in v for v in verses)
```

## Coverage Goals

### Minimum Coverage Targets
- **Overall**: 80% line coverage
- **Critical paths**: 100% (reservation creation, race condition protection)
- **Edge cases**: 90% (error handling, boundary conditions)

### Current Coverage Areas
- ✅ Verse.get_adaptive_featured_verses() method
- ✅ VerseReservation model methods
- ✅ /vers-auswaehlen route logic
- ✅ /vers/<verse_id>/spendenart route
- ✅ Checkout route validation
- ✅ Session management
- ✅ URL slug generation

## Test Data

### Sample Verses
The test suite includes carefully crafted sample verses:
- **High positivity scores** (90+): ISA 43:1, JER 29:11, ZEP 3:17
- **Medium scores** (70-89): PSA 23:1, PRO 3:5
- **Keyword bonus verses**: Contains "Liebe", "Hoffnung", "Frieden", etc.
- **Sponsored verses**: For exclusion testing
- **Edge case verses**: Various formats and corner cases

### Reservation Scenarios
- Active reservations (various expiry times)
- Expired reservations (for cleanup testing)
- Multiple session scenarios
- Concurrent access patterns

## Debugging Failed Tests

### Common Issues and Solutions

1. **Time-related test failures**
   ```bash
   # Check if freezegun is properly applied
   pytest tests/verse_reservation_system/test_reservation_system.py::test_reservation_lifecycle -v -s
   ```

2. **Database state issues**
   ```bash
   # Run tests individually to isolate
   pytest tests/verse_reservation_system/test_verse_selection.py::test_basic_verse_selection -v
   ```

3. **Session-related failures**
   ```bash
   # Check session configuration
   pytest tests/verse_reservation_system/test_integration_checkout.py::test_session_data_consistency -v -s
   ```

### Debug Mode
```python
# Add to test for debugging
import pdb; pdb.set_trace()

# Or use pytest debug on failure
pytest tests/verse_reservation_system/ --pdb
```

## Performance Considerations

### Database Queries
Tests include performance checks for:
- Large exclude lists in verse selection
- Multiple reservation queries
- Cleanup operations on large datasets

### Time Complexity
- Verse selection should remain efficient with 10,000+ verses
- Reservation queries should be fast with hundreds of active sessions
- Cleanup operations should scale linearly

## Future Test Extensions

### Planned Additions
- [ ] Load testing for concurrent users
- [ ] Memory usage profiling
- [ ] Database query optimization verification
- [ ] Cross-browser session compatibility
- [ ] Mobile-specific reservation behavior

### Integration Points
These tests are designed to integrate with:
- Stripe payment flow tests (future)
- Email notification tests (future)
- Certificate generation tests (future)
- Admin dashboard tests (future)

## Contributing

### Adding New Tests
1. Follow the existing naming convention: `test_descriptive_name`
2. Use appropriate fixtures from `conftest.py`
3. Include both happy path and error cases
4. Add docstrings explaining the test purpose
5. Use helper functions from `test_helpers.py`

### Test Quality Guidelines
- ✅ Each test should test one specific behavior
- ✅ Tests should be independent and not rely on order
- ✅ Use descriptive assertion messages
- ✅ Clean up any created data (handled automatically)
- ✅ Use appropriate mock data vs real data

---

## Summary

This test suite provides comprehensive coverage of the verse selection and reservation system, ensuring:

- **Reliability**: Core business logic is thoroughly tested
- **Race condition protection**: Multiple user scenarios are verified
- **User experience**: Complete checkout flows are validated
- **Error handling**: Edge cases and failures are covered
- **Performance**: Scalability considerations are tested

The tests serve as both quality assurance and documentation of how the system should behave under various conditions.