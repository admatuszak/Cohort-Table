import pandas as pd
import numpy as np

class CohortTable:
    """
    Customizable cohort table class projects revenue by year and cohort using productivity ramp up periods, mid-year hiring, and attrition. Productivity ramp 
    can be linear or sigmoid (s-curve) and can be of any length. 
    """
    
    def __init__ (self, forecast_period, n_years, hires_per_year, revenue_goal, annual_attrition=.15, \
                  ramp_type='linear', beta=.3, shift=3, first_year_full_hire=False, attrition_y0=False):
        self.forecast_period = forecast_period
        self.n_years = n_years
        self.hires_per_year = hires_per_year
        self.revenue_goal = revenue_goal
        self.annual_attrition = annual_attrition
        self.attrition_y0 = attrition_y0
        self.ramp_type = ramp_type
        self.beta = beta # default for sigmoid function
        self.shift = shift # default for sigmoid function
        
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
        new_list = l
        if len(new_list) >= length:
            del new_list[length:]
        else:
            new_list.extend([pad] * (length - len(new_list)))
        
        return new_list
    
    def sigmoid(self, x, beta, shift):
        # beta should be between .1 and 1 for these purposes
        # shift should be between -10 and and 10 for these purposes
        if (.1 > beta) | (beta > 1):
            beta = self.beta # reset to default
        if (-10 > shift) | (shift > 10):
            shift = self.shift
        return 1 / (1 + np.exp(beta*(-x - shift)))
    
    def create_ramp_sigmoid(self):
        ramp_sigmoid = [self.sigmoid(n, self.beta, self.shift) for n in np.linspace(-10,10, self.n_years)]
        ramp_sigmoid = self.size_list(ramp_sigmoid, self.forecast_period, pad=1)
        
        #move the two lines below to create_productivity_df
        productivity_array = [np.roll(ramp_sigmoid, n) for n in range(self.forecast_period)]
        productivity_array = np.triu(productivity_array)
        
        return productivity_array
        
    def create_ramp_lin(self):
        productivity_array = [[min(max(n, 0)/self.n_years, 1) for n in range(1-i, self.forecast_period+1-i)] for i in range(self.forecast_period)]
        return productivity_array
    
    def create_productivity_df(self):
        if self.ramp_type == 'linear':
            productivity_array = self.create_ramp_lin()
        if self.ramp_type == 'sigmoid':
            productivity_array = self.create_ramp_sigmoid()
        
        self.productivity_df = pd.DataFrame(productivity_array)
        
    def create_employee_df(self):
        # Create upper triangle of employees
        self.employee_count_df = pd.DataFrame(self.mask_ones)
        self.employee_count_df = self.employee_count_df.multiply(self.hires_per_year, axis=0)
        self.employee_count = np.triu(self.employee_count_df) # Switch back to np as opposed to DF to extract upper triangle
        self.employee_count_df = pd.DataFrame(self.employee_count)
    
    def create_attrition_tables(self):
        # Start with ndarray of all ones of shape (forecast_period x forecast_period)
        # Subtract the annual rate of attrition to all elements of ndarray
        self.attrition_mask = np.subtract(self.mask_ones, self.annual_attrition)
        
        # If attrition_y0 == True, allow attrition in year 0, otherwise set k=1 in np.triu() so that attrition starts in second year
        if self.attrition_y0 == True:
            k = 0
        else:
            k = 1
        
        # Set lower tri to 1's so we can cumprod attrition rates. If Y0 attrit == True, go one below diag; otherwise, set diag
        self.attrition_mask[np.tril_indices(self.attrition_mask.shape[0], -1+k)] = 1
        self.attrition_mask = np.cumprod(self.attrition_mask, axis=1)
        
    def create_retained_employee_count_df(self):
        self.retained_employee_count_df = self.employee_count_df.multiply(self.attrition_mask) 
        
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