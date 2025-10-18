import os
import pandas as pd
import numpy as np
import warnings
import csv
import joblib
from scipy.optimize import minimize

warnings.filterwarnings("ignore")

def load_trained_model():
    """Load the trained model and artifacts"""
    if not os.path.exists("ai_agent\\model_status_predict"):
        raise FileNotFoundError(
            "Models directory not found. Please run train mode first."
        )

    model_path = "ai_agent\\model_status_predict\\models\\random_forest_model.joblib"
    encoder_path = "ai_agent\\model_status_predict\\models\\label_encoder.joblib"

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found: {model_path}. Please run train mode first."
        )

    if not os.path.exists(encoder_path):
        raise FileNotFoundError(
            f"Label encoder not found: {encoder_path}. Please run train mode first."
        )

    try:
        model = joblib.load(model_path)
        label_encoder = joblib.load(encoder_path)

        print(f"Loaded model: {model_path}")
        print(f"Loaded encoder: {encoder_path}")

        return model, label_encoder
    except Exception as e:
        raise FileNotFoundError(f"Error loading model or encoder: {e}")


def predict_deflection(
    model, label_encoder, length, material, height, width, force=10000
):
    """Predict deflection for given parameters"""
    # Prepare input data
    input_data = pd.DataFrame(
        {
            "L (mm)": [length],
            "h (mm)": [height],
            "w (mm)": [width],
            "Material_encoded": [label_encoder.transform([material])[0]],
        }
    )

    # Create engineered features (same as in training)
    input_data["cross_sectional_area"] = input_data["w (mm)"] * input_data["h (mm)"]
    input_data["second_moment_area"] = (
        input_data["w (mm)"] * input_data["h (mm)"] ** 3
    ) / 12
    input_data["length_cubed"] = input_data["L (mm)"] ** 3
    input_data["aspect_ratio"] = input_data["L (mm)"] / input_data["h (mm)"]
    input_data["width_height_ratio"] = input_data["w (mm)"] / input_data["h (mm)"]
    input_data["deflection_factor"] = (
        input_data["length_cubed"] / input_data["second_moment_area"]
    )
    input_data["slenderness"] = input_data["L (mm)"] / np.sqrt(
        input_data["cross_sectional_area"]
    )
    input_data["L_h_interaction"] = input_data["L (mm)"] * input_data["h (mm)"]
    input_data["L_w_interaction"] = input_data["L (mm)"] * input_data["w (mm)"]
    input_data["h_w_interaction"] = input_data["h (mm)"] * input_data["w (mm)"]

    # Ensure the features are in the exact same order as during training
    # The expected order from feature_engineering function is:
    expected_columns = [
        "L (mm)",
        "h (mm)",
        "w (mm)",
        "Material_encoded",
        "cross_sectional_area",
        "second_moment_area",
        "length_cubed",
        "aspect_ratio",
        "width_height_ratio",
        "deflection_factor",
        "slenderness",
        "L_h_interaction",
        "L_w_interaction",
        "h_w_interaction",
    ]

    # Reorder columns to match training
    input_data = input_data[expected_columns]

    # Predict deflection
    predicted_deflection = model.predict(input_data)[0]
    return predicted_deflection


def check_design_status(deflection, allowable_deflection):
    """Check if design passes or fails"""
    return "PASS" if deflection <= allowable_deflection else "FAIL"


def find_best_historical_design(historical_data, length, material):
    """Find the best design from historical data for same length and material"""
    # Filter historical data for same length and material with PASS or OPT status
    try:
        # Allow small tolerance on length instead of exact equality
        length = float(length)
    except Exception:
        pass
    length_tolerance = length * 0.2 if isinstance(length, (int, float)) else 0
    filtered_data = historical_data[
        (historical_data["Material"] == material)
        & (
            (
                (historical_data["L (mm)"] >= length - length_tolerance)
                & (historical_data["L (mm)"] <= length + length_tolerance)
            )
            if length_tolerance > 0
            else (historical_data["L (mm)"] == length)
        )
        & (historical_data["Status"].isin(["PASS", "OPT"]))
    ]

    if filtered_data.empty:
        return None, None

    # Find design with minimum volume
    best_design = filtered_data.loc[filtered_data["V (mm^3)"].idxmin()]
    return best_design, filtered_data


