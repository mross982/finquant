import numpy as np
import pandas as pd
import DataAccess as da
import sys
import portfolioopt as pfopt
import matplotlib.pyplot as plt
import cvxopt as opt
from cvxopt import blas, solvers
import itertools
import os
import time
import copy


class portfolio_visualizer(object):
	'''

	'''
	def df_data(self):

		data_path = self.datafolder
		item = da.DataItem.ADJUSTED_CLOSE
		accounts = [] # a list container for all accounts

		ls_acctdata = da.DataAccess.get_info_from_account(self)
		for acct in ls_acctdata: 
			account_info = [] # a list container for the details per account: dataframe, acct name, filepath
			filename = acct[0] + '-' + da.DataItem.ADJUSTED_CLOSE + '.pkl'
			filename = filename.replace(' ', '')
			filepath = os.path.join(self.datafolder, filename)
			
			ofilepath = self.imagefolder
			acct = acct[0]			

			df_data = da.DataAccess.get_dataframe(filepath, clean=True)
			account_info.extend((df_data, acct, ofilepath))
			accounts.append(account_info) 

		return accounts
		
	def plot_returns(self):

		accounts = portfolio_visualizer.df_data(self)

		for time_period in range(2): # create two time periods for all graphs 1. Year to date, 2. All data
			if time_period == 0:
				for acct in accounts:
					out_filepath = acct[2] # oddly, when assigning filepath last, i get weird results
					df_data = acct[0]
					df_data = df_data[-252:]
					print(df_data.shape)
					acct = acct[1]
					filename_addition = '_YTD'
					portfolio_visualizer.sub_returns(df_data, acct, out_filepath, filename_addition)
				
			else:
				for acct in accounts:
					out_filepath = acct[2] # oddly, when assigning filepath last, i get weird results
					df_data = acct[0]
					acct = acct[1]
					filename_addition = '_Total'
					portfolio_visualizer.sub_returns(df_data, acct, out_filepath, filename_addition)

		sys.exit(0)		

		for acct in accounts:
			out_filepath = acct[2] # oddly, when assigning filepath last, i get weird results
			df_data = acct[0]
			acct = acct[1]

	def sub_returns(df_data, acct, out_filepath, filename_addition):
			ls_syms = df_data.columns.tolist()
			ls_index = df_data.index.tolist()
			ls_index.insert(0, 'tot_return')
			
			npa = df_data.values # converts dataframe to numpy array

			
			return_vec = npa/npa[0,:] # Divides each column by the first value in the column (i.e % returns)

			# Here I add total returns to the DF and sort based on total returns to bring more clarity to the plot.
			# Especially when there are numerous funds and the colors are similiar, the legend will be in order of greatest returns
			# to lowest returns.

			tot_returns = npa[-1,:] / npa[0, :] # divide the last value by the first in each column to get total returns
			return_vec = np.insert(return_vec, 0, tot_returns, 0) # insert the total returns at the top of the daily returns
				
			df = pd.DataFrame(return_vec, columns=ls_syms, index=ls_index) # convert back to dataframe
			# to retain the return to symbol relationship.
			
			df = df.transpose() # Transpose the dataframe so all total return values are in one column
			
			df = df.sort_values(by=df.columns[0], ascending=False) # sort symbols by largest to smallest total returns
			
			df = df.drop(df.columns[0], axis=1) # drop the total return values from the dataframe.
			df = df.transpose() # reshape to original

			# End of sorting
			
			ls_syms = df.columns.tolist()
			ls_index = df.index.tolist()

			np_array = df.values
			
			if len(ls_syms) > 20: # When there are numerous funds in an account, split the funds into four groups based
								  # on total returns and plot each of the four groups seperately.
				ls_symscopy = copy.deepcopy(ls_syms)
				ls_indexcopy = copy.deepcopy(ls_index)
				i = 1
				sym_slice1 = 0
				np_array = np_array.T
				for array in np.array_split(np_array, 4):
					array = array.T
					# print(array.shape)
					filepath = os.path.join(out_filepath, acct + '_returns' + str(i) + filename_addition + '.png')
					sym_slice2 = sym_slice1 + array.shape[1]
					
					ls_syms_temp = ls_symscopy[sym_slice1: sym_slice2] # slice the columns to 1/4 of the total

					portfolio_visualizer.subplot_returns(ls_indexcopy, ls_syms_temp, array, filepath) # plot results
					
					i += 1 # increment counter
					sym_slice1 = sym_slice2 # increment slicer
					filepath = '' # reset filename
			else:
				out_filepath = os.path.join(out_filepath, acct + '_returns' + filename_addition + '.png')
				portfolio_visualizer.subplot_returns(ls_index, ls_syms, np_array, out_filepath)

			# returns = df_data.pct_change()
			# cov_mat = returns.cov()
			# avg_rets = returns.mean()

		

	def subplot_returns(ls_index, ls_syms, return_vec, filepath):
		f = plt.figure(num=None, figsize=(12, 6), dpi=80, facecolor='w', edgecolor='k')
		plt.clf()
		plt.plot(ls_index, return_vec)
		plt.legend(ls_syms)
		plt.ylabel('Adjusted Close')
		plt.xlabel('Date')
		# plt.show()
		f.savefig(filepath)
		plt.close('all')


	def rand_weights(n):
		''' Produces n random weights that sum to 1 '''
		k = np.random.rand(n)
		return k / sum(k)


	def random_portfolio(returns):
		''' 
		Returns the mean and standard deviation of returns for a random portfolio
		'''

		p = np.asmatrix(np.mean(returns, axis=1))
		w = np.asmatrix(portfolio_visualizer.rand_weights(returns.shape[0]))
		C = np.asmatrix(np.cov(returns))
	
		mu = w * p.T  # Expected return
		# p.T is the transpose for the mean returns for each time series
		# w is the weight vector of the portfolio

		sigma = np.sqrt(w * C * w.T)  #standard deviation
		# C is covariance matrix of the returns NOTE: if it used the simple std dev std(array(ret_vec).T*w)
		# the result would be slightly different as it would not take covariances into account.!
		#********* make sure this is the same in the portfolioopt package *****************************
	
		#*************** REMOVED THIS FILTER ********************
		# This recursion reduces outliers to keep plots pretty  
		# if sigma > 2: # a filter that only allows to plot portfolios with a standard deviation of < 2 for better illustration.
		# 	return random_portfolio(returns)
		return mu, sigma

	def main(return_vec, plot=True):
		

		n_portfolios = 1000
		# means, stds = np.column_stack([portfolio_visualizer.random_portfolio(return_vec) for _ in range(n_portfolios)])

		means, stds = np.column_stack([portfolio_visualizer.random_portfolio(return_vec) for _ in range(n_portfolios)])
		# print(type(means))
		# print(means)
		# print(type(stds))
		# print(stds)

		if plot == True:
			plt.plot(stds, means, 'o', markersize=5)
			plt.xlabel('std')
			plt.ylabel('mean')
			plt.title('Mean and standard deviation of returns of randomly generated portfolio weights')
			# plt.show()


	def optimal_portfolio(returns):

		n = len(returns)
		returns = np.asmatrix(returns)
	
		N = 100
		mus = [10**(5.0 * t/N - 1.0) for t in range(N)]
	
		# Convert to cvxopt matrices
		S = opt.matrix(np.cov(returns))
		pbar = opt.matrix(np.mean(returns, axis=1))
		
		# Create constraint matrices
		G = -opt.matrix(np.eye(n))   # negative n x n identity matrix
		h = opt.matrix(0.0, (n ,1))
		A = opt.matrix(1.0, (1, n))
		b = opt.matrix(1.0)
		
		# Calculate efficient frontier weights using quadratic programming
		portfolios = [solvers.qp(mu*S, -pbar, G, h, A, b)['x'] 
			for mu in mus]
		## CALCULATE RISKS AND RETURNS FOR FRONTIER
		returns = [blas.dot(pbar, x) for x in portfolios]
		risks = [np.sqrt(blas.dot(x, S*x)) for x in portfolios]
		## CALCULATE THE 2ND DEGREE POLYNOMIAL OF THE FRONTIER CURVE
		m1 = np.polyfit(returns, risks, 2)
		x1 = np.sqrt(m1[2] / m1[0])
		# CALCULATE THE OPTIMAL PORTFOLIO
		wt = solvers.qp(opt.matrix(x1 * S), -pbar, G, h, A, b)['x']
		weights = np.asarray(wt)
		return weights, returns, risks

	# weights, returns, risks = optimal_portfolio(return_vec)

	# plt.plot(stds, means, 'o')
	# plt.ylabel('mean')
	# plt.xlabel('std')
	# plt.plot(risks, returns, 'y-o')


# if __name__ == '__main__':

# 	if len(sys.argv)>1:
# 		c_dataobj = da.DataAccess(sourcein=sys.argv[1])
# 	else:
# 		c_dataobj = da.DataAccess(sourcein=da.DataSource.YAHOO)

# 	returns = portfolio_visualizer.returns(c_dataobj, plot=True)
	# weights, returns, risks = portfolio_visualizer.optimal_portfolio(returns)
	# print(weights)
	# print(returns)
	# print(risks)
	# portfolio_visualizer.main(returns, plot=True)