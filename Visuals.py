import numpy as np
import pandas as pd
import DataAccess as da
import DataUtil as du
import sys
import portfolioopt as pfopt
import matplotlib.pyplot as plt
from matplotlib import cm
import cvxopt as opt
from cvxopt import blas, solvers
import itertools
import os
import time
import copy


class scope(object):

	TIMESERIES = {'_6_months': 126, '_1_year': 252, '_all_years': 'nan'}

		
def create_plots(self):
	print('creating images')

	ls_acctdata = da.DataAccess.get_info_from_account(self)

	for acct in ls_acctdata:
		acctname = acct[0] # get account name
		filename = acctname + '-' + da.DataItem.ADJUSTED_CLOSE + '.pkl'
		filename = filename.replace(' ', '')
		filepath = os.path.join(self.datafolder, filename) 
		df_data = da.DataAccess.get_dataframe(filepath, clean=True) # get data frame
		out_filepath = self.imagefolder # get out file path

		for k, v in scope.TIMESERIES.items():
			filename_addition = k
			df = df_data.copy()
			if k != '_all_years': # 'all years' data is passed as is
				df = df.iloc[-v:] # slice the data into the timeframes described in scope.TIMESERIES
				efficient_frontier(df, acctname, out_filepath, filename_addition)
			else:
				efficient_frontier(df, acctname, out_filepath, filename_addition)
			
		for k, v in scope.TIMESERIES.items():
			filename_addition = k
			df = df_data.copy()
			if k != '_all_years': # 'all years' data is passed as is
				df = df.iloc[-v:] # slice the data into the timeframes described in scope.TIMESERIES
				returns(self, df, acctname, out_filepath, filename_addition)
			else:
				returns(self, df, acctname, out_filepath, filename_addition)


def returns(self, df_data, acct, out_filepath, filename_addition):
	
	if len(df_data.columns) > 20: # When there are numerous funds in an account, get unique optimized symbols and
		# chart those.
		ls_syms = da.DataAccess.get_opt_syms(self, acct)
		df_data1 = df_data[ls_syms]
		npa = df_data1.values
	else:
		ls_syms = df_data.columns.tolist()
		npa = df_data.values # converts dataframe to numpy array
	
	ls_index = df_data.index.tolist()
	ls_index.insert(0, 'tot_return')
	return_vec = npa/npa[0,:] # Divides each column by the first value in the column (i.e % returns)
	return_vec = return_vec - 1 # normalizes returns to be 0 based.
	tot_returns = npa[-1,:] / npa[0, :] # divide the last value by the first in each column to get total returns
	return_vec = np.insert(return_vec, 0, tot_returns, 0) # insert the total returns at the top of the daily returns	
	df = pd.DataFrame(return_vec, columns=ls_syms, index=ls_index) # convert back to dataframe to retain the return to symbol relationship.
	
	df = df.transpose() # Transpose the dataframe so all total return values are in one column
	
	df = df.sort_values(by=df.columns[0], ascending=False) # sort symbols by largest to smallest total returns
	
	df = df.drop(df.columns[0], axis=1) # drop the total return values from the dataframe.
	df = df.transpose() # reshape to original
	
	ls_syms = df.columns.tolist()
	ls_index = df.index.tolist()

	np_array = df.values

	out_filepath = os.path.join(out_filepath, acct + '_returns' + filename_addition + '.png')
	
	plot_returns(ls_index, ls_syms, np_array, out_filepath)


def plot_returns(ls_index, ls_syms, return_vec, filepath):
	f = plt.figure(num=None, figsize=(12, 6), dpi=80, facecolor='w', edgecolor='k')
	plt.clf()
	plt.plot(ls_index, return_vec)
	plt.legend(ls_syms, loc='upper left')
	plt.ylabel('Adjusted Close')
	plt.xlabel('Date')
	# plt.show()
	f.savefig(filepath)
	plt.close('all')


