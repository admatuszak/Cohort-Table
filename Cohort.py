import pandas as pd
import numpy as np

class CohortTable:
    """
    Creates new cohort table class instance. 

    Keyword arguments:
    forecast_period (required) Int -- The length of the forecast period
    n_years (required) Int -- The length over which to 'ramp up' productivity from 0 to 100%
    hires_per_year (required) List of Integers -- How many employees will be hired each year, will be reshaped to fit forecast_period if necessary
    revenue_goal (required) Int -- The revenue per person when productivity is 100%
    annual_attrition (optional) Decimal -- Average percentage of attrition, expressed as decimal between 0 and 1. Default = .15.
    first_year_full_hire (optional) True / False -- Whether to use mid-point hiring for first year calculation. Default = False
    
    Functions:
    print_all_tables() -- Prints all of the resulting tables
    print_table() -- Prints specified table and allows for specific formatting
    """
    
    def __init__ (self, forecast_period, n_years, hires_per_year, revenue_goal, annual_attrition=.15, first_year_full_hire=False):
        self.forecast_period = forecast_period
        self.n_years = n_years
        self.hires_per_year = hires_per_year
        self.revenue_goal = revenue_goal
        self.annual_attrition = annual_attrition
        
        self.mask_zeros = np.zeros(shape=(self.forecast_period, self.forecast_period))
        self.mask_ones = np.ones(shape=(self.forecast_period, self.forecast_period))
        
        # Ensure hire_per_year list matches forecast_period
        self.hires_per_year = self.size_list(self.hires_per_year, self.forecast_period)
        
        self.create_productivity_df()
        self.create_fte_df(first_year_full_hire)
        self.create_revenue_df()
        
    def size_list(self, l, length, pad=0):
        if len(l) >= length:
            del l[length:]
        else:
            l.extend([pad] * (length - len(l)))
        
        return l
    
    def create_productivity_df(self):
        # Create productivity matrix by cohort and year using nested list comprehension
        productivity_list = [[min(max(n, 0)/self.n_years, 1) for n in range(1-i, self.forecast_period+1-i)] for i in range(self.forecast_period)]
        self.productivity_df = pd.DataFrame(productivity_list)
        
    def create_fte_df(self, first_year_full_hire):
        # Apply hiring plan to productivity matrix to derive FTE count by cohort and year
        fte_df = self.productivity_df.multiply(self.hires_per_year, axis=0)
        
        # Apply mid-point hiring to FTE DF to account for initial year (assumes hiring throughout, not at beginning of period)
        midpoint_mask = np.ones(shape = (self.forecast_period, self.forecast_period))
        np.fill_diagonal(midpoint_mask, .5)
        self.midpoint_mask_df = pd.DataFrame(midpoint_mask)
        
        # Check to see whether the first year hires exist at the beginning of the period
        if first_year_full_hire:
            self.midpoint_mask_df.iloc[0,0] = 1
        fte_df = fte_df.multiply(self.midpoint_mask_df)
        
        # Generate employee DF and associated attrition DF
        self.create_employee_df(fte_df)
        # Apply attrition mask to calculate retained employees over time
        self.fte_retained_df = fte_df.subtract(self.attrition_df)
        
    def create_attrition_tables(self):
        # Start with ndarray of all zeros of shape (forecast_period x forecast_period)
        # Add the annual rate of attrition to all elements of ndarray
        self.attrition_mask = np.add(self.mask_zeros, self.annual_attrition)
        # Take upper triangle of attrition rate elements and add ndarray of ones
        self.attrition_mask = np.add(self.mask_ones, np.triu(self.attrition_mask))
        self.attrition_mask = np.cumprod(self.attrition_mask, axis=1)
        # We only want to go to maximum value of 2 since we want the compounded percentage between 1 and 2
        self.attrition_mask = np.minimum(self.attrition_mask, 2)
        # Now we have ndarray of upper triangle of compounded attrition rates
        self.attrition_mask = np.subtract(self.attrition_mask, 1)
   
    def create_employee_df(self, fte_df):
        # Create upper triangle of employees
        self.employee_count_df = pd.DataFrame(self.mask_ones)
        self.employee_count_df = self.employee_count_df.multiply(self.hires_per_year, axis=0)
        self.employee_count = np.triu(self.employee_count_df) # Switch back to np as opposed to DF to extract upper triangle
        self.employee_count_df = pd.DataFrame(self.employee_count)

        # Calculate expected attrition by year and derive retained employees by cohort and year
        self.create_attrition_tables()
        self.attrition_df = self.employee_count_df.multiply(self.attrition_mask)
        self.retained_employee_count_df = self.employee_count_df.subtract(self.attrition_df).apply(np.ceil) # Use ceiling to keep whole employees
        
    def create_revenue_df(self):
        # Calculate revenue by cohort and year using retained FTE
        self.revenue_df = self.fte_retained_df.multiply(self.revenue_goal)
    
    def print_all_tables(self):
        self.print_table(self.fte_retained_df, 'FTE', 'FTE(Based on Productivity Ramp Up) by Year', 1)
        self.print_table(self.retained_employee_count_df, 'Employees', 'Employees, After Attrition, by Year', 0)
        self.print_table(self.revenue_df, 'Revenue', 'Total Revenue by Year', 0)
            
    def print_table(self, df, sum_title, table_title, precision=1):
        df.index.name='Cohort'
        sum_title = 'Sum of '+sum_title
        df.loc[sum_title] = df.sum()
        format_string = '{:,.' + str(precision) + 'f}'
        df_styled = df.style.format(format_string).set_caption(table_title)
        display(df_styled)