def optimize_design(length, material, force, historical_data=None, user_height=None, user_width=None):
    """Simplified optimization using only SciPy with physics-based calculations"""
    
    # Validate input parameters
    if length <= 0 or force <= 0:
        print(f"Invalid parameters: length={length}, force={force}")
        return None, None, None, None
    
    if user_height is not None and user_height <= 0:
        print(f"Invalid user_height: {user_height}")
        return None, None, None, None
        
    if user_width is not None and user_width <= 0:
        print(f"Invalid user_width: {user_width}")
        return None, None, None, None
    
    def objective(x):
        """Minimize volume"""
        height, width = x
        return length * height * width
    
    def constraint_deflection(x):
        """Ensure deflection <= L/240 using physics"""
        height, width = x
        if height <= 0 or width <= 0:
            return -1e6
        
        try:
            deflection = calculate_beam_deflection(
                load=force,
                material=material,
                span=length,
                width=width,
                height=height,
                load_type="point"
            )
            allowable = length / 240
            constraint_value = allowable - deflection  # > 0 for valid design
            return constraint_value
        except Exception as e:
            print(f"Error in constraint calculation: {e}")
            return -1e6
    
    # Set bounds and initial guess based on realistic structural requirements
    if user_height and user_width:
        # Start with user dimensions but allow significant variation
        bounds = [
            (max(10, user_height / 10), user_height * 10),  # height bounds
            (max(10, user_width / 10), user_width * 10)     # width bounds
        ]
        initial_guess = [user_height, user_width]
    else:
        # Default bounds based on length - more conservative
        min_height = max(20, length / 100)   # minimum reasonable height
        max_height = length / 3              # maximum reasonable height
        min_width = max(10, length / 200)    # minimum reasonable width  
        max_width = length / 5               # maximum reasonable width
        
        bounds = [
            (min_height, max_height),   # height bounds
            (min_width, max_width)      # width bounds
        ]
        # Start with a reasonable guess - larger dimensions for safety
        initial_guess = [length / 15, length / 20]
    
    # Try multiple initial guesses to avoid linesearch issues
    initial_guesses = [
        initial_guess,
        [initial_guess[0] * 1.5, initial_guess[1] * 1.5],  # Larger dimensions
        [initial_guess[0] * 0.7, initial_guess[1] * 1.3],  # Different proportions
        [max(bounds[0][0] + 10, initial_guess[0] * 0.5), 
         max(bounds[1][0] + 5, initial_guess[1] * 0.8)]    # Conservative fallback
    ]
    
    # Multiple optimization attempts with different strategies and initial guesses
    optimization_methods = ['trust-constr', 'SLSQP']  # Start with trust-constr (more robust)
    
    for method in optimization_methods:
        for i, guess in enumerate(initial_guesses):
            try:
                print(f"Trying optimization with {method} method (attempt {i+1}/4)...")
                
                # Ensure initial guess is within bounds
                guess[0] = max(bounds[0][0], min(bounds[0][1], guess[0]))
                guess[1] = max(bounds[1][0], min(bounds[1][1], guess[1]))
                
                if method == 'trust-constr':
                    # trust-constr handles constraints differently
                    constraints = [{'type': 'ineq', 'fun': constraint_deflection}]
                    result = minimize(
                        objective,
                        guess,
                        method=method,
                        bounds=bounds,
                        constraints=constraints,
                        options={'maxiter': 1000, 'xtol': 1e-8, 'gtol': 1e-6}
                    )
                else:
                    # SLSQP with improved tolerance settings
                    result = minimize(
                        objective,
                        guess,
                        method=method,
                        bounds=bounds,
                        constraints={'type': 'ineq', 'fun': constraint_deflection},
                        options={'maxiter': 1000, 'ftol': 1e-8, 'eps': 1e-8}
                    )
                
                if result.success and constraint_deflection(result.x) > 0:
                    opt_height, opt_width = result.x
                    opt_volume = result.fun
                    opt_deflection = calculate_beam_deflection(
                        force, material, length, opt_width, opt_height, "point"
                    )
                    print(f"Optimization successful with {method}: {opt_width:.1f}x{opt_height:.1f} mm")
                    return opt_height, opt_width, opt_volume, opt_deflection
                else:
                    error_msg = getattr(result, 'message', 'No feasible solution found')
                    print(f"Optimization with {method} (attempt {i+1}) failed: {error_msg}")
                    
            except Exception as e:
                print(f"Optimization with {method} (attempt {i+1}) error: {e}")
                continue
    
    # Smart iterative approach: find minimum feasible design
    print("Trying intelligent feasibility search...")
    try:
        # Start with dimensions that should work
        test_height = length / 10  # Conservative starting point
        test_width = length / 15
        
        best_solution = None
        best_volume = float('inf')
        
        # Test multiple scaling strategies to find minimum feasible volume
        scale_ranges = [
            [1.0, 1.5, 2.0, 2.5, 3.0],  # Conservative range
            [0.8, 1.0, 1.2, 1.4, 1.6],  # Try smaller first
            [0.5, 0.7, 0.9, 1.1, 1.3],  # Even smaller
        ]
        
        for scale_set in scale_ranges:
            for scale in scale_set:
                h = test_height * scale
                w = test_width * scale
                
                # Ensure minimum practical dimensions
                if h < 20 or w < 10:
                    continue
                    
                constraint_val = constraint_deflection([h, w])
                if constraint_val > 0:  # Feasible solution
                    volume = objective([h, w])
                    if volume < best_volume:
                        best_volume = volume
                        deflection = calculate_beam_deflection(
                            force, material, length, w, h, "point"
                        )
                        best_solution = (h, w, volume, deflection)
                        print(f"Found better solution: {w:.1f}x{h:.1f} mm, Volume: {volume/1e6:.1f}M mm³")
        
        if best_solution:
            h, w, vol, defl = best_solution
            print(f"Optimal solution found: {w:.1f}x{h:.1f} mm")
            return h, w, vol, defl
        else:
            print("No feasible solution found in tested range")
            return None, None, None, None
        
    except Exception as e:
        print(f"Intelligent search error: {e}")
        return None, None, None, None


