# CohortTable
##  Projecting per-Person Revenue Using Productivity Ramp Up Periods

One of the most common modeling tasks is to create future revenue projections based on a hiring plan, where hires are not immediately productive and only reach their full potential after a period of time.
Import and call the CohortTable class to automatically generate Full Time Equivalent (FTE), employee count, and revenue tables based on 6 variables.
The class and associated output tables will:
* Allow for setting the forecast period to any length
* Provide a ‘productivity ramp-up period’ to account for lower productivity in the early years of new hires
* Account for attrition (each cohort will be reduced over time as people leave the company)
* Provide for mid-point hiring (i.e., assume that hires happen throughout the year, not on the first of the fiscal year)
* Allow for full-year hiring for the first period (since the first cohort class may be identified in advance, e.g., be included in the acquisition)

Call the CohortTable class using the following arguments.
* forecast_period (required) Int -- The length of the forecast period
* n_years (required) Int -- The length over which to 'ramp up' productivity from 0 to 100%
* hires_per_year (required) List of Integers -- How many employees will be hired each year, will be reshaped to fit forecast_period if necessary
* revenue_goal (required) Int -- The revenue per person when productivity is 100%
* annual_attrition (optional) Decimal -- Average percentage of attrition, expressed as decimal between 0 and 1. Default = .15.
* first_year_full_hire (optional) True / False -- Whether to use mid-point hiring for first year calculation. Default = False
