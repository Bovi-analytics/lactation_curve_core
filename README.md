# lactation-curves

Repository for lactation curve models and cumulative production computations

[Lactation Curve Models](https://github.com/Bovi-analytics/lactation-curves/tree/main/Lactation%20curve%20models):

Includes linear fitting of multiple lactation curve models: Wood, Wilmink, Ali/Schaeffer, Fischer.  
Also includes Bayesian fitting of the MilkBot model and a script to create your own MilkBot priors

[Cumulative milk yield calculations](<https://github.com/Bovi-analytics/lactation-curves/tree/main/Cummulative%20production%20(ICAR%20Guidelines)>):

Contains code to calculate 305 day milk yield. currently holds The Test Interval Method (TIM) (Sargent, 1968) and
Interpolation using Standard Lactation Curves (ISLC) (Wilmink, 1987)

[Lactation curve characteristics](https://github.com/Bovi-analytics/lactation-curves/blob/main/lactation_curve_characterstics.ipynb):

Notebook with functions to extract lactation curve characteristics of commonly used traditional lactation curve models.
Calculates time to peak, peak yield and cumulative production.

[Lactation curve package](https://github.com/Bovi-analytics/lactation-curves/tree/main/lactationcurve):

Name package: lactationcurve

Authors: Lucia Trapanese & Meike van Leerdam

This package provides implementations of several well-known lactation curve models and tools to fit them to milk yield
data.
It is designed for dairy science applications where milk production data (milk yield vs. days in milk) is modeled to
estimate lactation patterns.

## Main Lactation curve models implemented:

_MilkBot_ – Flexible four-parameter model describing rise, peak, and decline. (Both frequentist and Bayesian fitting
available)

_Wood_ – Classic three-parameter gamma function model.

_Wilmink_ – Linear–exponential hybrid model, with fixed or estimated decay rate.

_Ali & Schaeffer_ – Polynomial–logarithmic model for complex curve shapes.

_Fischer_ – Simplified exponential decay model.

Model fitting methods:

Uses [scipy.optimize.minimize](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html)
or [scipy.optimize.curve_fit](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html) for
parameter estimation.
Bayesian fitting is done through [the MilkBot API](https://api.milkbot.com/#section/MilkBot-Fitting) and requires a key.

Supports model-specific initial guesses and parameter bounds.

Returns predicted yields for each day in a standard lactation (1–305 DIM) or for the full range of input data.

## Core functions:

The model functions of the following lactation curve models: milkbot, wood, wilmink, ali_schaeffer, fischer, brody,
sikka, nelder, dhanoa, emmans, hayashi, rook, dijkstra, prasad

**test_interval_method(df)** - calculates 305 cumulative milk yield based on milk recording samples.
Parameters: df (DataFrame): Input DataFrame with 'DaysInMilk', 'TestId', and 'MilkingYield'. Minimal three samples per
lactation are needed to use this method correctly.
Returns: pandas dataframe with the columns TestId, Total 305-day milk yield.

**fit_lactation_curve(dim, milkrecordings, model='wood', fitting = 'frequentist', breed = 'H', parity = 3, continent = '
USA', key = None)** – Fits the chosen model to data and returns predicted daily milk yields. Both Bayesian and
Frequentist methods are available.

**get_lc_parameters(dim, milkrecordings, model='wood')** – Fits the chosen model and returns its estimated parameters
using frequentists statistics.

**bayesian_fit_milkbot_single_lactation(dim, milkrecordings, key, parity=3, breed = "H", continent="USA")** – Fits the
MilkBot model and returns its estimated parameters using Bayesian statistics

Parameters:
dim: Days in milk (list or array of integers).
milkrecordings: Milk yield records (list or array of floats).
model: Model name ("wood", "wilmink", "ali_schaeffer", "fischer", "milkbot").
key (Str): API key for MilkBot.
parity (Int): Cow parity (default=3).
continent (Str): Region for prior selection (USA, EU or priors made by Chen et al.)
breed (Str): 'H' for Holstein, 'J' for Jersey

Outputs: Predicted daily milk yields (array) or model parameters (tuple), depending on the function.

**lactation_curve_characteristic_function(model = 'wood', characteristic = None)** - Finds the algebraic function to
calculate time of peak, peak yield and cumulative milk yield for 14 lactation curve models. (see table LC review)
Input:
model (Str): type of model you wish to extract characteristics from. Options: milkbot, wood, wilmink, ali_schaeffer,
fischer, brody, sikka, nelder, dhanoa, emmans, hayashi, rook, dijkstra, prasad.
characteristic (Str): characteristic you wish to extract, options are time_to_peak, peak_yield (both based on where the
derivative of the function equals zero) and cumulative_milk_yield (based on the integral over 305 days).

Output: equation for characteristic

**calculate_characteristic(dim, milkrecordings, model, characteristic, fitting = 'frequentist', key = None, parity = 3,
breed = 'H', continent = 'USA')**
Calculate a lactation curve characteristic from a set of milk recordings.

Inputs:
dim (Int): days in milk
milkrecordings (Float): milk recording of the test day in kg
characteristic (String): characteristic you want to calculate, choose between time_to_peak, peak_yield, cumulative_milk_yield.
fitting (String): way of fitting the data, options: 'frequentist' or 'Bayesian'.

Extra input for Bayesian fitting:
key (String): key to use the fitting API,
parity (Int): parity of the cow, all above 3 are considered 3,
breed (String): breed of the cow H = Holstein, J = Jersey,
continent (String): continent of the cow, options USA, EU and defined by Chen et al.

Output: float of desired characteristic
