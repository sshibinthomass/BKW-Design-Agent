"""
Test script to verify all dependencies are working correctly
Run this script to check if your environment is set up properly
"""

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    try:
        print("  ✓ Testing numpy...", end=" ")
        import numpy as np
        print(f"OK (v{np.__version__})")
    except ImportError as e:
        print(f"FAILED: {e}")
        return False
    
    try:
        print("  ✓ Testing pandas...", end=" ")
        import pandas as pd
        print(f"OK (v{pd.__version__})")
    except ImportError as e:
        print(f"FAILED: {e}")
        return False
    
    try:
        print("  ✓ Testing scipy...", end=" ")
        import scipy
        print(f"OK (v{scipy.__version__})")
        
        print("  ✓ Testing scipy.optimize...", end=" ")
        from scipy.optimize import minimize
        print("OK")
    except ImportError as e:
        print(f"FAILED: {e}")
        return False
    
    try:
        print("  ✓ Testing scikit-learn...", end=" ")
        import sklearn
        print(f"OK (v{sklearn.__version__})")
    except ImportError as e:
        print(f"FAILED: {e}")
        return False
    
    try:
        print("  ✓ Testing plotly...", end=" ")
        import plotly
        print(f"OK (v{plotly.__version__})")
    except ImportError as e:
        print(f"FAILED: {e}")
        return False
    
    try:
        print("  ✓ Testing flask...", end=" ")
        import flask
        print(f"OK (v{flask.__version__})")
    except ImportError as e:
        print(f"FAILED: {e}")
        return False
    
    try:
        print("  ✓ Testing anthropic...", end=" ")
        import anthropic
        print(f"OK (v{anthropic.__version__})")
    except ImportError as e:
        print(f"FAILED: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality"""
    print("\nTesting basic functionality...")
    
    try:
        print("  ✓ Testing numpy operations...", end=" ")
        import numpy as np
        arr = np.array([1, 2, 3, 4, 5])
        result = np.mean(arr)
        assert result == 3.0
        print("OK")
    except Exception as e:
        print(f"FAILED: {e}")
        return False
    
    try:
        print("  ✓ Testing pandas operations...", end=" ")
        import pandas as pd
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        assert len(df) == 3
        print("OK")
    except Exception as e:
        print(f"FAILED: {e}")
        return False
    
    try:
        print("  ✓ Testing scipy optimization...", end=" ")
        from scipy.optimize import minimize
        
        def objective(x):
            return x[0]**2 + x[1]**2
        
        result = minimize(objective, [1, 1], method='SLSQP')
        assert result.success
        print("OK")
    except Exception as e:
        print(f"FAILED: {e}")
        return False
    
    return True

def main():
    print("=" * 50)
    print("GenDesign - Dependency Test")
    print("=" * 50)
    
    if not test_imports():
        print("\n❌ Import tests FAILED!")
        print("Please run setup.bat again to reinstall dependencies")
        return False
    
    if not test_basic_functionality():
        print("\n❌ Functionality tests FAILED!")
        print("Dependencies are installed but not working correctly")
        return False
    
    print("\n✅ All tests PASSED!")
    print("Your environment is ready to run GenDesign")
    print("\nNext step: Run 'python app.py' or '.\\run.bat' to start the application")
    
    return True

if __name__ == "__main__":
    main()