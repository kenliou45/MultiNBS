###############################################
# ---------- Data Import Functions ---------- #
###############################################

import pandas as pd
import numpy as np
import networkx as nx
import time
import os
import random

# Load network from file as unweighted network
# params is generated by the load_params() function
# Can set delimiter, but default delimiter is tab
# Only will read edges as first two columns, all other columns will be ignored
# There are also options to shuffle the network to be loaded if desired (testing randomized network controls)
def load_network_file(network_file_path, delimiter='\t', degree_shuffle=False, label_shuffle=False, verbose=True):
	# Load network using networkx
	network = nx.read_edgelist(network_file_path, delimiter=delimiter, data=False)
	if verbose:
		print('Network File Loaded:', network_file_path)
	if degree_shuffle:
		network = degree_shuffNet(network, verbose=verbose)
	if label_shuffle:
		network = label_shuffNet(network, verbose=verbose)
	return network

# Load binary mutation data with 2 file types (filetype= 'matrix' or 'list')
# params is a dictionary of optional function parameters. 
# params is generated by the load_params() function
# filetype=='matrix' is a csv or tsv style matrix with row and column headers, rows are samples/patients, columns are genes
# filetype=='list' is a 2 columns text file separated by the delimiter where 1st column is sample/patient, 2nd column is one gene mutated in that patient
# Line example in 'list' file: 'Patient ID','Gene Mutated'
def load_binary_mutation_data(filename, filetype='list', delimiter='\t', verbose=True):
	# Load binary mutation data from file
	if filetype=='list':
		f = open(filename)
		binary_mat_lines = f.read().splitlines()
		binary_mat_data = [(line.split('\t')[0], line.split('\t')[1]) for line in binary_mat_lines]
		binary_mat_index = pd.MultiIndex.from_tuples(binary_mat_data, names=['Tumor_Sample_Barcode', 'Gene_Name'])
		binary_mat_2col = pd.DataFrame(1, index=binary_mat_index, columns=[0])[0]
		binary_mat = binary_mat_2col.unstack().fillna(0)
	elif filetype=='matrix':
		binary_mat = pd.read_csv(filename, delimiter=delimiter, index_col=0).astype(int)
	else:
		raise ValueError("'filetype' must be either 'matrix' or 'list'.")
	if verbose:
		print('Binary Mutation Matrix Loaded:', filename)
	return binary_mat

# Loads any non-default optional parameters that may be used in the pyNBS pipeline
# If no file is given, all default values will be set
# If only some parameters are given in parameter file, default values will be used for all other parameters.
# Full parameter documentation is given in the GitHub wiki documentation
def load_params(params_file=None):
	run_pyNBS_params = {
		# Overall pyNBS Parameters
		'verbose' : True,
		'job_name' : 'pyNBS',
		'outdir' : './Results/',
		# Data Loading Parameters
		'mut_filetype' : 'list',
		'mut_filedelim' : '\t',
		'net_filedelim' : '\t',
		'degree_preserved_shuffle' : False,
		'node_label_shuffle' : False,
		# Data Subsampling Parameters
		'pats_subsample_p' : 0.8,
		'gene_subsample_p' : 0.8,
		'min_muts' : 10,
		# Network Propagation Parameters
		'prop_data' : True,
		'prop_alpha' : 0.7,
		'prop_symmetric_norm' : False,
		'save_kernel' : False,
		'save_prop' : False,
		'qnorm_data' : True,
		# KNN Network Construction Parameters
		'reg_net_gamma' : 0.01,
		'k_nearest_neighbors' : 11,
		'save_knn_glap' : True,	
		# Network Regularized NMF Parameters
		'netNMF_k' : 4,
		'netNMF_lambda' : 200,
		'netNMF_maxiter' : 250,
		'netNMF_eps' : 1e-15,
		'netNMF_err_tol' : 1e-4,
		'netNMF_err_delta_tol' : 1e-8,
		'save_H' : False,		
		# Consensus Clustering Parameters
		'niter' : 100,  
		'hclust_linkage_method' : 'average',
		'hclust_linkage_metric' : 'euclidean',
		'save_cc_results' : True,
		'save_cc_map' : True,
		# Cluster Survival Analysis Parameters
		'plot_survival' : False,
		'surv_file_delim' : '\t',
		'surv_lr_test' : True,
		'surv_tmax' : -1,
		'save_KM_plot' : False
	}
	# Load parameters from file and change any given values
	# Performs data type assignment for parameters, throws errors if types cannot be cast
	if params_file is not None:
		params_file = pd.read_csv(params_file, header=-1, comment='#', index_col=0)
		params_file.columns = ['value']
		for param in params_file.index:
			if param in run_pyNBS_params:
				if type(run_pyNBS_params[param])==bool:
					run_pyNBS_params[param] = (params_file.loc[param, 'value']=='True')
				else:
					run_pyNBS_params[param] = params_file.loc[param].astype(type(run_pyNBS_params[param]))['value']
			else:
				run_pyNBS_params[param] = params_file['value'].loc[param]
	else:
		pass
	# Constructs output directory if directory does not exist
	if not os.path.exists(run_pyNBS_params['outdir']):
		os.makedirs(run_pyNBS_params['outdir'])
	return run_pyNBS_params