def update_historical_data(length, material, width, height, deflection, volume, status, 
                         force=None, shape=None, design_type="Beam", file_path=None):
    """Update historical data CSV file with all required columns"""
    if file_path is None:
        # Use relative path compatible with web app
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, "extracted_historical_data_00.csv")
        
        # If not found, try parent directory
        if not os.path.exists(file_path):
            parent_dir = os.path.dirname(os.path.dirname(current_dir))
            file_path = os.path.join(parent_dir, "extracted_historical_data_00.csv")
    
    # Determine shape based on material if not provided
    if shape is None:
        if material.lower() == "steel":
            shape = "IPE"
        elif material.lower() in ["concrete", "wood"]:
            shape = "Rectangular"
        else:
            shape = "Custom"
    
    # Calculate derived fields
    allowable_deflection = length / 240
    def_ratio = (deflection / allowable_deflection) * 100 if allowable_deflection > 0 else 0
    
    # Generate reason text
    if status in ["PASS", "OPT"]:
        reason = f"Deflection: {deflection:.1f} mm < Allowable Deflection = {allowable_deflection:.1f} mm"
    else:
        reason = f"Excessive Deflection: {deflection:.1f} mm and Allowable Deflection = {allowable_deflection:.1f} mm"
    
    # Generate design file name
    import time
    timestamp = int(time.time())
    design_file_name = f"{length}_{design_type}_{material}_{shape}_{height}_{width}_{force or 'Unknown'}_{timestamp}.json"
    
    # Complete data record with all columns
    new_data = {
        "Design file Name": design_file_name,
        "L (mm)": length,
        "Type": design_type,
        "Material": material,
        "Shape": shape,
        "h (mm)": height,
        "w (mm)": width,
        "F (N)": force if force is not None else 0,
        "V (mm^3)": volume,
        "Deflection (mm)": deflection,
        "Allowable_Def (mm) L/240": allowable_deflection,
        "Def_Ratio %": def_ratio,
        "Status": status,
        "Reason": reason,
        # Fill remaining unnamed columns with empty strings
        **{f"Unnamed: {i}": "" for i in range(14, 30)}
    }

    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        else:
            # Create with proper column order if file doesn't exist
            columns = ["Design file Name", "L (mm)", "Type", "Material", "Shape", 
                      "h (mm)", "w (mm)", "F (N)", "V (mm^3)", "Deflection (mm)",
                      "Allowable_Def (mm) L/240", "Def_Ratio %", "Status", "Reason"] + \
                     [f"Unnamed: {i}" for i in range(14, 30)]
            df = pd.DataFrame([new_data], columns=columns)

        df.to_csv(file_path, index=False)
        print(f"Historical data updated: {file_path}")
    except Exception as e:
        print(f"Error updating historical data: {e}")


