import json
import sys

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python extract_usda_sr_data_name.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    with open(output_file, 'w') as f:
        out_dict = {}
        for d in data['SRLegacyFoods']:
            out_dict[d['fdcId']] = d['description']
        json.dump(out_dict, f, ensure_ascii=False, indent=2)
