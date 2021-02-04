import pandas as pd
import numpy as np
from IPython.display import display, Markdown

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
    attrition_y0 (optional) True / False -- Should attrition occur in first year of hiring. Default = False
    
    Functions:
    print_all_tables() -- Prints all of the resulting tables
    print_table() -- Prints specified table and allows for specific formatting
    """
    
    def __init__ (self, forecast_period, n_years, hires_per_year, revenue_goal, annual_attrition=.15, \
                  first_year_full_hire=False, attrition_y0=False):
        self.forecast_period = forecast_period
        self.n_years = n_years
        self.hires_per_year = hires_per_year
        self.revenue_goal = revenue_goal
        self.annual_attrition = annual_attrition
        self.attrition_y0 = attrition_y0
        
        self.mask_zeros = np.zeros(shape=(self.forecast_period, self.forecast_period))
        self.mask_ones = np.ones(shape=(self.forecast_period, self.forecast_period))
        
        # Ensure hire_per_year list matches forecast_period
        self.hires_per_year = self.size_list(self.hires_per_year, self.forecast_period)
        
        self.create_productivity_df()
        self.create_employee_df()
        self.create_attrition_tables()
        self.create_retained_employee_count_df()
        self.apply_midpoint_hiring(first_year_full_hire)
        self.apply_productivity_ramp()
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
        
    def create_employee_df(self):
        # Create upper triangle of employees
        self.employee_count_df = pd.DataFrame(self.mask_ones)
        self.employee_count_df = self.employee_count_df.multiply(self.hires_per_year, axis=0)
        self.employee_count = np.triu(self.employee_count_df) # Switch back to np as opposed to DF to extract upper triangle
        self.employee_count_df = pd.DataFrame(self.employee_count)
    
    def create_attrition_tables(self):
        # Start with ndarray of all zeros of shape (forecast_period x forecast_period)
        # Add the annual rate of attrition to all elements of ndarray
        self.attrition_mask = np.add(self.mask_zeros, self.annual_attrition)
        # Take upper triangle of attrition rate elements and add ndarray of ones
        # If attrition_y0 == True, allow attrition in year 0, otherwise set k=1 in np.triu() so that attrition starts in second year
        if self.attrition_y0 == True:
            k = 0
        else:
            k = 1
        self.attrition_mask = np.add(self.mask_ones, np.triu(self.attrition_mask, k))
        self.attrition_mask = np.cumprod(self.attrition_mask, axis=1)
        # We only want to go to maximum value of 2 since we want the compounded percentage between 1 and 2
        self.attrition_mask = np.minimum(self.attrition_mask, 2)
        # Now we have ndarray of upper triangle of compounded attrition rates
        self.attrition_mask = np.subtract(self.attrition_mask, 1)
        self.attrition_df = self.employee_count_df.multiply(self.attrition_mask)
        
    def create_retained_employee_count_df(self):
        self.retained_employee_count_df = self.employee_count_df.subtract(self.attrition_df).apply(np.ceil) # Use ceiling to keep whole employees
        
    def apply_midpoint_hiring(self, first_year_full_hire):
        midpoint_mask = np.ones(shape = (self.forecast_period, self.forecast_period))
        np.fill_diagonal(midpoint_mask, .5)
        self.midpoint_mask_df = pd.DataFrame(midpoint_mask)
        
        # Check to see whether the first year hires exist at the beginning of the period
        if first_year_full_hire:
            self.midpoint_mask_df.iloc[0,0] = 1
        self.retained_fte_df = self.retained_employee_count_df.multiply(self.midpoint_mask_df)
        
    def apply_productivity_ramp(self):
        self.retained_fte_factored_df = self.retained_fte_df.multiply(self.productivity_df)
        
    def create_revenue_df(self):
        # Calculate revenue by cohort and year using retained FTE
        self.revenue_df = self.retained_fte_factored_df.multiply(self.revenue_goal)
    
    def print_all_tables(self):
        display(Markdown('## Productivity Table'))
        display(Markdown('The following table contains the percentage of productivity for each cohort by year.'))
        display(Markdown('The maximum percentage for each cell is 100% or 1. Any value less than 1 is used to discount the \
        productivity of that cohort class for that particular year.\n'))
        self.print_table(self.productivity_df, 'Productivity Table')
        
        display(Markdown('## Employee Count before Attrition'))
        display(Markdown('This table for each year, by each cohort, if no attrition were to occur.\n'))
        self.print_table(self.employee_count_df, 'Employee Count (Before Attrition) by Year', precision=0, create_sum=True, sum_title='Employees')
        
        display(Markdown('## Attrition Mask Table'))
        display(Markdown('This table represents the *percentage* of the cohort **population** that has left. It is cummulative; the number \
        starts at zero at increases to 100%, at which point the entire cohort has left the company.\n'))
        self.print_table(pd.DataFrame(self.attrition_mask), 'Attrition Mask - 0% to 100% of Employee Count')
        
        display(Markdown('## Attrition Table'))
        display(Markdown('This table contains the number of employees that have left **up to that year**. \
        This is a cummulative number and will increase from zero to the number of employees that were hired as part of that cohort. \
        Notice that this table contains decimals; the actual calculation ignores the decimals and only accounts for \
        a termination after the number reaches an integer, i.e., people either leave or they do not, fractions of people do not exist.'))
        self.print_table(self.attrition_df, 'Attrition Table - Number of Employees Leaving Before Rounding\n')
        
        display(Markdown('## Retained Employees after Attrition'))
        display(Markdown('This table contains the number of employees that remain with the company after accounting for attrition.\n'))
        self.print_table(self.retained_employee_count_df, 'Employees, After Attrition, by Year', precision=0, create_sum=True, sum_title='Employees')
        
        display(Markdown('## Full Time Equivalent Table'))
        display(Markdown('This table takes the retained employees after attrition from the table above and calculates the \
        number of FTE after applying mid-year hiring. We assume that hiring takes place throughout the year rather than have \
        all employees hired on the first of the year. This results in a lower FTE figure for the first year of the cohort.\n'))
        self.print_table(self.retained_fte_df, 'FTE Table', create_sum=True, sum_title='FTE')
        
        display(Markdown('## Full Time Equivalent after Factoring Productivity Ramp Up'))
        display(Markdown('This table takes the FTE figures from the table above and applies the ramp up in productivity.\n'))
        self.print_table(self.retained_fte_factored_df, 'FTE After Applying Productivity Ramp', create_sum=True, sum_title='FTE')
        
        display(Markdown('## Revenue Table'))
        display(Markdown('This table takes the final FTE figures, after factoring for productivity ramp up periods, and calculates \
        the total revenue per year and per cohort.\n'))
        self.print_table(self.revenue_df, 'Total Revenue by Year', precision=0, create_sum=True, sum_title='Revenue')
            
    def print_table(self, df, table_title, precision=2, create_sum=False, sum_title='Sum'):
        df.index.name='Cohort'
        if create_sum:
            sum_title = 'Sum of '+sum_title
            df.loc[sum_title] = df.sum()
        format_string = '{:,.' + str(precision) + 'f}'
        df_styled = df.style.format(format_string).set_caption(table_title)
        display(df_styled)