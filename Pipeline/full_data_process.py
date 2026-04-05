"""
Function used to process a full dataframe and save a train test split as csv.
"""

import argparse as ap
import pandas as pd
import numpy as np
from pathlib import Path

def full_data_process(file_loc, train_test_path, name, drop_cols=[]):
    
    """
    Function processes the data to make it working for synthpop.
    File_loc: The path to the csv file that gets processed.
    train_test_path: The path to where the train and holdout csv will be saved.
    
    Function returns 2 csvs saved to the specified directory
    """

    # Reading the file
    try:
        df = pd.read_csv(file_loc)
    except:
        df = pd.read_spss(file_loc)

    # Drop columns that were provided in the configuration step
    for col in drop_cols:
        if col in df.columns:
            df = df.drop(columns=col)
        else:
            print(col, 'not in dataframe')
        
    # Replacing the custom missing values
    df = df.replace({'$5':np.nan,'$6':np.nan,'$7':np.nan, '':np.nan, " ":np.nan})
    for col in df.columns:
        if "zip" in col.lower():   # force zip columns to string
            df[col] = df[col].astype(str)
        else:
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                if df[col].nunique() > 10:
                    df = df.drop(columns=col)
                    print(col, 'has been dropped from the dataset')
   
    # Drop empty rows
    df = df[df.index.isin(df.dropna(how='all').index)]
   
    # Printing the amount of binary, categorical and continues columns
    bin_col = [col for col in df.columns if df[col].nunique() <= 2]
    cat_col = [col for col in df.columns if df[col].nunique() >= 3 and df[col].nunique() < 10]
    con_col = [col for col in df.columns if df[col].nunique() >= 10]
    print('\n Amount of binary columns: ', len(bin_col), '\n',
          'Amount of categorical columns: ', len(cat_col), '\n',
          'Amount of continues columns: ', len(con_col))
    
    # Splitting to train and holdout
    df_train = df.sample(frac=0.5, random_state=42)
    df_holdout = df.drop(index=df_train.index)
    
    #df.to_csv(train_test_path + '\\' + name + '_original.csv', index=False)
    # df_train.to_csv(train_test_path + '\\' + name + '_train.csv', index=False)
    # df_holdout.to_csv(train_test_path + '\\' + name + '_holdout.csv', index=False)
    df_train.to_csv(Path(train_test_path) / (name + '_train.csv'), index=False)
    df_holdout.to_csv(Path(train_test_path) / (name + '_holdout.csv'), index=False)
    
    print('Finished processing')
    
    
if __name__ == "__main__":
    
    
    argparser = ap.ArgumentParser(description="Script that gives evaluation scores of the synthetic data")
    argparser.add_argument("-file_loc", action="store", dest="file_loc", required=True, type=str,
                           help="path to the full dataset")
    argparser.add_argument("-train_loc", action="store", dest="train_loc", required=True, type=str,
                           help="path to where the train and holdout file will be saved")
    argparser.add_argument("-name", action="store", dest="name", required=True, type=str,
                           help="name of the dataset")
    
    args = argparser.parse_args()
    
    full_data_process(args.file_loc, args.train_loc, args.name)