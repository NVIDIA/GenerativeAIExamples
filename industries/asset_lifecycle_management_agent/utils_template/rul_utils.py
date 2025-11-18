"""
RUL (Remaining Useful Life) transformation utilities.

Provides pre-built functions for transforming RUL data to create realistic patterns
for Asset Lifecycle Management and predictive maintenance tasks.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


def apply_piecewise_rul_transformation(
    df: pd.DataFrame,
    maxlife: int = 100,
    time_col: str = 'time_in_cycles',
    rul_col: str = 'RUL'
) -> pd.DataFrame:
    """
    Transform RUL data to create realistic "knee" patterns.
    
    This function applies a piecewise transformation to RUL (Remaining Useful Life) values
    to create a more realistic degradation pattern commonly seen in predictive maintenance:
    - RUL stays constant at MAXLIFE until the remaining cycles drop below the threshold
    - Then RUL decreases linearly to 0 as the equipment approaches failure
    
    This creates the characteristic "knee" pattern seen in actual equipment degradation.
    
    Args:
        df: pandas DataFrame with time series data containing RUL values
        maxlife: Maximum life threshold for the piecewise function (default: 100)
                 RUL values above this will be capped at maxlife
        time_col: Name of the time/cycle column (default: 'time_in_cycles')
        rul_col: Name of the RUL column to transform (default: 'RUL')
    
    Returns:
        pandas DataFrame with original data plus new 'transformed_RUL' column
        
    Raises:
        ValueError: If required columns are missing from the DataFrame
        
    Example:
        >>> df = pd.DataFrame({'time_in_cycles': [1, 2, 3], 'RUL': [150, 100, 50]})
        >>> df_transformed = apply_piecewise_rul_transformation(df, maxlife=100)
        >>> print(df_transformed['transformed_RUL'])
        0    100
        1    100
        2     50
        Name: transformed_RUL, dtype: int64
    """
    # Validate inputs
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f"Expected pandas DataFrame, got {type(df)}")
    
    if rul_col not in df.columns:
        raise ValueError(
            f"RUL column '{rul_col}' not found in DataFrame. "
            f"Available columns: {list(df.columns)}"
        )
    
    if time_col not in df.columns:
        logger.warning(
            f"Time column '{time_col}' not found in DataFrame, but continuing anyway. "
            f"Available columns: {list(df.columns)}"
        )
    
    # Create a copy to avoid modifying the original
    df_copy = df.copy()
    
    logger.info(f"Applying piecewise RUL transformation with maxlife={maxlife}")
    logger.debug(f"Input RUL range: [{df_copy[rul_col].min()}, {df_copy[rul_col].max()}]")
    
    # Apply piecewise transformation
    def transform_rul(rul_value):
        """Apply the piecewise transformation to a single RUL value."""
        if pd.isna(rul_value):
            return rul_value  # Keep NaN values as NaN
        if rul_value > maxlife:
            return maxlife
        return rul_value
    
    # Apply transformation to create new column
    df_copy['transformed_RUL'] = df_copy[rul_col].apply(transform_rul)
    
    logger.info(
        f"✅ Transformation complete! Added 'transformed_RUL' column. "
        f"Output range: [{df_copy['transformed_RUL'].min()}, {df_copy['transformed_RUL'].max()}]"
    )
    logger.debug(f"Total rows processed: {len(df_copy)}")
    
    return df_copy


def show_utilities():
    """
    Display available utility functions and their usage.
    
    Prints a formatted list of all available utilities in this workspace,
    including descriptions and example usage.
    """
    utilities_info = """
    ================================================================================
    WORKSPACE UTILITIES - Asset Lifecycle Management
    ================================================================================
    
    Available utility functions:
    
    1. apply_piecewise_rul_transformation(df, maxlife=100, time_col='time_in_cycles', rul_col='RUL')
       
       Description:
         Transforms RUL (Remaining Useful Life) data to create realistic "knee" patterns
         commonly seen in predictive maintenance scenarios.
       
       Parameters:
         - df: pandas DataFrame with time series data
         - maxlife: Maximum life threshold (default: 100)
         - time_col: Name of time/cycle column (default: 'time_in_cycles')
         - rul_col: Name of RUL column to transform (default: 'RUL')
       
       Returns:
         DataFrame with original data plus new 'transformed_RUL' column
       
       Example:
         df_transformed = utils.apply_piecewise_rul_transformation(df, maxlife=100)
         print(df_transformed[['time_in_cycles', 'RUL', 'transformed_RUL']])
    
    2. show_utilities()
       
       Description:
         Displays this help message with all available utilities.
       
       Example:
         utils.show_utilities()
    
    ================================================================================
    """
    print(utilities_info)


if __name__ == "__main__":
    # Simple test
    print("RUL Utilities Module")
    print("=" * 50)
    show_utilities()

