import pandas as pd
import numpy as np
import os
from sklearn.feature_selection import VarianceThreshold
from sklearn.ensemble import AdaBoostRegressor
from sklearn.ensemble import BaggingRegressor
from xgboost import XGBRegressor
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import f1_score
from sklearn.metrics import recall_score
from sklearn.metrics import precision_score




#Loading the Data
df_shear_train = pd.read_excel('X_train.xlsx', engine='openpyxl')
df_shear_test = pd.read_excel('X_test.xlsx', engine='openpyxl')

#Seperating X and Ys
Y_bulk_train = df_shear_train["ael_bulk_modulus_vrh"]
Y_shear_train = df_shear_train["ael_shear_modulus_vrh"]
Y_bulk_test = df_shear_test["ael_bulk_modulus_vrh"]
Y_shear_test = df_shear_test["ael_shear_modulus_vrh"]
df_shear_train_X = df_shear_train.drop(["Counter","ael_shear_modulus_reuss","ael_shear_modulus_voigt","ael_shear_modulus_vrh","compound","ael_shear_modulus_reuss","ael_bulk_modulus_reuss","ael_bulk_modulus_voigt","ael_bulk_modulus_vrh","auid","aurl","spacegroup_relax","Pearson_symbol_relax"], axis = "columns")
df_shear_test_X = df_shear_test.drop(["Counter","ael_shear_modulus_reuss","ael_shear_modulus_voigt","ael_shear_modulus_vrh","compound","ael_shear_modulus_reuss","ael_bulk_modulus_reuss","ael_bulk_modulus_voigt","ael_bulk_modulus_vrh","auid","aurl","spacegroup_relax","Pearson_symbol_relax"], axis = "columns")

#Feature Preprocessing

#VT

var_thres = VarianceThreshold(threshold=0.01)
var_thres.fit(df_shear_train_X)
var_thres.get_support()
constant_columns = [column for column in X.columns if column not in X.columns[var_thres.get_support()]]
After_Variance = df_shear_train_X.drop(constant_columns,axis=1)

#PC
import matplotlib.pyplot as plt 
import seaborn as sns
def correlation(dataset, threshold):
    col_corr = set()  # Set of all the names of correlated columns
    corr_matrix = dataset.corr()
    for i in range(len(corr_matrix.columns)):
        for j in range(i):
            if abs(corr_matrix.iloc[i, j]) > threshold: # we are interested in absolute coeff value
                colname = corr_matrix.columns[j]  # getting the name of column
                col_corr.add(colname)
    af_corr = dataset.drop(col_corr,axis=1)
    return af_corr

af_both = correlation(After_Variance, .75)

#Defining the Xs
df_shear_train_X = df_shear_train_X[af_both.columns]
df_shear_test_X = df_shear_test_X[af_both.columns]

#Training
#defining the XGB Algorithm

#Hyperparameters obtained by RandomGridSearch
from sklearn.model_selection import RandomizedSearchCV
param = { "eta" : [0.05,0.1,0.2,0.5,1], "gamma" : [1,2,5,10,100] , "max_depth" : [5,8,11,15] , reg_lambda : [1, 1.05, 1.1, 2], reg_alpha : [0.25 , 0.055, 0.2]}
reg_xgb_orig = XGBRegressor()
best_fit_bulk = RandomizedSearchCV(reg_xgb_orig, param, random_state=0)
best_fit_shear = RandomizedSearchCV(reg_xgb_orig, param, random_state=0)
best_fit_bulk.fit(df_shear_train_X,Y_bulk_train)
best_fit_shear.fit(df_shear_train_X,Y_shear_train)

reg_xgb = XGBRegressor(eta = 0.2, gamma = 5 , max_depth = 11 , reg_lambda = 1.05, reg_alpha = 0.055)
reg_xgb1 = XGBRegressor(eta = 0.1, gamma = 5 , max_depth = 11 , reg_lambda = 1.05, reg_alpha = 0.055)


#Establishing ADABoost

ada_reg = AdaBoostRegressor(base_estimator=reg_xgb, random_state=0)
ada_reg1 = AdaBoostRegressor(base_estimator=reg_xgb1, random_state=0)

#AdaBoost Regression
model_bulk = ada_reg.fit(df_shear_train,Y_bulk_train)
model_shear = ada_reg1.fit(df_shear_train,Y_shear_train)

#Stability Classification
df_energy = pd.read_csv("stability_data.csv")
df_energy = df_energy.dropna()
filename =  df_energy['mat']

#designating the data
Y_energy = df_energy['if']
X_energy = df_energy.drop(['delta_e','filename','mat','if','stability','mili'],axis='columns')
X_energy = X_energy[af_both2.columns]
X_energy.columns = af_both2.columns

#scaling the data
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()
X_scaled_energy = scaler.fit_transform(X_energy)
X_sca_en = pd.DataFrame(X_scaled_energy)
X_sca_en.columns = af_both2.columns
X_sca_en = X_sca_en[af_both2.columns]

#balancing the data
from imblearn.under_sampling import InstanceHardnessThreshold
rus = InstanceHardnessThreshold(cv =5, random_state=7)
X_res, y_res = rus.fit_resample(X_sca_en, Y_energy)


from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X_res,y_res,  test_size=0.2, random_state=485)


#Training & Testing
from sklearn.ensemble import AdaBoostClassifier
ada_reg = AdaBoostClassifier(random_state=0)
ada_reg.fit(X_train,y_train)


