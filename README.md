# Cohort Analysis
##  Projecting Revenue Using Productivity Ramp Up Periods

One of the most common modeling tasks is to create future revenue projections based on a hiring plan, where hires are not immediately productive and only reach their full potential after a period of time. Use this module to quickly build cohort tables (revenue, employee count, attrition, FTE, and productivity).

### Quick Instructions
1. Download Cohort.py to local working directory
2. Create new instance by calling CohortTable() class using the arguments listed below.

This analysis provides the following functionality:
* Allows for setting the forecast period to any length
* Provides a ‘productivity ramp-up period’ to account for lower productivity in the early years of new hires
* Accounts for attrition (each cohort will be reduced over time as people leave the company)
* Provides for mid-point hiring (i.e., assume that hires happen throughout the year, not on the first of the fiscal year)
* Allows for full-year hiring for the first period (since the first cohort class may be identified in advance, e.g., be included in the acquisition)

### Arguments 
Create an instance by calling CohortTable() with the following arguments.
* forecast_period (**required**) -- Integer: The length of the forecast period
* n_years (**required**) -- Integer: The length, in years, over which to 'ramp up' productivity from 0 to 100%. 
* hires_per_year (**required**) -- [List of Integers]: How many employees will be hired each year, will be reshaped to fit forecast_period if necessary
* revenue_goal (**required**) -- Integer: The revenue per person when productivity is 100%
* annual_attrition (*optional, default=.15*) -- Decimal, between 0 and 1: Average percentage of attrition, expressed as decimal between 0 and 1
* ramp_type (*optional, default='linear'*) -- String, either 'linear' or 'sigmoid': Whether the shape of the ramp up curve is linear (i.e., a straight line) or sigmoid (i.e., curved where steepness of the slope changes over time)
* beta (*optional, used only when ramp_type != 'linear', default=.3*) -- Decimal, between 0 and 1: Decrease or increase the amount of curve in the line. As beta approaches zero, the line straightens to be linear. As beta approaches 1, the degree of curve increases. This is often referred to as the learning curve.
* shift (*optional, used only when ramp_type != 'linear', default=3*) -- Integer, between -10 and +10: Shifts the s-curve to the left (as shift approaches -10) or to the right (as shift approaches +10). As s-curve is shifted to the left, the largest gains in productivity occur towards the end of the ramp up period. As the s-curve is shifted to the right, the largest gains in productivity occur towards the beginning of the period. When the shift argument is set to zero (0), the curve is balanced.
* first_year_full_hire (*optional, default=False*) -- Boolean (True / False): Whether to use mid-point hiring for first year calculation. 
* attrition_y0 (*optional, default=False*) -- Boolean (True / False): Should attrition occur in the first year of hiring for all cohorts?
