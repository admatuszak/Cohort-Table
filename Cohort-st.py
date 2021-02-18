import streamlit as st
import sys
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import altair as alt

sys.path.append(r'c:\Users\amatuszak\Documents\GitHub\Cohort-Table')
from Cohort import CohortTable

# Common functions
color = '#800000ff'
def bar_chart(df_melted, y_axis, title):
    chart = alt.Chart(df_melted).mark_bar(color=color, size=40).encode(
        x = alt.X('Year:Q', axis=alt.Axis(tickCount=forecast_period), sort=list(df_melted.index)),
        y = alt.Y(y_axis),
        tooltip = [alt.Tooltip(y_axis, format=',.0f')]
    ).properties(title=title, width=alt.Step(60), height=400).interactive()
    return chart

def line_chart(df_melted, y_axis, title):
    nearest = alt.selection(type='single', nearest=True, on='mouseover', fields=['Year'], empty='none')
    selectors = alt.Chart(df_melted).mark_point().encode(
        x='Year:Q',
        opacity=alt.value(0),
    ).add_selection(nearest)
    
    line = alt.Chart(df_melted).mark_line(color=color).encode(
        x = alt.X('Year:Q', axis=alt.Axis(tickCount=forecast_period), sort=list(df_melted.index)),
        y = alt.Y(y_axis),
        tooltip = [alt.Tooltip(y_axis, format=',.0%')]
    )
    
    points = line.mark_point(color=color, size=40).encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )
    
    chart = alt.layer(line, selectors, points).properties(title=title, width=alt.Step(60), height=400).interactive()
    
    return chart

# Site
st.title('Cohort Tables with Productivity Ramp Up')

st.sidebar.title('Variables')
forecast_period = st.sidebar.slider('Forecast Period', 3, 15, 5)
n_years = st.sidebar.slider('Productivity Ramp Up Period', 1, 10, 3)
ramp_type = st.sidebar.selectbox('Ramp Up Type', ['Linear', 'Sigmoid']).lower()
if ramp_type == 'sigmoid':
    beta = st.sidebar.slider('Beta for S Curve', .1, 1.0, value=.3, step=.1)
    shift = st.sidebar.slider('Shift for S Curve', -10, 10, value=3, step=1)
    
    x = np.linspace(-10,10,50)
    source = pd.DataFrame({
        'Time Passed to Full Productivity' : ((x+10)*5)/100,
        '% of Productivity' : 1 / (1 + np.exp(beta*(-x-shift)))
    })
    s_chart = alt.Chart(source).mark_line().encode(
        alt.X('Time Passed to Full Productivity', axis=alt.Axis(format='.0%')),
        alt.Y('% of Productivity', axis=alt.Axis(format='.0%')),
        tooltip=[alt.Tooltip('Time Passed to Full Productivity', format='.0%'), alt.Tooltip('% of Productivity', format='.0%')]
    )
    st.sidebar.altair_chart(s_chart, use_container_width=True)
else:
    beta=.3
    shift=3

hires_per_year_string = st.sidebar.text_input('Number of hires per year, seperated by commas', value='10, 12, 15, 18, 20')
revenue_goal = st.sidebar.number_input('Revenue Goal per Individual', min_value=0, format='%i')
annual_attrition=st.sidebar.number_input('Annual Attrition Rate', min_value=0.00, max_value=1.00, value=.10, step=.01, format='%f')
first_year_full_hire = st.sidebar.checkbox('First Year Full Hire?', value=True)
attrition_y0 = st.sidebar.checkbox('Attrition in First Year?', value=False)

try:
    hires_per_year = hires_per_year_string.split(",")
    hires_per_year = [float(i) for i in hires_per_year]
except ValueError:
    st.error('The hires per year variable has been entered incorrectly. Please enter a series of numbers seperated by commas')
    st.stop()

# Model
T = CohortTable(forecast_period=forecast_period, n_years=n_years, ramp_type=ramp_type, beta=beta, shift=shift, hires_per_year=hires_per_year, \
                      revenue_goal=revenue_goal, annual_attrition=annual_attrition, \
                      first_year_full_hire=first_year_full_hire, attrition_y0=attrition_y0)
# Sitewide variables
columns_years = [f'Year {i+1}' for i in range(forecast_period)]
columns_Q = [i+1 for i in range(forecast_period)]
rows_cohorts = [f'Cohort {i+1}' for i in range(forecast_period)]

# Main Page
st.write('Click to expand each of the sections below')