# Shuffle network by preserving node-degree
def degree_shuffNet(network, verbose=False):
	shuff_time = time.time()
	edge_len=len(list(network.edges))
	shuff_net=network.copy()
	try:
		nx.double_edge_swap(shuff_net, nswap=edge_len, max_tries=edge_len*10)
	except:
		if verbose:
			print('Note: Maximum number of swap attempts ('+repr(edge_len*10)+') exceeded before desired swaps achieved ('+repr(edge_len)+').')
	if verbose:
		# Evaluate Network Similarity
		shared_edges = len(set(list(network.edges)).intersection(set(list(shuff_net.edges))))
		print('Network shuffled:', time.time()-shuff_time, 'seconds. Edge similarity:', shared_edges/float(edge_len))
	return shuff_net

# Shuffle network by permuting network node labels
def label_shuffNet(network, verbose=False):
	shuff_time = time.time()
	edge_len=len(list(network.edges))
	# Permute node labels
	network_nodes = list(network.nodes)
	shuff_nodes = list(network_nodes)
	for i in range(10):
		random.shuffle(shuff_nodes)
	network_relabel_map = {network_nodes[i]:shuff_nodes[i] for i in range(len(network_nodes))}	
	shuff_net = nx.relabel_nodes(network, network_relabel_map, copy=True)
	if verbose:
		# Evaluate Network Similarity
		shared_edges = len(set(list(network.edges)).intersection(set(list(shuff_net.edges))))
		print('Network shuffled:', time.time()-shuff_time, 'seconds. Edge similarity:', shared_edges/float(edge_len))
	return shuff_net		

# Filter extended network txt file where all edges are weighted by a specific quantile
# Return the filtered network edge list and save it to a file if desired (for import by load_network_file)
# The input weighted network file may be any table format of edge list, but the columns for Node A, Node B, and weight must be specified
def filter_weighted_network(network_file_path, save_path, nodeA_col=0, nodeB_col=1, score_col=2, q=0.9, delimiter='\t', verbose=False):
	data = pd.read_csv(network_file_path, sep=delimiter, header=-1, low_memory=False)
	# Filter edges by score quantile
	q_score = data[score_col].quantile(q)
	if verbose:
		print(str(round(q*100,2))+'%', 'score:', q_score)
	data_filt = data[data[score_col]>q_score][data.columns[[nodeA_col, nodeB_col, score_col]]]
	data_filt.columns = ['nodeA', 'nodeB', 'edgeScore']
	if verbose:
		print(data_filt.shape[0], '/', data.shape[0], 'edges retained')
	data_filt.to_csv(save_path, sep='\t', header=False, index=False)
	return 

# Convert and save MAF from Broad Firehose
# Can produce 2 types of filetypes: 'matrix' or 'list', matrix is a full samples-by-genes binary csv, 'list' is a sparse representation of 'matrix'
# This is a conversion tool, so the result must be saved (most tools will require a path to a processed MAF file and load it separately)
# Gene naming can be 'Symbol' or 'Entrez'
def process_TCGA_MAF(maf_file, save_path, filetype='matrix', gene_naming='Symbol', verbose=False):
	loadtime = time.time()
	# Load MAF File
	TCGA_MAF = pd.read_csv(maf_file,sep='\t',low_memory=False)
	# Get all patient somatic mutation (sm) pairs from MAF file
	if gene_naming=='Entrez':
		TCGA_sm = TCGA_MAF.groupby(['Tumor_Sample_Barcode', 'Entrez_Gene_Id']).size()
	else:
		TCGA_sm = TCGA_MAF.groupby(['Tumor_Sample_Barcode', 'Hugo_Symbol']).size()
	# Turn somatic mutation data into binary matrix
	TCGA_sm_mat = TCGA_sm.unstack().fillna(0)
	TCGA_sm_mat = (TCGA_sm_mat>0).astype(int)
	# Trim TCGA barcodes
	TCGA_sm_mat.index = [pat[:12] for pat in TCGA_sm_mat.index]
	# Filter samples with duplicate IDs
	non_dup_IDs = list(TCGA_sm_mat.index.value_counts().index[TCGA_sm_mat.index.value_counts()==1])
	dup_IDs = list(TCGA_sm_mat.index.value_counts().index[TCGA_sm_mat.index.value_counts()>1])
	# Save file as binary matrix or sparse list
	if filetype=='list':
		# Now try to construct two-column/sparse representation of binary sm data
		# Get list of all patient somatic mutations
		index_list = list(TCGA_sm.index)
		# Filter list of patient somatic mutations of duplicate patient barcodes
		index_list_filt = [i for i in index_list if not any([True if barcode in i[0] else False for barcode in dup_IDs])]
		# Save patient somatic mutations list to file
		f = open(save_path, 'w')
		for sm in index_list_filt:
			f.write(sm[0][:12]+'\t'+sm[1]+'\n')
		f.close()
		if verbose:
			print('Binary somatic mutations list saved')
	else:
		# Save non-duplicate patients' binary TCGA somatic mutation matrix to csv
		TCGA_sm_mat_filt = TCGA_sm_mat.loc[non_dup_IDs]  # used to be .ix
		# Remove all genes that have no more mutations after patient filtering
		nonempty_cols = [col for col in TCGA_sm_mat_filt.columns if not all(TCGA_sm_mat_filt[col]==0)]
		TCGA_sm_mat_filt2 = TCGA_sm_mat_filt[nonempty_cols]
		# Remove columns with bad names like '0'
		named_cols = [col for col in TCGA_sm_mat_filt.columns if col!='0']
		TCGA_sm_mat_filt3 = TCGA_sm_mat_filt2[nonempty_cols]
		TCGA_sm_mat_filt3.to_csv(save_path)
		if verbose:
			print('Binary somatic mutation matrix saved')
	if verbose:
		print('MAF file processed:', maf_file, round(time.time()-loadtime, 2), 'seconds.')
	return

