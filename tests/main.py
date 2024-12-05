from matching.test import test_matching

if __name__ == "__main__":
    assert test_matching(), "Parent matching tests failed!"

    print("=" * 80)
    print("All tests passed!")
    print("=" * 80)