def efficient_frontier(df_data, acct, out_filepath, filename_addition):
	'''
	
	'''
	df_all = du.get_risk_ret(df_data) # get np arrays of the exp return and st. dev of each fund

	df_eff = du.get_frontier(df_data) # get twenty efficient portfolios 

	df_eff_port = du.get_frontier_portfolios(df_data) # get four defined efficient porfolios

	y_arr_d = df_all.iloc[:,0:1].values # all funds expected returns
	x_arr_d = df_all.iloc[:,1:2].values # all funds std deviations

	y_arr_e = df_eff.iloc[:,0:1].values # efficient portfolio graph expected return
	x_arr_e = df_eff.iloc[:,1:2].values # efficient portfolio graph std deviation

	titles = df_eff_port.iloc[:,0:1].values # all first column i.e. portfolio names
	y_arr_e_port = df_eff_port.iloc[:,1:2].values # efficient portfolios expected return
	x_arr_e_port = df_eff_port.iloc[:,2:3].values # efficient portfolios std deviation

	fig = plt.figure()
	ax1 = fig.add_subplot(111)
	ax1.scatter(x_arr_d, y_arr_d, c='b')
	ax1.plot(x_arr_e, y_arr_e, c='r')
	ax1.scatter(x_arr_e_port, y_arr_e_port, c='r')

	plt.xlabel('Risk')
	plt.ylabel('Returns')


	for label, x, y in zip(titles, x_arr_e_port, y_arr_e_port):
		plt.annotate(label, xy = (x, y), xytext = (20, -20),
			textcoords = 'offset points', ha = 'right', va = 'top',
			bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
			arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))

	filepath = os.path.join(out_filepath, acct + '_eff_frontier' + filename_addition + '.png')
	# plt.show()
	plt.savefig(filepath)
	plt.close('all')


def index_averages(self):
	'''
	@Summary: Takes a dataframe of index close prices, converts to .change(), converts to .mean(), then averages the mean
	across all stocks into a single series. This is done in a loop across all sectors and the result is a dataframe of price
	changes across all sectors which is then plotted. 
	'''
	
	#starting over here by adding the indexes file in the root dir to pull the index tickers from file.
	index_dir = self.indexdir
	for file in os.listdir(index_dir):
		filename = str(file)
		if 'sp500_sectors' in filename:
			break

	text_file_path = os.path.join(index_dir, filename)
	ls_account_info = da.DataAccess.get_info_from_index(text_file_path)

	data_path = os.path.join(index_dir, 'sp500_sectors_data')
	ls_files = da.DataAccess.get_sp500_sect_files(data_path, syms=False)
	out_filepath = self.index_images

	print('All done to here')
	sys.exit(0)

	for file in ls_files:
		filepath = os.path.join(data_path, file) 
		df_data = da.DataAccess.get_dataframe(filepath, clean=True)
		sector_name = file[:-10]

		for k, v in scope.TIMESERIES.items():
			filename_addition = k
			df = df_data.copy()
			if k != '_all_years': # 'all years' data is passed as is
				df = df.iloc[-v:] # slice the data into the timeframes described in scope.TIMESERIES
				index_returns(df, sector_name, out_filepath, filename_addition)
			else:
				index_returns(df, sector_name, out_filepath, filename_addition)

def index_returns(df_data, sector_name, out_filepath, filename_addition):
	
	print(sector_name)
	df_rets = du.returnize0(df_data)
	print(df_rets.head())
	sys.exit(0)
	# ls_syms = df_data.columns.tolist()
	# ls_index = df_data.index.tolist()
	# ls_index.insert(0, 'tot_return')

	# npa = df_data.values # converts dataframe to numpy array
	# return_vec = npa/npa[0,:] # Divides each column by the first value in the column (i.e % returns)
	# return_vec = return_vec - 1 # normalizes returns to be 0 based.
	# tot_returns = npa[-1,:] / npa[0, :] # divide the last value by the first in each column to get total returns
	# return_vec = np.insert(return_vec, 0, tot_returns, 0) # insert the total returns at the top of the daily returns	
	# df = pd.DataFrame(return_vec, columns=ls_syms, index=ls_index) # convert back to dataframe to retain the return to symbol relationship.
	
	# df = df.sort_values(by=df.columns[0], ascending=False) # sort symbols by largest to smallest total returns
	# df = df.transpose()
	# print(df.head())
	# sys.exit(0)
	
	# df = df.drop(df.columns[0], axis=1) # drop the total return values from the dataframe.
	# df = df.transpose() # reshape to original
	
	# ls_syms = df.columns.tolist()
	# ls_index = df.index.tolist()

	# np_array = df.values

	out_filepath = os.path.join(out_filepath, acct + '_returns' + filename_addition + '.png')
	
	plot_returns(ls_index, ls_syms, np_array, out_filepath)