# the purpose of this function is supposed to combine somatic mutation data with RNA seq data (gene expression quantification).
# it models the function S(t) = (beta)(P(t)) + (1-beta)(Q(t)) where it mixes somatic and RNA data
#   			where S(t) is the new vector, P(t) is somatic mutation vector, Q(t) is the RNA-seq vector, lambda is 
# 				the tuning parameter set by the user
# sm_mat = a binary matrix loaded from the other data import function (load_binary_mutation_data()) 
# 		   rows are observations (patients) and columns are genes (features)
# rna_mat = a matrix that uses TPM_unstranded data from the gene expression quantification - see R notebook (data.process)
# 			notice that this matrix has not normalized the TPM data - this function does that 
# 			for further details on cleaning and assembling this data. Rows are observations (patients) and columns are genes (features). 
# beta = a tuning parameter - usually it is better to set lambda closer to 1 so Q(t) is not too large 

def calc_combined_matrix(sm_mat, rna_mat, beta=0.8, replace_nan = False, verbose = True, **save_args):
	starttime = time.time()

	beta = float(beta)
	
	# check if beta is within bounds
	if beta < 0.0 or beta > 1.0:
		raise ValueError('Alpha must be a value between 0 and 1, inclusive')
	
	# check if there are any NAs in both matrices
	if sm_mat.isnull().values.any():
		raise ValueError('All sm_mat entries must have non NA values. If you wish to set these cells to 0, set replace_nan = True ')
	if rna_mat.isnull().values.any():
		raise ValueError('All rna_mat entries must have non NA values. If you wish to set these cells to 0, set replace_nan = True ')
	

	# replace NAs with 0 in both matrices (spit out a warning that this was done)
	if replace_nan == True:
		sm_mat = sm_mat.fillna(0)
		rna_mat = rna_mat.fillna(0)
		print("NA values have been replaced by 0.")

	# print that matrix combining is starting
	if verbose:
		print('Performing matrix combining with beta:', beta)

	# filter rna_mat columns to only contain sm_mat genes 
	pat_id = rna_mat.iloc[:, 0]  # Get the first column and assign it to a separate variable
	rna_mat_filtered = rna_mat[rna_mat.columns.intersection(sm_mat.columns)]

	# make sure the sm_mat spit out from load_binary_mutation function is transformed to a similar dataframe like rna_mat
	rna_mat_clean = rna_mat_filtered.set_index(pat_id)

	# make sure row and column indices match sm_mat
	rna_mat_clean = rna_mat_clean.reindex(sm_mat.index)
	rna_mat_clean = rna_mat_clean[sm_mat.columns]

	# normalize by the columns(genes) of rna_mat to match sm_mat range of 0 and 1
	# using min max scaling which achieves our objective

	def min_max_normalize(col):
		col_range = col.max() - col.min()
		if col_range == 0:
			# If the range is zero (constant column), return 0 for all values
			return pd.Series(0, index=col.index)
		else:
			return (col - col.min()) / col_range

	rna_norm = rna_mat_clean.apply(min_max_normalize)

	# apply formula across matrices to combine the 2 matrices using beta parameter 
	combined_mat = beta * sm_mat + (1-beta) * rna_norm

	# save results
	if 'outdir' in save_args:
		if 'job_name' in save_args:
			save_path = save_args['outdir']+str(save_args['job_name'])+'combined_mat.csv'
		else:
			save_path = save_args['outdir']+'combined_mat.csv'
		combined_mat.to_csv(save_path)
	else:
		pass
	if verbose:
		print('Combined Matrix Complete:', time.time()-starttime, 'seconds')

	# return final matrix
	return combined_mat