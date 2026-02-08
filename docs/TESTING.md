# Testing Documentation - M3 Timetable System

## Testing Strategy

### Overview
The M3 Timetable System uses a comprehensive testing strategy covering unit tests, integration tests, and manual testing to ensure system reliability and correctness.

---

## Testing Tools

### Backend Testing
- **pytest**: Primary testing framework
- **pytest-django**: Django integration for pytest
- **pytest-cov**: Code coverage reporting
- **Python**: 3.13.5

### Frontend Testing (Planned for Sprint 2)
- **Vitest**: Fast unit testing framework
- **React Testing Library**: Component testing
- **Jest**: Additional testing utilities

---

## Test Coverage

### Current Test Suite (Sprint 1)

#### Unit Tests - Models (`tests/test_models.py`)
✅ **17 tests - 100% passing**

**Test Classes:**
1. `TestTeacherModel` - 2 tests
   - Create teacher
   - Validate max hours constraint
   
2. `TestCourseModel` - 2 tests
   - Create theory course
   - Create lab course
   
3. `TestRoomModel` - 2 tests
   - Create classroom
   - Create lab room
   
4. `TestTimeSlotModel` - 1 test
   - Create time slot
   
5. `TestSectionModel` - 1 test
   - Create section
   
6. `TestScheduleModel` - 1 test
   - Create schedule
   
7. `TestTeacherCourseMapping` - 1 test
   - Create teacher-course mapping

#### Unit Tests - Constraints (`tests/test_constraints.py`)
✅ **7 tests - 100% passing**

**Test Classes:**
1. `TestConstraintValidator` - 7 tests
   - Faculty availability (valid)
   - Faculty availability (conflict)
   - Room availability (valid)
   - Room type match (valid)
   - Room type match (invalid - lab in classroom)
   - Section availability (valid)
   - Validate all constraints (success)

---

## Running Tests

### Run All Tests
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_models.py -v
pytest tests/test_constraints.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=core --cov=scheduler --cov-report=html
```

### View Coverage Report
```bash
open htmlcov/index.html
```

---

## Test Results (Sprint 1)

### Summary
```
======================== test session starts ========================
collected 17 items

tests/test_constraints.py::TestConstraintValidator::test_faculty_availability_valid PASSED
tests/test_constraints.py::TestConstraintValidator::test_faculty_availability_conflict PASSED
tests/test_constraints.py::TestConstraintValidator::test_room_availability_valid PASSED
tests/test_constraints.py::TestConstraintValidator::test_room_type_match_valid PASSED
tests/test_constraints.py::TestConstraintValidator::test_room_type_match_invalid PASSED
tests/test_constraints.py::TestConstraintValidator::test_section_availability_valid PASSED
tests/test_constraints.py::TestConstraintValidator::test_validate_all_success PASSED
tests/test_models.py::TestTeacherModel::test_create_teacher PASSED
tests/test_models.py::TestTeacherModel::test_teacher_max_hours_validation PASSED
tests/test_models.py::TestCourseModel::test_create_course PASSED
tests/test_models.py::TestCourseModel::test_lab_course PASSED
tests/test_models.py::TestRoomModel::test_create_classroom PASSED
tests/test_models.py::TestRoomModel::test_create_lab PASSED
tests/test_models.py::TestTimeSlotModel::test_create_timeslot PASSED
tests/test_models.py::TestSectionModel::test_create_section PASSED
tests/test_models.py::TestScheduleModel::test_create_schedule PASSED
tests/test_models.py::TestTeacherCourseMapping::test_create_mapping PASSED

======================== 17 passed in 0.15s ========================
```

**Pass Rate**: 100% (17/17)  
**Execution Time**: 0.15 seconds

---

## Integration Testing

### Manual Integration Tests Performed

1. **Data Import Flow** ✅
   - CSV files → Database
   - Verified 1,300+ records imported correctly
   
2. **Schedule Generation Flow** ✅
   - API call → Algorithm → Database
   - Verified schedule entries created
   - Verified conflict detection
   
3. **Frontend-Backend Integration** ✅
   - API calls from React → Django
   - Data display in UI
   - Filter functionality
   
4. **Constraint Validation** ✅
   - Faculty double-booking prevention
   - Room double-booking prevention
   - Lab room type matching

---

## Test Data

### Fixtures
Test data is created dynamically in each test using Django ORM:
- Teachers with valid/invalid constraints
- Courses (theory and lab)
- Rooms (classroom and lab)
- Time slots
- Sections
- Schedules

### Real Data Testing
System tested with actual campus data:
- 86 teachers
- 165 courses
- 44 rooms
- 40 time slots
- 32 sections
- 924 teacher-course mappings

---

## Code Coverage Goals

### Sprint 1 Target
- **Models**: 80%+ coverage ✅
- **Constraints**: 80%+ coverage ✅
- **Algorithm**: 60%+ coverage ✅
- **API Views**: 50%+ coverage ✅

### Sprint 2 Target
- **Overall**: 85%+ coverage
- **Critical paths**: 95%+ coverage
- **Frontend**: 70%+ coverage

---

## Testing Best Practices

### Followed Practices
1. ✅ Test isolation (each test independent)
2. ✅ Descriptive test names
3. ✅ Arrange-Act-Assert pattern
4. ✅ Test both success and failure cases
5. ✅ Use fixtures for setup
6. ✅ Mock external dependencies

### Code Quality
- All tests have docstrings
- Clear assertion messages
- Proper error handling
- Database cleanup after tests

---

## Known Issues & Limitations

### Sprint 1
- Frontend tests not yet implemented (planned for Sprint 2)
- API endpoint tests limited (basic functionality tested)
- Performance tests not included
- Load testing not performed

### To Be Addressed in Sprint 2
- Add API integration tests
- Add frontend component tests
- Add end-to-end tests
- Add performance benchmarks
- Add load testing

---

## Continuous Integration (Sprint 2)

### Planned CI/CD Pipeline
```yaml
# GitHub Actions workflow (planned)
- Checkout code
- Set up Python 3.13
- Install dependencies
- Run migrations
- Run pytest with coverage
- Upload coverage report
- Deploy if tests pass
```

---

## Test Maintenance

### Adding New Tests
1. Create test file in `tests/` directory
2. Import required models/functions
3. Use `@pytest.mark.django_db` decorator
4. Write test methods starting with `test_`
5. Run tests to verify
6. Update this documentation

### Test Naming Convention
- File: `test_<module>.py`
- Class: `Test<ClassName>`
- Method: `test_<functionality>_<scenario>`

---

## Conclusion

Sprint 1 testing demonstrates:
- ✅ Solid foundation with 17 passing tests
- ✅ 100% pass rate
- ✅ Core functionality validated
- ✅ Constraint system verified
- ✅ Integration tested manually

**Next Steps**: Expand test coverage in Sprint 2 with API tests, frontend tests, and automated CI/CD pipeline.

---

**Last Updated**: February 7, 2026  
**Sprint**: 1  
**Test Engineer**: Kanishthika (Team 10)
