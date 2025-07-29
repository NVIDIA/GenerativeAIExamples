def knee_RUL(cycle_list, max_cycle, MAXLIFE):
    '''
    Piecewise linear function with zero gradient and unit gradient
            ^
            |
    MAXLIFE |-----------
            |            \
            |             \
            |              \
            |               \
            |                \
            |----------------------->
    '''
    knee_RUL_values = []
    if max_cycle >= MAXLIFE:
        knee_point = max_cycle - MAXLIFE
        
        for i in range(0, len(cycle_list)):
            if i < knee_point:
                knee_RUL_values.append(MAXLIFE)
            else:
                tmp = knee_RUL_values[i - 1] - (MAXLIFE / (max_cycle - knee_point))
                knee_RUL_values.append(tmp)
    else:
        knee_point = MAXLIFE
        print("=========== knee_point < MAXLIFE ===========")
        for i in range(0, len(cycle_list)):
            knee_point -= 1
            knee_RUL_values.append(knee_point)
            
    return knee_RUL_values

def apply_piecewise_rul_to_data(df, cycle_col='time_in_cycles', max_life=125):
    """
    Apply piecewise RUL transformation to single-engine data.
    Uses original RUL values to determine proper failure point.
    
    Args:
        df (pd.DataFrame): Input dataframe (single engine)
        cycle_col (str): Column name for cycle/time
        max_life (int): Maximum life parameter for knee_RUL function
        
    Returns:
        pd.DataFrame: DataFrame with transformed RUL column
    """
    df_copy = df.copy()
    
    # Check if cycle column exists
    if cycle_col not in df_copy.columns:
        logger.warning(f"Cycle column '{cycle_col}' not found. Using row index as cycle.")
        df_copy[cycle_col] = range(1, len(df_copy) + 1)
    
    # Get cycle list for single engine
    cycle_list = df_copy[cycle_col].tolist()
    max_cycle_in_data = max(cycle_list)
    
    # Use original RUL values to determine true failure point
    # Following the original GitHub pattern: max_cycle = max(cycle_list) + final_rul
    # Get the final RUL value (RUL at the last cycle in our data)
    final_rul = df_copy.loc[df_copy[cycle_col] == max_cycle_in_data, 'actual_RUL'].iloc[0]
    # True failure point = last cycle in data + remaining RUL
    true_max_cycle = max_cycle_in_data + final_rul
    logger.info(f"Using original RUL data: final_rul={final_rul}, true_failure_cycle={true_max_cycle}")
    
    # Apply knee_RUL function with the true failure point
    rul_values = knee_RUL(cycle_list, true_max_cycle, max_life)
    
    # Replace actual_RUL column with piecewise values
    df_copy['actual_RUL'] = rul_values
    
    return df_copy