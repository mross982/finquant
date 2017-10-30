import DataAccess as da
import api
import optimize
import scraper
import visuals
import sys


if len(sys.argv)>1:
	c_dataobj = da.DataAccess(sys.argv[1])
else:
	c_dataobj = da.DataAccess(da.DataSource.YAHOO)


if c_dataobj.source == da.DataSource.YAHOO:
	# api.API.getYahooData(c_dataobj, da.DataAccess.get_info_from_account(c_dataobj)) # Get financial data
	optimize.portfolio_optimizer.main(c_dataobj) # Optimize portfolio 

	# scraper.WebScrapers.wiki_sp500_sectors(c_dataobj) # get SP 500 index info
	# sp500_index_json = da.DataAccess.get_index_json(c_dataobj) # Get SP 500 financial data.
	# api.API.getGoogleData(c_dataobj, da.DataAccess.json_to_ls_acctdata(c_dataobj, sp500_index_json), source='index')
	