with st.beta_expander("Variables and Assumptions"):
    st.write('##### General')
    st.write('Forecast Period = ', '{:.0f} years'.format(forecast_period))
    st.write('Productivity Ramp = ', '{:.0f} years'.format(n_years))
    st.write('Revenue Goal per Employee = ', '${:,.0f}'.format(revenue_goal))
    st.write('Annual Attrition Rate = ', '{:.0%}'.format(annual_attrition))
    if attrition_y0:
        st.write('This model assumes that there **is** attrition in the first year.')
    else:
        st.write('This model **does not** assume attrition in the first year')
    if first_year_full_hire:
        st.write('This model assumes that employees in the first year are hired at the **beginning** of the year.')
    else:
        st.write('This model assumes that employees in the first year are hired **throughout** the year, not at the beginning.')
    st.write('##### Hires per Year')
    st.write(pd.DataFrame([hires_per_year], columns=columns_years, index=['No. Hires']))
    st.write('##### Productivity Ramp Variables')
    st.write(f'Productivity ramps can be either linear or s-curve (sigmoid) shaped. This model assumes {ramp_type}.')
    if ramp_type == 'sigmoid':
        st.write('Beta, or degree of curve = ', '{:.2f}'.format(beta))
        st.write('Shift, or the degree to which the curve is skewed to either the left or right = ', '{:.0f}'.format(shift))

with st.beta_expander('Revenue Table'):
    st.write('This table uses FTE figures (fractions of employees) to calculate total revenue after accounting for the productivity ramp up periods, timing of hiring, and attrition.')
    T.revenue_df.columns = columns_Q
    T.revenue_df.index = rows_cohorts
    T.revenue_df.loc['Sum of Revenue'] = T.revenue_df.sum()
    revenue_styled = T.revenue_df.style.format('{:,.0f}')
    revenue_styled

    revenue_melt = T.revenue_df.loc[['Sum of Revenue']].melt(var_name='Year', value_name='Revenue')
    revenue_chart = bar_chart(revenue_melt, 'Revenue', 'Total Revenue by Year')
    revenue_chart

with st.beta_expander("Productivity Ramp Up Table"):
    st.write('This table the productivity ramp up factor for each year by cohort.')

    T.productivity_df.columns = columns_Q
    T.productivity_df.index = rows_cohorts
    productivity_styled = T.productivity_df.style.format('{:.0%}')
    productivity_styled
    
    productivity_melt = T.productivity_df.iloc[[0]].melt(var_name='Year', value_name='Productivity %')
    productivity_chart = line_chart(productivity_melt, 'Productivity %', 'Productivity Ramp as % of Full Potential')
    productivity_chart

with st.beta_expander('Employee Counts by Year'):
    st.write("""
        This table contains the number of employees by year, after accounting for attrition. Please note that attrition is calculated using FTE (i.e., fractional employees). This table shows whole employees and is based on rounding of the FTE figures. While this is directionally accurate for larger figures, the projections for small figures (i.e., less than 5 employees) can be misleading and care should be taken to factor how a small number of employees in a cohort may behave.For example, if there is only one (1) employee in a cohort, an attrition rate based on the gradual reduction in FTE units will **never** result in an absolute zero. This table arrives at an eventual figure of zero by assuming that an FTE of less than .5 is equivalent to zero.
    """)
    T.retained_employee_count_df.columns = columns_Q
    T.retained_employee_count_df.index = rows_cohorts
    T.retained_employee_count_df.loc['Sum of Employees'] = T.retained_employee_count_df.sum()
    retained_employee_count_df_styled = T.retained_employee_count_df.style.format('{:,.0f}')
    retained_employee_count_df_styled

    retained_employees_melt = T.retained_employee_count_df.loc[['Sum of Employees']].melt(var_name='Year', value_name='Number of Employees')
    employee_chart = bar_chart(retained_employees_melt, 'Number of Employees', 'Number of Employees After Attrition by Year')
    employee_chart

with st.beta_expander('Attrition by Year'):
    st.write("""
        The following table contains the cummulative % of a cohort remaining after attrition.
    """)
    attrition_mask = pd.DataFrame(T.attrition_mask, columns=columns_Q, index=rows_cohorts)
    attrition_mask_styled = attrition_mask.style.format('{:,.0%}')
    attrition_mask_styled
    attrition_y_name = '% of Cohort Remaining'
    attrition_mask_melt = attrition_mask.iloc[[0]].melt(var_name='Year', value_name=attrition_y_name)
    attrition_chart = line_chart(attrition_mask_melt, attrition_y_name, 'Cumulative Percentage of Cohort Retained by Year')
    attrition_chart
