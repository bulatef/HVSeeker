from proteinbert import OutputType, OutputSpec, FinetuningModelGenerator, load_pretrained_model, finetune, evaluate_by_len, evaluate_by_len2
from proteinbert.conv_and_global_attention_model import get_model_with_hidden_layers_as_outputs, GlobalAttention
from proteinbert.finetuning import filter_dataset_by_len, split_dataset_by_len, encode_dataset, get_evaluation_results
from proteinbert import load_pretrained_model, InputEncoder
import numpy as np
import random
import argparse
import pandas as pd
from tensorflow import keras

def predict_and_test(model, input_encoder, output_spec, seqs, raw_Y, start_seq_len = 512, start_batch_size = 32, increase_factor = 2):
    

    
    dataset = pd.DataFrame({'seq': seqs, 'raw_y': raw_Y})
        
    results = []
    results_names = []
    y_trues = []
    y_preds = []
    sequences = []

    for len_matching_dataset, seq_len, batch_size in split_dataset_by_len(dataset, start_seq_len = start_seq_len, start_batch_size = start_batch_size, \
            increase_factor = increase_factor):

        X, y_true, sample_weights = encode_dataset(len_matching_dataset['seq'], len_matching_dataset['raw_y'], input_encoder, output_spec, \
                seq_len = seq_len, needs_filtering = False)

        y_pred = model.predict(X, batch_size = batch_size)
        
        y_true = y_true.flatten()

        if output_spec.output_type.is_categorical:
            y_pred = y_pred.reshape((-1, y_pred.shape[-1]))
        else:
            y_pred = y_pred.flatten()

        results.append(get_evaluation_results(y_true, y_pred, output_spec))
        results_names.append(seq_len)
        sequences.append(len_matching_dataset['seq'])
        y_trues.append(y_true)
        y_pred = y_pred.flatten()
        y_preds.append(y_pred)
        
    y_true = np.concatenate(y_trues, axis = 0)
    y_pred = np.concatenate(y_preds, axis = 0)
    sequences = np.concatenate(sequences, axis = 0)
    all_results, confusion_matrix = get_evaluation_results(y_true, y_pred, output_spec, return_confusion_matrix = True)
    results.append(all_results)
    results_names.append('All')
    
    results = pd.DataFrame(results, index = results_names)
    results.index.name = 'Model seq len'
    
    return results, confusion_matrix, y_preds, y_true, np.array(sequences)
    
    

def run_prediction(arguments, output_file, seq_len, test_file):

        max_epochs_per_stage = arguments[0] 
        dropout_rate = arguments[1]
        patience1 = arguments[2] 
        patience2 = arguments[3] 
        factor = arguments[4] 
        min_lr = arguments[5] 
        lr = arguments[6] 
        lr_with_frozen_pretrained_layers = arguments[7]

        _, input_encoder = load_pretrained_model()

        OUTPUT_TYPE = OutputType(False, 'binary')
        UNIQUE_LABELS = [0, 1]
        OUTPUT_SPEC = OutputSpec(OUTPUT_TYPE, UNIQUE_LABELS)
        

        test_set = pd.read_csv(test_file).dropna().drop_duplicates()
        test_set.columns = ["label","seq"]
        
        model = keras.models.load_model(
        "./models/unfrozen_pretrained3.keras", custom_objects={"GlobalAttention": GlobalAttention}
         )
        input_encoder = InputEncoder(8943)

        results, confusion_matrix, ypred, y_true, sequences = predict_and_test(model, input_encoder, OUTPUT_SPEC, test_set['seq'], test_set['label'], \
        start_seq_len = 573, start_batch_size = 32)
        
        
        dict_ = {"sequence": sequences, "y_true": y_true, "y_pred": ypred[0]}
        df= pd.DataFrame(dict_)
        df.to_csv(output_file + "_unfrozen_pretrained.csv")
        
        model = keras.models.load_model(
        "./models/frozen_pretrained3.keras", custom_objects={"GlobalAttention": GlobalAttention}
         )
        
        results, confusion_matrix, ypred, y_true, sequences = predict_and_test(model, input_encoder, OUTPUT_SPEC, test_set['seq'], test_set['label'], \
        start_seq_len = 573, start_batch_size = 32)
        
        dict_ = {"sequence": sequences, "y_true": y_true, "y_pred": ypred[0]}
        df= pd.DataFrame(dict_)
        df.to_csv(output_file + "_frozen_pretrained.csv")
        
        model = keras.models.load_model(
        "./models/last_pretrained3.keras", custom_objects={"GlobalAttention": GlobalAttention}
         )
        
        results, confusion_matrix, ypred, y_true, sequences = predict_and_test(model, input_encoder, OUTPUT_SPEC, test_set['seq'], test_set['label'], \
        start_seq_len = 573, start_batch_size = 32)
        

        dict_ = {"sequence": sequences, "y_true": y_true, "y_pred": ypred[0]}
        df= pd.DataFrame(dict_)
        df.to_csv(output_file + "_last_pretrained.csv")

        
        return
        
        

if __name__ == "__main__":

    cmdline_parser = argparse.ArgumentParser('prediction')



    cmdline_parser.add_argument('-o', '--output_file',
                                default="./test_result_",
                                help='output_file',
                                type=str)
    cmdline_parser.add_argument('-s', '--seq_len',
                                default=512,
                                help='seq_len',
                                type=int)
    cmdline_parser.add_argument('-t', '--test_file',
                                default='./bac_phage_1.csv',
                                help='name of test file',
                                type=str)

    args, unknowns = cmdline_parser.parse_known_args()     



    
    random.seed(31)
    keras.utils.set_random_seed(31)
    np.random.seed(31)
    
    run_prediction([35, 0.6930443135406078, 3, 2, 0.39657786522163363, 3.8602329788847605e-05, 0.00035016815751852485, 0.0011187914605146963], output_file = args.output_file, seq_len=args.seq_len, test_file=args.test_file)
 
    