def inference_mode(input_data):
    """Execute inference mode - calculate deflection using AI model or physics based on environment variable"""
    print("=" * 60)
    print("BEAM DEFLECTION PREDICTION - INFERENCE MODE")
    print("=" * 60)
    results = {}

    try:
        # Parse input parameters
        try:
            # Extract numerical values from string format
            force = float(input_data["Load"].replace(" N", ""))
            material = input_data["Material"].strip().capitalize()
            length = float(input_data["Length"].replace(" mm", ""))
            height = float(input_data["Height"].replace(" mm", ""))
            width = float(input_data["Width"].replace(" mm", ""))

            print("Parsed parameters:")
            print(f"  Force: {force} N")
            print(f"  Material: {material}")
            print(f"  Length: {length} mm")
            print(f"  Height: {height} mm")
            print(f"  Width: {width} mm")

        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid input format: {e}")

        # Calculate design properties
        volume = length * height * width
        allowable_deflection = length / 240

        print("\nDesign Analysis:")
        print(f"Volume: {volume:,.0f} mm³")
        print(f"Allowable Deflection: {allowable_deflection:.2f} mm")

        # Check environment variable for calculation method
        use_ai_inference = os.getenv('USE_AI_INFERENCE', 'true').lower() == 'true'
        
        if use_ai_inference:
            print("Using AI model for deflection prediction...")
            try:
                # Load the trained model and label encoder
                model, label_encoder = load_trained_model()
                
                # Use AI model to predict deflection
                predicted_deflection = predict_deflection(
                    model=model,
                    label_encoder=label_encoder,
                    length=length,
                    material=material,
                    height=height,
                    width=width,
                    force=force
                )
                
                print(f"AI Predicted Deflection: {predicted_deflection:.2f} mm")
                
            except Exception as e:
                print(f"AI model error: {e}")
                print("Falling back to physics-based calculation...")
                use_ai_inference = False
        
        if not use_ai_inference:
            print("Using physics-based calculation for deflection...")
            try:
                # Use physics-based calculation
                predicted_deflection = calculate_beam_deflection(
                    load=force,
                    material=material,
                    span=length,
                    width=width,
                    height=height,
                    load_type="point"
                )
                
                print(f"Physics Calculated Deflection: {predicted_deflection:.2f} mm")
                
            except Exception as e:
                raise ValueError(f"Error calculating deflection with physics: {e}")
        
        # Convert status to boolean (True for PASS, False for FAIL)
        status_text = check_design_status(predicted_deflection, allowable_deflection)
        status = True if status_text == "PASS" else False
        
        calculation_method = "AI Model" if use_ai_inference else "Physics-based"
        print(f"Calculation Method: {calculation_method}")
        print(f"Design Status: {'PASS' if status else 'FAIL'}")

        results = {
            "Load": f"{force} N",
            "Material": material,
            "Length": f"{length} mm",
            "Height": f"{height} mm",
            "Width": f"{width} mm",
            "Volume_mm3": float(volume),
            "Allowable_Deflection_mm": float(allowable_deflection),
            "Predicted_Deflection_mm": float(predicted_deflection),
            "Status": status,
            "Calculation_Method": calculation_method,
        }

        print("\n" + "=" * 60)
        print("INFERENCE COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as e:
        print(f"Error during inference: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return results

def get_closest_I_by_height(target_height_mm, csv_path=None):
    """
    Finds the closest IPE beam by height and returns its moment of inertia (I).

    Parameters:
    - target_height_mm (int or float): desired beam height in mm
    - csv_path (str): path to IPE dimensions CSV file

    Returns:
    - int: Moment of inertia (I) in mm⁴
    - fallback calculation if file not found
    """
    if csv_path is None:
        # Use relative path compatible with web app
        current_dir = os.path.dirname(__file__)
        csv_path = os.path.join(current_dir, 'ipe_beams_dims.csv')
    
    closest_I = None
    min_diff = float('inf')

    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    height = float(row['h (mm)'])
                    diff = abs(height - target_height_mm)
                    if diff < min_diff:
                        min_diff = diff
                        closest_I = int(row['I (mm^4)'])
                except (ValueError, KeyError):
                    continue
    except FileNotFoundError:
        print(f"IPE dimensions file not found: {csv_path}")
        # Fallback to rectangular approximation
        return (100 * target_height_mm**3) / 12

    return closest_I if closest_I is not None else (100 * target_height_mm**3) / 12


def calculate_beam_deflection(load, material, span, width, height, load_type="point"):
    """
    Calculate deflection using proper material properties and geometry.

    Parameters:
    - load: Load in N (point) or N/mm (distributed)
    - material: Material type ('steel', 'wood', 'concrete')
    - span: Span length in mm
    - width: Beam width in mm
    - height: Beam height in mm
    - load_type: 'point' or 'distributed'

    Returns:
    - float: Deflection in mm
    """
    # Material properties
    modulus_map = {
        "steel": 200000,    # N/mm² for steel
        "wood": 11000,     # N/mm² for wood
        "concrete": 30000  # N/mm² for concrete
    }
    
    E = modulus_map.get(material.lower(), 200000)
    
    # Calculate moment of inertia based on material
    if material.lower() == "steel":
        # Use IPE beam lookup for steel
        moment_of_inertia = get_closest_I_by_height(height)
    else:
        # Rectangular cross-section for wood and concrete
        moment_of_inertia = (width * height**3) / 12
    
    # Deflection calculation
    if load_type == "point":
        return (load * span**3) / (48 * E * moment_of_inertia)
    else:  # distributed
        return (5 * load * span**4) / (384 * E * moment_of_inertia)


def find_efficient_standard_beam(target_volume, length, material, force, csv_path=None):
    """
    Find standard IPE beam that is more efficient than custom solution.
    Only recommends IPE beams for Steel material.
    
    Returns:
    - dict: Best standard beam info or None if no improvement or non-steel material
    """
    # Only recommend IPE beams for Steel material
    if material.lower() != 'steel':
        return None
        
    if csv_path is None:
        current_dir = os.path.dirname(__file__)
        csv_path = os.path.join(current_dir, 'ipe_beams_dims.csv')
    
    if not os.path.exists(csv_path):
        return None
    
    best_standard = None
    
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
        
        for _, row in df.iterrows():
            try:
                height = float(row['h (mm)'])
                width = float(row['b (mm)'])  # Assuming flange width
                area = float(row.get('A (mm^2)', height * width * 0.7))  # Approximation if area not available
                beam_volume = area * length
                
                # Check if beam is structurally safe
                deflection = calculate_beam_deflection(
                    load=force, material=material, span=length,
                    width=width, height=height, load_type="point"
                )
                allowable = length / 240
                
                if deflection <= allowable and beam_volume < target_volume:
                    if best_standard is None or beam_volume < best_standard['volume']:
                        best_standard = {
                            'profile': row.get('Profile', f'IPE{int(height)}'),
                            'height': height,
                            'width': width,
                            'volume': beam_volume,
                            'deflection': deflection,
                            'efficiency_gain': ((target_volume - beam_volume) / target_volume) * 100
                        }
            except (ValueError, KeyError) as e:
                continue
                
    except Exception as e:
        print(f"Error checking standard beams: {e}")
        return None
    
    return best_standard


def optimize_mode_for_webapp(length, material, force, user_height=None, user_width=None):
    """Optimize beam design for web app integration"""
    try:
        # Load historical data if available
        historical_data = None
        try:
            current_dir = os.path.dirname(__file__)
            hist_path = os.path.join(current_dir, "extracted_historical_data_00.csv")
            if not os.path.exists(hist_path):
                parent_dir = os.path.dirname(os.path.dirname(current_dir))
                hist_path = os.path.join(parent_dir, "extracted_historical_data_00.csv")
            
            if os.path.exists(hist_path):
                historical_data = pd.read_csv(hist_path)
        except Exception as e:
            print(f"Could not load historical data: {e}")
        
        # Run optimization
        result = optimize_design(length, material, force, historical_data, user_height, user_width)
        
        if all(x is not None for x in result):
            opt_height, opt_width, opt_volume, opt_deflection = result
            
            # Calculate comparison with user's original design if provided
            result_data = {
                'success': True,
                'height': opt_height,
                'width': opt_width,
                'volume': opt_volume,
                'deflection': opt_deflection,
                'allowable_deflection': length / 240
            }
            
            if user_height and user_width:
                # Check if original design is structurally safe
                original_deflection = calculate_beam_deflection(
                    load=force, material=material, span=length,
                    width=user_width, height=user_height, load_type="point"
                )
                original_volume = length * user_height * user_width
                volume_change_percent = ((opt_volume - original_volume) / original_volume) * 100
                is_improvement = opt_volume < original_volume
                original_is_safe = original_deflection <= (length / 240)
                
                # Determine optimization category
                if original_is_safe and is_improvement:
                    optimization_category = 'optimization_success'
                    assessment = f'Material reduction achieved: {abs(volume_change_percent):.1f}% less volume'
                elif original_is_safe and not is_improvement:
                    optimization_category = 'design_feasible'
                    assessment = 'Original design is adequate. Alternative design uses more material.'
                elif not original_is_safe and is_improvement:
                    optimization_category = 'safety_upgrade_efficient'
                    assessment = f'Safety improved with {abs(volume_change_percent):.1f}% less material'
                else:  # not original_is_safe and not is_improvement
                    optimization_category = 'safety_upgrade'
                    assessment = f'Original design unsafe. Minimum safe design requires {volume_change_percent:.1f}% more material for structural safety'
                
                result_data.update({
                    'original_volume': original_volume,
                    'original_deflection': original_deflection,
                    'original_is_safe': original_is_safe,
                    'volume_change_percent': volume_change_percent,
                    'is_improvement': is_improvement,
                    'optimization_category': optimization_category,
                    'assessment': assessment
                })
            else:
                result_data.update({
                    'optimization_category': 'minimum_feasible',
                    'assessment': 'Minimum feasible design found'
                })
            
            # Check for more efficient standard beam alternatives
            if result_data['optimization_category'] in ['safety_upgrade', 'minimum_feasible']:
                standard_beam = find_efficient_standard_beam(
                    opt_volume, length, material, force
                )
                if standard_beam:
                    result_data.update({
                        'standard_beam_alternative': standard_beam,
                        'has_better_standard': True,
                        'assessment': result_data['assessment'] + f" Consider {standard_beam['profile']} beam: {standard_beam['efficiency_gain']:.1f}% more efficient."
                    })
                else:
                    result_data['has_better_standard'] = False
            
            # Update historical data - Convert float optimization results to integers
            update_historical_data(length, material, int(round(opt_width)), int(round(opt_height)), 
                                   opt_deflection, opt_volume, "OPT", 
                                   force=force, design_type="Beam")
            
            return result_data
        else:
            return {'success': False, 'error': 'No feasible optimization solution found within constraints'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}


if __name__ == "__main__":
    # For testing purposes only
    print("Script loaded successfully. Use optimize_mode_for_webapp() for web app integration.")
