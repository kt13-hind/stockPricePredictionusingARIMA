# -*- coding: utf-8 -*-
"""spp_streamlit.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Gqcb879NxaUNXmt_NBIHAo62_yyjvt4d
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pandas_datareader as data
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima_model import ARIMA
from pmdarima.arima import auto_arima
from sklearn.metrics import mean_squared_error, mean_absolute_error
import math
import streamlit as sp

sp. title('Stock Trend Prediction')
sp.write('The aimbition of this project is market trend prediction. In this project we use time series analysis.')
sp.markdown(
"""
The concepts used in this project are
- Time Series Analysis
- Stationarity of timeseries
    - Rolling Mean and Standard Deviation
    - Dickey Fuller Test
- Decomposition of timeseries
- Make the time series stationary
- ARIMA 
- Forcast
"""
)
import datetime

start = '2010-01-01'

today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
end = datetime.datetime.strftime(yesterday, '%Y-%m-%d')

sp.markdown('#')
sp.subheader('Enter Stock Ticker')
user_input = sp.text_input('','^NSEI')
sp.markdown(
"""
Stock ticker ends with .NS example
- ^NSEI is ticker for Nifty 50
- ^BSESN is ticker for Sensex
- TCS.NS
- WIPRO.NS
- PIDILITIND.NS
- etc
"""
)
df = data.DataReader(user_input, 'yahoo', start, end)
df = df.reset_index()

sp.markdown('#')
sp.write('First five rows of dataset')
sp.write(df.head())

sp.markdown('#')
#plot close price
plt.style.use('ggplot')
fig = plt.figure(figsize=(10,6))
plt.title('Closing Price over Index')
plt.ylabel('Closing Price')
plt.plot(df['Close'])
sp.pyplot(fig)

#determine whether a series is stationary
def test_stationarity(timeseries):
    sp.info('Results of dickey fuller test')
    adft = adfuller(timeseries, autolag='AIC')
    output = pd.Series(adft[0:4], index=['Test Statistics','p-value','No. of lags used', 'Number of observations used'])
    sp.text(output)
    critical_value = adft[4]['5%']
    if(adft[1] < 0.05) and (adft[0] < critical_value):
        sp.text('The series is stationary')
    else:
        sp.text('The series is not stationary')
        

def rollingStat(timeseries):
    #determining rolling statistics
    rolmean = timeseries.rolling(12).mean()
    rolstd = timeseries.rolling(12).std()
    #plot rolling statistics:
    fig = plt.figure(figsize=(12,6))
    sp.info('Rolling Mean and Standard Deviation')
    plt.plot(timeseries, label='Original')
    plt.plot(rolmean, label='Rolling Mean')
    plt.plot(rolstd, label='Rolling Std')
    plt.legend(loc='best')
    sp.pyplot(fig)


#test statistics exceed the critical values. The data is non linear
#isolate the timeseries with the trend and seasonality
#decompose  the series
def decomposeSeries(timeseries, mode):
    result = seasonal_decompose(timeseries, model=mode, period=200)
    sp.info('Decomposition of Time series')
    fig = plt.figure()
    fig = result.plot()
    fig.set_size_inches(12,9)
    sp.pyplot(fig)
    
#convert the statsmodel into a dataframe
def results_summary_to_dataframe(results):
    '''take the result of an statsmodel results table and transforms it into a dataframe'''
    pvals = results.pvalues
    coeff = results.params
    conf_lower = results.conf_int()[0]
    conf_higher = results.conf_int()[1]

    results_df = pd.DataFrame({"pvals":pvals,
                               "coeff":coeff,
                               "conf_lower":conf_lower,
                               "conf_higher":conf_higher
                                })    
df_Close = df['Close']

sp.markdown('#')
sp.subheader('Analysis of Closing Price')
rollingStat(df_Close)
sp.write('Lets check for stationarity')
test_stationarity(df_Close)
sp.write('Decomposing the series')
decomposeSeries(df_Close, 'multiplicative')

sp.markdown('#')
sp.subheader("Lets make the log of time Series")
df_log = np.log(df_Close)
fig = plt.figure(figsize=(10,6))
plt.title('Log of Closing Price Over Index')
plt.ylabel('Log of Closing Price')
plt.plot(df_log)
sp.pyplot(fig)
sp.write('Lets check for stationarity')
test_stationarity(df_log)

sp.markdown('#')
sp.subheader('Lets take this difference: Log of series - Moving average of log series')
moving_avg = df_log.rolling(12).mean()
log_minus_moving_av = df_log - moving_avg
log_minus_moving_av.dropna(inplace=True)
rollingStat(log_minus_moving_av)
sp.write('Lets check for stationarity')
test_stationarity(log_minus_moving_av)
sp.write('Decomposing the series')
decomposeSeries(log_minus_moving_av, 'additive')


#now lets develop the arima model
#split data into training and testing
sp.markdown('#')
train, test = log_minus_moving_av[:int(len(log_minus_moving_av)*0.9)], log_minus_moving_av[int(len(log_minus_moving_av)*0.9):]
sp.subheader('Training and Testing data')
fig = plt.figure(figsize=(10,6))
plt.title('Training and testing data')
plt.ylabel('Log of series - Moving average of log series')
plt.plot(train, label='Training data')
plt.plot(test, label='Testing data')
plt.legend(loc='best')
sp.pyplot(fig)
           
        
#AUTO find the parameters p, q and d
model_autoARIMA = auto_arima(train, start_p=0, start_q=0,
                            test='adf',      # use adftest to find optimal d
                            max_p=3, max_q=3,
                             m=1,            #frequency of series
                             d=None,         #let model determine 'd'
                             seasonal=False, #No seasonality
                             start_P=0,
                             D=0,
                             trace=True,
                             error_action='ignore',
                             supress_warnings=True,
                             stepwise=True )
sp.markdown('#')
sp.subheader('A glimpse at the model')
#sp.table(results_summary_to_dataframe(model_autoARIMA.summary()))
#model_summary = model_autoARIMA.summary()
#sp.markdown(model_summary)
print(model_autoARIMA.summary())
fig = model_autoARIMA.plot_diagnostics(figsize=(15,8))
sp.pyplot(fig)

#modeling 
#build model
sp.write('The model is being built in real time. Please wait.........')
import statsmodels.api as sm
model = sm.tsa.arima.ARIMA(train, 
                           order=model_autoARIMA.order)
res_arima = model.fit()
sp.write('')
fig = plt.figure(figsize=(10,6))
plt.title('Model fit using training data')
plt.plot(log_minus_moving_av, label='Original log minus moving average')
plt.plot(res_arima.fittedvalues, label='Model fitted values')
plt.legend(loc='best')
sp.pyplot(fig)

#forcast
predicted_arima_diff = pd.Series(res_arima.fittedvalues, copy=True)
print(predicted_arima_diff.head())
#sp.write('Now the model forcasts for the training data')
fc = res_arima.forecast(steps=len(test))
predicted_arima_diff = predicted_arima_diff.append(fc)

#plot
sp.markdown('#')
sp.subheader('Testing, Training and Prediction')
fig= plt.figure(figsize=(10,6))
plt.plot(test, label='Testing')
plt.plot(fc, label='Predicted')
plt.plot(train, label='Training')
plt.title('Prediction')
plt.ylabel('Log of series - Moving average of log series')
plt.legend(loc='best')
plt.show()
sp.pyplot(fig)

predictions_log = predicted_arima_diff + moving_avg
predictions_log.isna().sum()
df_antilog = np.exp(predictions_log)

sp.markdown('#')
sp.subheader('Original vs Predicted')
fig = plt.figure(figsize=(10,6))
plt.title('Original VS Predicted')
plt.plot(df_Close, label='Closing Price')
plt.plot(df_antilog, label='Predicted Price')
plt.ylabel('Price')
plt.legend(loc='best')
sp.pyplot(fig)

sp.markdown('#')
sp.subheader('Original vs Predicted last 200 values')
fig = plt.figure(figsize=(10,6))
plt.plot( df_Close[-200 : ], label='Original Closing Price')
plt.plot(df_antilog[-200 : ], label='Predicted Trend')
plt.legend(loc='best')
sp.pyplot(fig)

sp.markdown('#')
#report performance
sp.subheader('Report Performance')
mse= mean_squared_error(test, fc)
sp.text('Mean Squared Error: '+str(mse))
mae = mean_absolute_error(test, fc)
sp.text('Mean Absolute Error: '+str(mae))
rmse = math.sqrt(mean_squared_error(test, fc))
sp.text('Mean Squared Error: '+str(rmse))
mape = np.mean(np.abs(fc - test)/np.abs(test))
sp.text('Mean Absolute Percentage Error: '+str(mape))
#with mape of around 0.95% the model is 99.05% accurate in predicting next 15 observations

#sp.markdown('#')
#forcast next 15 values
#fc = res_arima.forecast(steps=len(test)+15)
#sp.subheader('Forcast on Log - Moving Average')
#fig = plt.figure(figsize=(10,6))
#plt.plot(test,label='Actual stock price')
#plt.plot(fc, label="Predicted stock price")
#plt.legend(loc='best')
#sp.pyplot(fig)

