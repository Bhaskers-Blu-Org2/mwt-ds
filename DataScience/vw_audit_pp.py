# ==========================================================================================
# Parse out the vw audit logs to a dataframe.
# ==========================================================================================

import pandas as pd
from subprocess import check_output
import os
import argparse


def run_vw_audit_command(model_file, log_file, pred_file=None, verbose=False, vw_base_cmd="vw -t -l 0.001"):
    """
    Run the VW audit command for a model and input vectors.

    @param: model_file The input model file.
    @param: log_file: The input log file.
    @param: verbose: The verbose flag for advanced printing.
    @param: save_pred: Flag to save model predictions file.
    @param: vw_base_cmd: The base vw command line args.

    @returns: The vw audit command capture from command line.
    """
    if pred_file:
        # Save prediction file
        vw_base_cmd += ' -p {pred_file}'.format(pred_file=pred_file)
    
    vw_audit_cmd = vw_base_cmd+' -i {model} --dsjson {test_input} --audit'.format(model=model_file, test_input=log_file)

    if verbose:
        print("VW Audit command: {0}".format(vw_audit_cmd))
    
    # Run the command in windows and check output.
    vw_cmd_output = check_output(vw_audit_cmd).decode()

    if verbose:
        print(vw_cmd_output)

    return vw_cmd_output

def parse_audit_command(vw_cmd_output, audit_output_file, verbose=False):
    """
    Parse the output of the audit command and output to a dataframe.

    @param: vw_cmd_output: The output of the audit command.
    @param: audit_output_file: The file to which pandas data frame will be written.
    @param: verbose: The verbose flag for advanced printing.

    @returns: The dataframe containing the audit command output.
    """
    coeff_list = []
    line_number = 0
    for line in [s.strip() for s in vw_cmd_output.splitlines()]:
        line_number += 1
        if verbose:
            print("Line {0}: {1}".format(line_number, line))

        # Process lines that have more than one tokens.
        coefficients = line.split("\t")
        if verbose:
            print("Num coefficients: {0}".format(len(coefficients)))

        if len(coefficients) <= 1:
            # This line does not contain coefficients
            continue

        # process coefficients
        for coeff in coefficients:
            coeff_term = coeff.split(":")
            if verbose:
                print("Coefficients: {0}", coeff_term)

            coeff_list.append({"Namespace^Feature": coeff_term[0],
                               "HashValue": coeff_term[1],
                               "FeatureValue": coeff_term[2],
                               "WeightValue": coeff_term[3]})

    # Convert coefficients to pandas and output
    df_coeff = pd.DataFrame(coeff_list)

    # De-duplicate
    df_coeff.set_index(["Namespace^Feature", "HashValue", "FeatureValue"], inplace=True)
    df_coeff = df_coeff[~df_coeff.index.duplicated(keep='first')]

    df_coeff.to_csv(audit_output_file, sep='\t', index=True)
    return df_coeff

def pprint_vw_audit(model_file, log_file, audit_output_file, pred_file=None, verbose=False, vw_base_cmd='vw -t -l 0.001'):
    """
    Run the VW audit command for a model and input vectors.

    @param: model_file The input model file.
    @param: log_file: The input log file.
    @param: audit_output_file: The file to which parsed audit will be written.
    @param: verbose: The verbose flag for advanced printing.
    @param: save_pred: Flag to save model predictions file.
    """
    vw_cmd_output = run_vw_audit_command(model_file, log_file, pred_file, verbose, vw_base_cmd)
    parse_audit_command(vw_cmd_output, audit_output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-m', '--model', type=str, help="VW model used for audit.", required=True)
    parser.add_argument('-i', '--input', type=str, help="input samples on which audit is to be run.", required=True)
    parser.add_argument('-o', '--output', type=str, help="output file that captures audit info in a tabular format in TSV format.", required=True)
    parser.add_argument('-v', '--verbose', help="advanced printing for debugging", action='store_true')
    parser.add_argument('-p', '--pred_file', type=str, help="path for output predictions file")
    parser.add_argument('-b','--base_command', help="base Vowpal Wabbit command (default: vw -t -l 0.001)", default='vw -t -l 0.001')

    args = parser.parse_args()
    print(args)

    # Pretty print the VW audit.
    pprint_vw_audit(args.model, args.input, args.output, args.pred_file, args.verbose, args.base_command)

    # Output message
    print("Please see {file} for VW audit output in TSV format".format(file=args.output))
